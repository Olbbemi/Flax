# Rosemary에서 Flax 사용

PostgreSQL 드라이버, 연결 풀, ring 기반 TLS, SHA-256과 parking_lot을
Flax의 소스로 오프라인에서 사용한다.
소비 프로젝트는 자신의 `Cargo.toml`과 `Cargo.lock`을 관리한다.
Flax의 검증용 테이블과 실행기는 Rosemary 제품 코드에 포함하지 않는다.

## 공급 버전과 기능

[검증 구성](../checks/postgres-smoke/Cargo.toml)의 직접 선언을 기준으로 한다.
ring을 제외한 직접 의존성은 `default-features = false`다.

| 패키지 | 정확한 버전 | 직접 요청 기능 |
| --- | --- | --- |
| tokio | 1.53.1 | io-util, macros, net, rt, sync, time |
| tokio-util | 0.7.18 | rt, codec |
| tokio-postgres | 0.7.18 | runtime |
| deadpool-postgres | 0.14.2 | rt_tokio_1, runtime |
| tokio-postgres-rustls | 0.14.0 | ring |
| rustls | 0.23.45 | std, ring, tls12 |
| ring | 0.17.14 | upstream 기본 기능 유지 |
| rustls-pki-types | 1.15.1 | std |
| sha2 | 0.11.0 | 없음 |
| parking_lot | 0.12.5 | 없음 |

테스트에만 tokio의 `rt-multi-thread`, `test-util`을 추가한다.
[검증용 Cargo.lock](../checks/postgres-smoke/Cargo.lock)은 전이 및 대상별 버전을 고정한다.
[소스 목록](../third_party/rust-registry.json)은 배포 체크섬, 출처와 라이선스를 기록하며,
각 소스의 라이선스 파일과 `.cargo-checksum.json`을 보존한다.
기존 gRPC용 84개에 87개를 추가하여 레지스트리 패키지는 총 171개다.

외부 원본은 모두 `third_party/` 아래에서 관리한다.
소비 범위는 각 프로젝트의 선언, 잠금 파일, 활성 기능과 대상 OS로 결정한다.
이 DB 검증 구성의 직접 선언은 10개이며 Linux에서 선택된 패키지는
검증 프로그램과 빌드용 의존성을 포함해 94개다.
보관한 모든 패키지와 파일을 한 프로그램에서 사용하는 것은 아니다.
원본 저장소의 예제와 테스트, 다른 소비 구성 및 대상별 패키지도 보존한다.

[Linux 활성 기능 목록](../checks/postgres-smoke/features-linux.json)은
고정 잠금 파일과 검증 구성에 대한 Cargo metadata의 기능 합침 결과다.
테스트 전용 기능과 빌드 의존성을 포함하며, 다른 소비 구성의 기능 합침은 다시 확인한다.

- rustls는 `ring`, `std`, `tls12`이며 AWS-LC 경로를 포함하지 않는다.
- ring은 `alloc`, `default`, `dev_urandom_fallback`이다.
- rustls-pki-types의 `std`는 `alloc`을 포함한다.
  전이 선언의 `default`도 `alloc`을 요청하므로 기능 범위는 동일하다.
- postgres-protocol의 선언으로 sha2에 `alloc`, `default`, `oid`가 합쳐진다.
  sha2의 기본 기능은 `alloc`, `oid`이며 십진수 연산 기능과 관계없다.
- parking_lot의 전이 `default`는 빈 목록이다.
  추가 선택 기능은 없으며 lock_api 0.4.14와 parking_lot_core 0.9.12를 사용한다.
- tokio-postgres의 전이 `default`는 이미 요청한 `runtime`을 포함한다.
  with-serde_json, with-chrono, with-time, with-uuid는 활성화하지 않는다.
- aws-lc-rs, aws-lc-sys, rustls-native-certs와 webpki-roots는 포함하지 않는다.

## 소비 프로젝트 연결

Flax를 서브모듈로 가져온 뒤 필요한 직접 의존성을 위 검증 구성처럼 정확한 버전으로 선언한다.
다음 명령은 Rosemary 루트에서 실행하며 `deps/flax`는 배치 예시다.

