---
status: completed
base_on: null
---

# Rosemary 저장 의존성 공급 논의

이 문서의 범위와 요구사항 및 제약은 두 Rosemary 공급 요청에서 확정한 계약의 정본이다.
환경 관찰과 미확인 전제는 2026-10-05 논의 시작 시점의 기록이다.
후속 설계와 검증 결과 및 현재 반환 상태는 [최종 QA](qa-report-001.md)를 따른다.

## 단계 결과

### 작업 모델과 승인

- 담당 범위: 두 공급 요청의 논의, 설계, 구현, 검증과 사용자 참여 QA.
- 제안 조합: GPT-6.1 Sol / high.
- 선정 이유: 요청된 버전과 검증 조건이 구체적이며, 의존성 해결, TLS 실패 조건과 기존 소비 경로의 회귀를 함께 판단해야 한다.
- 선택 근거: 2026-10-05에 조회한 [Aster 공용 모델 선택 기준](https://github.com/Olbbemi/Aster/blob/main/shared/model-selection.md).
- 승인 및 적용 확인: 제안 후 사용자가 모델 변경을 알렸다.
  제안한 조합으로 변경했다는 사용자 확인을 근거로 진행하며, 실제 모델과 강도를 독립적으로 확인한 것은 아니다.

논의 단계에서는 별도 검토 모델을 승인받지 않았다.
후속 코드 교차 검토의 승인과 실제 실행은 [검증 기록](verification-report-001.md#작업-모델과-승인)에 있다.

### 복귀 및 재검토 기록

최초 논의이며 해당 없음.

- 회귀 계기가 된 report: 해당 없음.

### 문제와 기대 결과

#### 사용 주체와 상황

Rosemary는 PostgreSQL 저장 라이브러리와 Track 관리 잠금에서 Flax의 Rust 소스를 소비한다.
두 원래 요청은 아래 로컬 파일에 보관되어 있으며 Git에서 제외된다.
다른 체크아웃에서 요청 파일이 없어도 이 문서의 확정 요구사항을 기준으로 작업을 확인할 수 있다.

- PostgreSQL 드라이버, 연결 풀 및 TLS: `data/todo/20261003-rosemary-postgresql-dependencies.md`.
- Track 관리 잠금: `data/todo/20261005-rosemary-parking-lot-dependency.md`.

두 요청은 같은 공급 및 소비 경로를 사용하므로 한 작업으로 처리했다.

#### 해결할 문제와 개발 목적

논의 시작 당시 Flax는 기본 Rust gRPC 소비 소스와 경로만 제공했다.
Rosemary의 DB 및 잠금 패키지는 미공급 상태였고,
기존 Cargo 실행 경로는 DB 전용 소비에도 protoc를 요구했다.
요청 패키지와 필요한 전이 의존성을 공급하고 DB 전용 소비 및 실제 서버 검증 경로를 마련한다.

#### 기대 결과

Rosemary가 자신의 Cargo.toml과 Cargo.lock으로 Flax 소스를 연결하여
Rust/Cargo 1.89.0에서 고정 잠금 파일을 사용하는 오프라인 빌드를 수행할 수 있다.
Flax는 사용 가능한 소스, 활성 기능, 실제 검증 결과와 재현 절차를 반환한다.

### 범위와 요구사항

#### 포함 범위

- 두 요청서에 지정된 직접 패키지, 기능과 필요한 전이 및 빌드 의존성의 공급.
- 기존 소스 관리 규약에 따른 버전, 출처, 체크섬과 라이선스 보존.
- protoc 없는 DB 전용 Cargo 소비 경로 및 기존 gRPC 명령 호환성.
- DB와 잠금 최소 소비 검증 구성, 검증용 Cargo.lock과 실제 활성 기능 기록.
- PostgreSQL 16을 사용하는 SCRAM 인증, TLS, 풀, 트랜잭션과 데이터 왕복 검증.
- 현 환경에서 필요한 PostgreSQL 설치 시도와, 직접 설치할 수 없는 경우 설치 가이드 제공.
- 실제 결과와 미실행 범위를 기존 Flax 요청 기록에 반영하고 Rosemary에 전달할 자료 정리.

#### 제외 범위

- 이번 작업에서 제외, 향후 고려: macOS Apple Silicon 실행 및 크로스 컴파일 검증.
  이번 실제 실행 완료 기준은 Ubuntu x86_64이다.
- 이번 작업에서 제외: 모든 upstream 예제와 개발 의존성의 공급.
  Rosemary 소비 구성과 Flax 검증 구성에 필요한 범위만 완결한다.
- 대상 범위 밖: PostgreSQL 서버 소스 반입, Rosemary의 Store, freight, 제품 테이블과 Track 구현.
  서버 OS 패키지는 검증 환경 준비로 다룬다.
- 대상 범위 밖: Rosemary의 멱등성, processing 판별, 조기 비교 종료,
  제품 성능, 종료 기아와 lost wakeup 검증.
- 대상 범위 밖: 사용자 전역 Cargo 설정 변경과 Rosemary로의 별도 소스 복사.

#### 기능 요구사항

두 요청서에서 확정한 직접 패키지의 고정 버전과 기능은 다음과 같다.
공급 과정에서 임의로 변경하지 않는다.

| 패키지 | 버전 | 소비 요청 기능 |
| --- | --- | --- |
| tokio | 1.53.1 | default-features=false; io-util, macros, net, rt, sync, time |
| tokio-util | 0.7.18 | default-features=false; rt, codec |
| tokio-postgres | 0.7.18 | default-features=false; runtime |
| deadpool-postgres | 0.14.2 | default-features=false; rt_tokio_1, runtime |
| tokio-postgres-rustls | 0.14.0 | default-features=false; ring |
| rustls | 0.23.45 | default-features=false; std, ring, tls12 |
| ring | 0.17.14 | upstream의 ring 경로에 필요한 전이 기능 보존 |
| rustls-pki-types | 1.15.1 | default-features=false; std 및 이에 포함되는 alloc |
| sha2 | 0.11.0 | default-features=false; 직접 추가 기능 없음 |
| parking_lot | 0.12.5 | default-features=false; 추가 기능 없음 |

검증 프로그램에 필요한 Tokio의 rt-multi-thread와 test-util도 공급 범위에 포함한다.
전이 패키지의 실제 버전과 대상별 의존성은 잠금 파일로 고정하고,
기능 합침은 요청 기능과 실제 활성 기능을 구분하여 반환한다.

TLS 구성은 Store별 명시적 ring 제공자와 상위가 전달한 메모리 PEM CA를 사용한다.
TLS ON 실패 시 평문으로 재접속하지 않고, TLS OFF에서도 SCRAM 인증을 유지한다.
aws-lc-rs, aws-lc-sys, rustls-native-certs와 webpki-roots를 이 소비 구성에서 활성화하지 않는다.
TLS 1.2 및 1.3, 서버 인증서와 대상 이름 검증, ON/OFF 풀의 동시 사용을 확인한다.

데이터 왕복은 bytea, TEXT 경유 NUMERIC, 소수와 u64 범위 값, 문자열과 정수로 확인한다.
소수와 u64 값은 십진 문자열로 전달하고 부동소수점으로 변환하지 않는다.
검증 테이블의 ID는 DB 자동 번호를 사용한다.
별도 설정 파서, 원본 압축, UUID 생성과 십진수 연산 패키지는 추가하지 않는다.
드라이버의 with-serde_json, with-chrono, with-time와 with-uuid 기능은 활성화하지 않는다.

필수 소비 검증은 다음 조건을 확인한다.

- SCRAM 인증으로 TLS ON/OFF 접속이 성공하고 잘못된 비밀번호는 28P01로 거부된다.
- TLS 1.2/1.3이 정상 협상되고 잘못된 CA, 대상 이름, 만료 인증서와 TLS 미지원 서버를 거부한다.
- ON/OFF 풀을 동시에 사용할 수 있고 지정 연결 수 및 풀 대기 제한이 동작한다.
- commit한 값은 별도 연결에서 보이고 rollback한 값은 보이지 않는다.
  SQL 오류 뒤 rollback 또는 연결 정리 후 후속 질의가 성공한다.
- bytea, 소수 및 u64 범위의 NUMERIC/TEXT, 기본 문자열과 정수가 정확히 왕복한다.
- 메모리 PEM 파싱과 알려진 입력의 SHA-256, RwLock의 공유 읽기, 배타 쓰기와 guard 해제 후 재취득이 성공한다.
- 기존 gRPC 소비 명령과 검사가 유지된다.

#### 품질 요구사항

- Ubuntu 24.04.4 x86_64, Rust/Cargo 1.89.0에서 검증한다.
- 완성된 소비 구성은 Flax 소스와 잠금 파일로 --locked --offline 빌드가 성공해야 한다.
  공급 준비 중 다운로드와 소비 시 오프라인 빌드를 구분한다.
- 기존 gRPC 소비 구성과 명령의 회귀를 검증한다.
- 원본을 임의 교체하지 않고, 버전이 갈리는 전이 패키지는 필요한 여러 버전을 보존한다.
- 실제 실행하지 못한 검사는 미실행으로 기록하고 완료나 통과로 표시하지 않는다.
- 검증 DB와 제한된 계정을 사용하며 비밀번호와 비공개 키를 소스, 로그와 인계 기록에 남기지 않는다.

#### 반환 자료와 공급 완료 조건

공급 작업의 반환 조건은 소비할 Flax 리비전, 출처와 라이선스 및 체크섬,
검증 선언과 잠금 파일, 실제 기능, 재현 명령과 환경 및 성공/실패와 정리 결과를 Rosemary에 전달하는 것이다.
QA 단계 종료와 해당 리비전 및 실제 프로젝트 간 인계 완료는 구분한다.

### 제약과 확인 근거

아래 관찰과 미확인 항목은 논의 시작 당시의 상태다.
이후 PostgreSQL 설치, 소스 반입과 실제 검증은 설계, 구현 및 검증 기록에서 확인한다.

#### 논의 시작 시점의 상태와 확인 근거

- 프로젝트 루트: git rev-parse 결과 `/home/olbbemi/Project/Flax`.
- 공용 경로: `~/.local/share/flax`가 이 저장소의 data 디렉토리를 가리킨다.
- 환경: /etc/os-release는 Ubuntu 24.04.4 LTS, uname -m은 x86_64이다.
  rustc와 cargo는 각각 1.89.0이다.
- psql, postgres와 pg_ctl 명령 및 /usr/lib/postgresql 경로는 확인되지 않았다.
  sudo, apt-get, C 컴파일러와 OpenSSL 명령은 존재한다.
- [기존 Tokio 소스](../../../third_party/core/tokio/tokio/Cargo.toml)는 1.53.1,
  [tokio-util 소스](../../../third_party/core/tokio/tokio-util/Cargo.toml)는 0.7.18이다.
  두 패키지의 rust-version은 1.71이다.
- 논의 당시 Cargo 실행 스크립트의 cargo_config는 protoc 파일을 필수 검사했다.
  build/install/bin/protoc가 존재했으므로 DB 전용 검증은 별도 protoc 없는 경로로 준비해야 했다.
  최종 인터페이스는 [설계](design-report-001.md#공개-인터페이스)를 따른다.
- `python3 -B scripts/verify-sources.py` 실행 결과,
  원본 저장소 5개의 Git 트리 및 파일 수와 레지스트리 패키지 84개의 파일 목록 및 SHA-256 검사가 통과했다.
- 공식 Cargo 인덱스에서 신규 직접 요청 패키지 8개의 지정 버전과 yanked=false를 확인했다.
  rust-version이 명시된 패키지의 요구는 모두 1.89.0 이하이다.
  tokio-postgres-rustls는 해당 필드를 선언하지 않아 실제 빌드가 필요하다.
- Cargo 인덱스에서 요청 기능 선언을 확인했다.
  rustls-pki-types의 std는 alloc을 포함하고 parking_lot의 기본 기능 목록은 비어 있다.
- 지정 버전과 요청 기능의 확인 근거는 직접 조회한 공식 Cargo 인덱스 항목이다.
  [tokio-postgres](https://index.crates.io/to/ki/tokio-postgres),
  [deadpool-postgres](https://index.crates.io/de/ad/deadpool-postgres),
  [tokio-postgres-rustls](https://index.crates.io/to/ki/tokio-postgres-rustls),
  [rustls](https://index.crates.io/ru/st/rustls),
  [rustls-pki-types](https://index.crates.io/ru/st/rustls-pki-types),
  [sha2](https://index.crates.io/sh/a2/sha2),
  [ring](https://index.crates.io/ri/ng/ring),
  [parking_lot](https://index.crates.io/pa/rk/parking_lot).
- 논의 시작 시 README 수정 및 훅, 할 일 경로 준비 파일 등의 미커밋 변경이 존재했다.
  기존 변경으로 구분했고 공급 작업에서 삭제하지 않았다.

#### 지켜야 할 제약

고정 버전 또는 Rust/Cargo 1.89.0에서 요청 구성이 성립하지 않으면 실패 근거와 변경안을 제시한다.
사용자 합의 전에 버전, 도구 체인 또는 공급 범위를 임의 변경하지 않는다.

PostgreSQL 설치가 필요한 시점에 실제 설치 권한과 패키지 준비 여부를 확인한다.
권한 승인이 필요한 설치 명령은 그 시점에 요청한다.
직접 설치할 수 없으면 사용자가 실행할 가이드를 제공하고 실제 서버 검증은 준비 후 수행한다.

#### 미확인 전제

논의 당시 미확인이며 후속 단계에서 해결 및 검증한 항목이다.
현재의 미처리 항목으로 해석하지 않는다.

- 신규 직접 패키지와 전이 패키지의 전체 해결 및 Rust/Cargo 1.89.0 빌드 성공 여부.
- crate 배포 파일의 다운로드 가능 여부와 기존 벤더링 소스와의 버전 충돌.
- PostgreSQL 16 설치 권한, 사용 가능한 OS 패키지와 실제 서버 패치 버전.
- TLS 인증서 시험 자료 준비 및 실제 실패 조건 검증 가능 여부.
- 최종 활성 기능과 기존 gRPC 회귀 결과.

### 미결정 사항

#### 설계 전에 결정할 사항

범위와 PostgreSQL 설치 방향을 확정했으며 설계 진입을 막는 미결정 사항은 없었다.

#### 설계에서 결정할 사항

아래 내용은 설계로 전달한 항목이며 [설계의 결정](design-report-001.md#넘겨받은-미결정-사항의-처리)에서 처리했다.

- 기존 Cargo 명령을 유지하면서 DB 전용 경로를 제공할 인터페이스와 설정 생성 방식.
- 신규 소스의 분류와 버전 공존, 레지스트리 목록 및 검증 잠금 파일 관리 방식.
- 서버, 인증서와 검사 자료의 격리, 준비, 실행 및 정리 절차.
- 요청서의 각 검증 조건과 검사 구성 및 재현 명령의 대응.

## 인계 사항

### 단계와 인계 대상

두 Rosemary 의존성 공급 요청의 확정 요구사항을 [설계](design-report-001.md)로 전달했다.

### 설계 시 참조할 자료

- 이 report의 범위와 요구사항 및 제약과 확인 근거.
- 이 문서에 보존한 두 공급 요청의 확정 계약과 검증 완료 조건.
- [외부 소스 관리 규약](../../../third_party/README.md).
- [기존 소비 연결 안내](../../../docs/cress-integration.md).
- [로컬 Rust 패키지 연결 목록](../../../integration/rust-packages.json).
- [레지스트리 소스 목록](../../../third_party/rust-registry.json).
- [원본 소스 검사](../../../scripts/verify-sources.py).
- [gRPC 검증 구성](../../../checks/grpc-smoke/Cargo.toml).

### 설계에서 검토할 사항

설계에 전달한 미확인 전제와 결정 항목을 확인 대상으로 삼았다.
직접 패키지의 배포 확인과 선언된 최소 Rust 버전 확인만으로
전이 의존성 해결, 실제 빌드 또는 DB 동작의 성공을 판정하지 않는다.

### 미리 논의한 설계 내용

두 요청서가 지정한 오프라인 소비, 명시적 ring 선택, 메모리 CA,
DB 데이터 변환 및 기존 gRPC 유지 조건은 확정된 입력 계약이다.
구체적인 CLI, 소스 배치와 검증 구현은 논의 시점에는 미설계였으며 후속 설계에서 확정했다.

## 완료 체크리스트

### 작업과 확인 대상

대상은 이 논의 report와 두 요청서의 범위 및 설계 인계다.

### 단계 완료 및 이관 확인

- [x] 사용 주체와 상황, 해결할 문제 또는 개발 목적, 기대 결과가 정리되어 있다.
  - 확인 근거: 문제와 기대 결과에 Rosemary 소비 목적 및 Flax 공급 결과를 정리했다.
- [x] 포함 범위와 제외 범위가 구분되어 있고, 제외 항목의 사유와 구분이 기록되어 있다.
  - 확인 근거: 두 공급 요청과 환경 준비를 포함하고 제품 구현 및 향후 플랫폼 검증을 구분했다.
- [x] 필요한 기능 요구사항과 품질 요구사항이 설계에서 참조할 수 있게 정리되어 있다.
  - 확인 근거: 고정 버전, 기능, TLS 경계, 데이터 변환과 오프라인 및 회귀 조건을 요청서와 대조했다.
- [x] 확인한 사실과 근거, 지켜야 할 제약, 미확인 전제가 구분되어 있다.
  - 확인 근거: 실제 환경, 기존 소스 무결성과 공식 인덱스 조회 결과를 미검증 조건과 구분했다.
- [x] 설계 전에 결정할 사항이 해결되었고, 설계에서 결정할 사항은 구분하여 기록되어 있다.
  - 확인 근거: 범위와 설치 방향은 정해졌으며 CLI, 소스 배치와 환경 준비 방식은 설계에 연결했다.
- [x] 설계에 필요한 자료와 검토 사항을 인계 영역에서 찾을 수 있고, 미리 논의한 설계 내용은 합의 상태가 구분되어 있다.
  - 확인 근거: 입력 요청서와 실제 코드 및 관리 문서를 연결하고 확정 계약과 미설계 구현을 구분했다.

### 일괄 반영 기록

- B1: 단계 완료 및 이관 확인의 6개 항목 전체.
  - 반영 시각: 2026-10-05 22:05:53 (KST).
  - 근거: 사용자가 논의 결과 확인 요청에 동의하고,
    상위 요구사항은 두 파일을 기준으로 설계부터 진행하도록 지시했다.

## 사용자 승인

### 사용자 판단

사용자가 논의 결과의 범위, 제약과 설계 인계 내용에 동의하고 설계 진행을 지시했다.
당시 입력한 두 요청의 확정 계약은 이 문서의 범위와 요구사항에 보존했다.

### 보완 요청과 처리 결과

없음.

### 남은 사항과 이관 조건

논의에서 해결하지 못한 범위 결정은 없었다.
설계로 전달한 항목과 처리 결과는 위 인계 참조를 따른다.
설계에 넘긴 미확인 전제를 공급 및 검증 완료로 취급하지 않는다.
