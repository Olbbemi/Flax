# JSON과 날짜 의존성 사용

serde_json과 chrono를 Flax의 원본 소스로 오프라인에서 사용한다.
소비 프로젝트는 자신의 Cargo.toml과 Cargo.lock을 관리한다.

## 공급 버전과 기능

| 패키지 | 고정 버전 | 직접 선언 기능 | Linux 실제 활성 기능 |
| --- | --- | --- | --- |
| serde_json | 1.0.151 | default-features=false, std | std |
| chrono | 0.4.45 | default-features=false, std | alloc, std |

```toml
serde_json = { version = "=1.0.151", default-features = false, features = ["std"] }
chrono = { version = "=0.4.45", default-features = false, features = ["std"] }
```

chrono의 clock, now, 로컬 시간대 탐색과 wasm 관련 기능을 활성화하지 않는다.
serde_json의 순서 보존과 임의 정밀도 기능도 활성화하지 않는다.
다른 소비 구성의 기능 합침은 그 구성에서 다시 확인한다.

[독립 소비 구성](../checks/json-date-smoke/Cargo.toml)은 typed JSON 해석과 직렬화의 호환성을
확인하기 위해 기존 serde 1.0.229의 std/derive를 함께 선언한다.
Value만 사용하는 소비자에게 derive 선언을 강제하지 않는다.

새로 공급한 전이 소스는 zmij 1.0.23, num-traits 0.2.19와 빌드 의존성 autocfg 1.5.1이다.
serde/serde_core와 itoa, memchr 및 derive용 소스는 기존 공급 버전을 재사용한다.
[검증용 잠금 파일](../checks/json-date-smoke/Cargo.lock)과
[Linux 활성 기능](../checks/json-date-smoke/features-linux.json)에 실제 버전과 기능을 기록한다.
검증 프로그램을 제외한 의존성 그래프는 14개 패키지다.

원본 배포 소스와 라이선스는 third_party의 분류 경로에 보관한다.
[소스 목록](../third_party/rust-registry.json)은 출처, 버전, 원본 커밋, 라이선스와 배포 체크섬을 기록한다.
파일별 체크섬은 각 패키지의 .cargo-checksum.json에 있다.
전체 레지스트리는 기존 171개와 새 5개를 합쳐 176개이며, 이 소비 구성에 모두 연결되지는 않는다.

## 소비 프로젝트 연결

Flax를 연결한 소비 프로젝트 루트에서 실행한다.
아래 `deps/flax`는 Flax의 배치 예시다.

```sh
python3 deps/flax/scripts/flax.py cargo-db generate-lockfile --offline
python3 deps/flax/scripts/flax.py cargo-db build --locked --offline
python3 deps/flax/scripts/flax.py cargo-db test --locked --offline
```

기존 잠금 파일이 있으면 먼저 고정 공급 버전과의 호환성을 확인한다.
Flax의 검증용 잠금 파일을 제품의 잠금 파일로 복사하지 않는다.
공급하지 않은 패키지나 선택 기능의 의존성 해결은 오프라인에서 실패한다.

cargo-db는 protoc가 없는 일반 Rust 소비에도 사용할 수 있다.
기존 Flax 패치와 로컬 디렉토리 소스를 연결하고 net.offline=true를 적용한다.
사용자 전역 설정을 변경하지 않으며, 생성 설정과 소스 뷰, 캐시 및 빌드 결과는 build 아래에 둔다.

## 기본 소비 검사

Flax 루트에서 실행한다.
Rust/Cargo 1.89.0, Ubuntu 24.04.4 x86_64를 기준으로 한다.
새 소비 검사는 외부 서버나 네트워크를 사용하지 않는다.

```sh
python3 scripts/flax.py --build-dir build/json-date-smoke cargo-db test --manifest-path checks/json-date-smoke/Cargo.toml --locked --offline
python3 scripts/flax.py --build-dir build/json-date-smoke cargo-db metadata --manifest-path checks/json-date-smoke/Cargo.toml --locked --offline --format-version 1
python3 -B scripts/verify-sources.py
```

빈 캐시에서 확인하려면 아직 없는 새 출력 경로를 --build-dir에 지정한다.
해당 경로 아래의 CARGO_HOME과 target을 사용하며 protoc 설치를 요구하지 않는다.
기존 gRPC/Protobuf 패치가 새 소비 그래프에서 사용되지 않는다는 Cargo 안내는 발생할 수 있다.
이 구성은 해당 패키지를 선언하지 않는다.

| 테스트 | 확인 내용 |
| --- | --- |
| 일봉 JSON 바이트 | 현재 응답과 같은 필드명에서 날짜와 가격/거래량/거래대금의 정수 문자열 해석 |
| 큰 정수 | 9007199254740993 및 u64 최댓값을 문자열에서 정확하게 해석하고 JSON 숫자로 직렬화/재해석 |
| 정수 경계 | 범위 초과, 음수, 소수와 빈 정수 문자열을 u64 파서에서 거부 |
| manifest와 JSONL | samples[].retrieved_at 해석, JSON 결과 및 두 JSONL 레코드 왕복 |
| 명시적 시간대 | +09:00과 Z로 표현한 요청 시각을 같은 1790899775581009 UTC microseconds로 변환 |
| 달력 날짜 | YYYYMMDD와 YYYY-MM-DD의 대응, 윤일 해석과 잘못된 날짜 거부 |
| 잘못된 입력 | 잘못된 JSON과 RFC3339 시각을 라이브러리 오류로 거부 |

[검증 입력](../checks/json-date-smoke/fixtures/)은 Walnut의 2026-10-02 로컬 샘플에서
daily-raw-01.json 첫 행의 필요한 공개 필드와 manifest 한 항목을 추출한 최소 입력이다.
원본 전체 응답이나 manifest를 복제한 자료가 아니며, 테스트 실행은 Walnut 파일에 의존하지 않는다.
이 검증 코드는 제품 파서를 구현하지 않는다.

## 기존 소비 경로 확인

새 패키지 추가 뒤 기존 Cargo 모드와 PostgreSQL/gRPC 소비를 함께 확인한다.

```sh
python3 -B -m unittest discover -s checks/cargo -v
python3 -B checks/postgres-smoke/run.py --build-dir build/json-date-regression/postgres
python3 scripts/flax.py cargo test --manifest-path checks/grpc-smoke/Cargo.toml --locked --offline
```

DB 검사는 PostgreSQL 16과 C 컴파일러, OpenSSL을 준비한 일반 사용자 환경에서 실행한다.
DB/gRPC 검사는 localhost 소켓 생성 권한이 필요하며 샌드박스에서 제한되면 해당 실행 권한을 확보한다.
DB 실행기는 자체 임시 서버와 검사 자료를 준비하고 종료 시 정리한다.
기존 구성은 [Rosemary 안내](rosemary-integration.md)와 [Cress 안내](cress-integration.md)를 따른다.

구현과 사전 실행 근거는 [작업 기록](../specs/dependencies/json-date-dependencies/implementation-report.md)에 연결한다.
사전 실행 성공과 검증/사용자 QA의 완료는 구분한다.
[최종 검증](../specs/dependencies/json-date-dependencies/verification-report.md)과
[QA 결과](../specs/dependencies/json-date-dependencies/qa-report.md)에 실제 판정과 확인 범위를 기록한다.
Walnut 전체 482행의 파싱/저장/조회 및 DB QA, Rosemary/Walnut의 리비전 갱신은 해당 프로젝트에서 수행한다.