```sh
python3 deps/flax/scripts/flax.py cargo-db generate-lockfile --offline
python3 deps/flax/scripts/flax.py cargo-db build --locked --offline
python3 deps/flax/scripts/flax.py cargo-db test --locked --offline
```

첫 잠금 파일 생성 이후에는 소비 프로젝트의 잠금 파일을 보존하고 `--locked`를 사용한다.
기존 잠금 파일이 있다면 먼저 공급 버전과의 호환성을 확인한다.
목록에 없는 패키지나 기능의 의존성 해결은 오프라인에서 실패하며 추가 공급 협의가 필요하다.
Flax의 잠금 파일을 Rosemary 제품의 잠금 파일로 복사하지 않는다.

`cargo-db`는 protoc와 Protobuf 빌드를 요구하지 않는다.
Flax의 patch, 디렉토리 소스 대체와 `net.offline = true`를 적용하고,
사용자 전역 Cargo 설정을 변경하지 않는다.
실행 때마다 현재 체크아웃 경로로 `build/cargo-db-config.toml`을 생성하며
캐시, Cargo용 심볼릭 링크와 빌드 결과도 `build/`에 둔다.
`PROTOC`, `PROTOC_INCLUDE`를 강제 설정하지 않는다.
사용자가 이미 설정한 환경 변수는 일반적인 Cargo 실행처럼 상속한다.

출력 경로를 지정할 수 있으며 공백이 있는 경로는 셸에서 인용한다.

```sh
python3 deps/flax/scripts/flax.py --build-dir "/absolute/output path" cargo-db build --locked --offline
```

기존 `cargo` 명령은 protoc를 검사하고 강제 연결하는 gRPC용 동작을 유지한다.
두 모드의 생성 설정 파일은 서로 덮어쓰지 않는다.
같은 빌드 경로에서는 소스 뷰, 캐시와 target을 공유한다.

## TLS와 데이터 사용 조건

각 TLS 구성은 `ClientConfig::builder_with_provider`에
`Arc::new(rustls::crypto::ring::default_provider())`를 전달한다.
프로세스 전역 제공자를 설치하지 않는다.
상위에서 받은 PEM 바이트를 `CertificateDer::pem_slice_iter`로 파싱하고
`RootCertStore`에 넣어 서버 인증서와 대상 이름을 검증한다.
OS 인증서나 내장 루트 목록을 자동으로 보충하지 않는다.

TLS ON은 `SslMode::Require`, OFF는 `SslMode::Disable`과 `NoTls`를 사용한다.
ON의 인증서나 접속 실패 뒤 OFF로 재접속하지 않는다.
OFF도 제한된 계정과 비밀번호로 SCRAM-SHA-256 인증을 수행한다.
[실행 가능한 소비 예제](../checks/postgres-smoke/tests/database.rs)에
명시적 제공자, 메모리 CA 파싱과 별도 ON/OFF 풀 구성이 있다.

bytea는 원본 바이트로 전달한다.
NUMERIC은 TEXT 매개변수를 명시적으로 변환하여 저장하고 TEXT로 읽는다.
소수와 u64 최댓값은 십진 문자열로 왕복하며 부동소수점으로 바꾸지 않는다.
검증에서 사용한 DB 자동 번호와 SQL은 의존성 사용 가능성 확인용이다.
Rosemary의 공개 타입, Track, Store와 제품 SQL은 Rosemary에서 구현한다.

## 실행 환경 준비

실행 기준은 Ubuntu 24.04.4 x86_64와 Rust/Cargo 1.89.0이다.
ring 빌드에는 C 컴파일러가 필요하고 인증서 시험에는 OpenSSL이 필요하다.
이 환경에서는 GCC 13.3.0, OpenSSL 3.0.13과 PostgreSQL/psql 16.15를 확인했다.
macOS Apple Silicon과 다른 대상의 실행은 확인하지 않았다.
대상별 crate 공급은 해당 OS에서의 빌드 성공을 뜻하지 않는다.

Ubuntu에서 PostgreSQL 16이 없을 때 일반 터미널에서 설치한다.

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends postgresql-16 postgresql-client-16
```

C 컴파일러와 OpenSSL도 없다면 설치한다.

```sh
sudo apt-get install --no-install-recommends build-essential openssl
```

Flax에는 PostgreSQL 서버와 Rust 도구 체인의 소스를 반입하지 않는다.
이 세션의 PostgreSQL 설치는 사용자가 직접 수행했다.
검사는 설치 과정에서 만들어진 기본 클러스터를 사용하지 않는다.

## Flax 소비 검사

Flax 루트에서 실행한다.

```sh
python3 -B -m unittest discover -s checks/cargo -v
python3 -B scripts/verify-sources.py
python3 scripts/flax.py cargo-db test --manifest-path checks/postgres-smoke/Cargo.toml --locked --offline --lib
python3 -B checks/postgres-smoke/run.py
python3 scripts/flax.py cargo test --manifest-path checks/grpc-smoke/Cargo.toml --locked --offline
```

단위 검사만 실행할 때는 `--lib`를 사용한다.
전체 DB 검사는 접속 자료를 준비하는 `run.py`로 실행한다.
필수 접속 자료가 없거나 서버를 기동하지 못하면 실패하며 검사를 생략하지 않는다.
로컬 소켓 및 루프백 TCP 생성이 허용된 일반 사용자 환경에서 실행한다.
root로 실행하지 않는다.
PostgreSQL의 설치 경로나 출력 위치가 다르면 지정한다.

```sh
python3 -B checks/postgres-smoke/run.py --pg-bin /usr/lib/postgresql/16/bin --build-dir build/postgres-smoke
```

실행기는 `/tmp/flax-pg-*`의 새로운 전용 디렉토리에 정상 TLS, 만료 인증서 TLS,
TLS 미지원 서버를 준비하고 루프백의 빈 포트를 사용한다.
TCP 인증 규칙과 계정의 비밀번호 저장 형식이 SCRAM인지 확인한다.
전용 DB에 검사 스키마를 만들고 해당 스키마를 소유하는 제한된 계정을 만든다.
비밀번호는 매 실행 새로 생성하여 자식 프로세스에만 전달한다.
CA와 서버 개인 키도 새로 만들고 작업 디렉토리에만 둔다.

| 검사 | 확인 내용 |
| --- | --- |
| 단위 검사 3개 | 메모리 PEM 파싱과 잘못된 PEM 거부, SHA-256 알려진 값, RwLock 공유 읽기와 배타 쓰기 및 재취득 |
| 접속과 인증 | ON/OFF 질의 성공, 잘못된 비밀번호의 인증 오류 |
| TLS | 1.2/1.3 실제 협상, 잘못된 CA/이름/만료 인증서 거부, TLS 미지원 서버에서 ON 거부 |
| 풀 | 동시에 존재하는 ON/OFF의 암호화 상태, 서로 다른 backend, 최대 2개 연결과 대기 시간 제한 |
| 트랜잭션 | 별도 연결에서 commit/rollback 결과, SQL 오류 정리 후 후속 질의 |
| 데이터 | bytea 정확한 값, 소수와 u64 최댓값의 NUMERIC/TEXT, 문자열과 정수 및 DB 자동 번호 |
| gRPC 회귀 | 기존 생성 클라이언트와 서버의 메시지 및 상태 교환 |

로그는 `build/postgres-smoke/logs/<실행 식별자>/`에 남긴다.
`environment.json`, `tests.log`, `features.json`, `result.json`, 명령 및 서버 로그를 보관한다.
로그에는 비밀번호와 개인 키 내용을 남기지 않는다.
종료할 때 시작한 서버만 중지하고 전용 DB, 비밀번호와 개인 키를 함께 삭제한다.
정리에 실패하면 실패 결과와 남은 디렉토리를 출력하므로 해당 서버의 종료 상태를 확인한다.
공급 소스와 빌드 캐시는 유지한다.

공급 결과와 단계별 판단은
[작업 기록](../specs/dependencies/rosemary-storage/implementation-report-001.md)에서 확인한다.
구현 중 사전 실행은 별도의 검증 및 사용자 QA를 대체하지 않는다.
기본 RwLock 검사로 Rosemary의 기아, 종료 시간이나 lost wakeup을 판정하지 않는다.
