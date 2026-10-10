# 외부 소스 관리

외부 라이브러리의 고정된 릴리스 소스를 일반 파일로 반입하여 보관한다.
라이브러리별 `.git` 디렉토리나 Git 서브모듈 연결은 두지 않는다.
프로젝트 역할과 루트 디렉토리의 Git 관리 범위는 [Flax 안내](../README.md)를 따른다.

## 주요 라이브러리

직접 사용하는 주요 라이브러리의 용도와 대표 버전을 정리한다.
경로는 이 디렉토리를 기준으로 한다.

| 라이브러리 | 버전 | 용도 | 경로 |
| --- | --- | --- | --- |
| Tokio | 1.53.1 | 비동기 작업 실행, 네트워크 I/O와 동기화 | [core/tokio/](core/tokio/) |
| tonic | 0.14.6 | Rust gRPC 클라이언트와 서버 및 서비스 코드 생성 | [networking/tonic/](networking/tonic/) |
| prost | 0.14.4 | Rust Protobuf 메시지와 메시지 코드 생성 | [data/prost/](data/prost/) |
| Protobuf | 36.2 | `protoc`와 C++ 메시지 코드 생성 및 직렬화 | [data/protobuf/](data/protobuf/) |
| tokio-postgres | 0.7.18 | 비동기 PostgreSQL 드라이버 | [data/tokio-postgres/](data/tokio-postgres/) |
| deadpool-postgres | 0.14.2 | PostgreSQL 연결 풀 | [data/deadpool-postgres/](data/deadpool-postgres/) |
| rustls | 0.23.45 | TLS 접속과 서버 인증서 검증 | [networking/rustls/](networking/rustls/) |
| ring | 0.17.14 | rustls에 제공하는 암호화 기능 | [core/ring/](core/ring/) |
| sha2 | 0.11.0 | SHA-256 등 SHA-2 해시 | [core/sha2/](core/sha2/) |
| parking_lot | 0.12.5 | Mutex와 RwLock 등 동기화 및 잠금 | [core/parking_lot/](core/parking_lot/) |
| serde_json | 1.0.151 | JSON 바이트 해석과 JSON/JSONL 출력 | [data/serde_json/](data/serde_json/) |
| chrono | 0.4.45 | 달력 날짜 해석과 명시적 시간대 및 UTC 시각 변환 | [data/chrono/](data/chrono/) |

표에 없는 디렉토리에는 주요 라이브러리가 사용하는 하위 의존성,
연결 보조 패키지와 빌드용 패키지 등이 들어 있다.
같은 원본 프로젝트에서 별도로 배포한 패키지와 다른 프로젝트의 의존성을 모두 포함한다.
별도 배포 패키지를 기능별로 배치하며 원본의 내부 코드를 임의로 나누지 않는다.
한 패키지를 여러 주요 라이브러리가 함께 사용할 수도 있다.

소비자는 필요한 패키지만 선언하고, 의존성 해결을 통해 필요한 하위 패키지를 연결한다.
개별 하위 패키지는 이 안내에서 나열하지 않으며 전체 출처와 버전은 아래 소스 목록으로 관리한다.
직접 선언할 패키지와 활성 기능은 [Cress 연결 안내](../docs/cress-integration.md)와
[Rosemary 연결 안내](../docs/rosemary-integration.md)와
[JSON/날짜 연결 안내](../docs/json-date-integration.md)를 따른다.

## 분류

| 분류 | 범위 |
| --- | --- |
| `core/` | 실행 기반과 범용 기능 및 빌드 보조 |
| `networking/` | 서버 간 통신과 데이터 전송 및 TLS |
| `data/` | 데이터 표현, 저장과 분석 및 자료구조와 텍스트 처리 |
| `media/` | 오디오 처리와 음성 인식 및 생성. 현재 반입한 소스 없음 |
| `web/` | 웹 서버와 화면 구성 및 관련 보조 기능 |

분류는 한 단계로 유지하며 언어나 세부 기능별로 다시 나누지 않는다.
원본 저장소의 내부 구조는 보존한다.
성격이 겹치면 공식 README, 설계 문서와 실제 제공 기능에서 주된 역할을 확인해 한 곳에 배치한다.
분류는 소스 보관 기준이며 같은 분류의 패키지를 모두 사용한다는 뜻은 아니다.
소비 프로젝트가 참조하는 경로에는 버전을 넣지 않는다.
레지스트리 패키지의 두 비호환 계열이 동시에 필요할 때만 라이브러리 디렉토리 안에
계열별 소스를 둔다.
소비 프로젝트는 물리적 경로 대신 Cargo 패키지 이름으로 참조한다.

## 출처와 버전의 정본

원본 저장소의 고정 커밋에 있는 추적 파일 전체를 가져온 소스 스냅샷과,
Cargo 레지스트리에서 배포한 패키지 소스를 함께 보관한다.

[sources.json](sources.json)은 원본 URL, 릴리스 태그, 커밋 SHA, Git 트리 SHA,
저장 경로, 라이선스 파일, 로컬 수정 목록과 반입 파일 수를 기록한다.
경로는 Flax 루트를 기준으로 한다.
주요 라이브러리 표의 버전은 대표 구성 요소의 버전이며,
같은 원본 저장소의 모든 패키지가 동일한 버전을 사용한다는 뜻은 아니다.

[rust-registry.json](rust-registry.json)은 Cargo 레지스트리에서 반입한 패키지 176개의
배포 버전, 원본 저장소, 가능한 경우 원본 커밋, 라이선스 식별자와 패키지 체크섬을
기록한다.
원본 패키지의 설명을 분류 근거로 함께 보관한다.
crate에 포함된 라이선스와 `.cargo-checksum.json`도 보존한다.
레지스트리 패키지는 배포 소스이며 원본 저장소 5개의 전체 소스 스냅샷과 구분한다.
목록의 `lockfiles`는 gRPC, PostgreSQL과 JSON/날짜 소비 검증의 잠금 파일을 연결하며,
기존 `lockfile` 필드는 gRPC 경로를 유지한다.

## 원본 보존과 업데이트

- 고정 커밋의 추적 파일 전체를 반입한다. 라이선스, 고지문, 원본 문서와 빌드 파일을 보존한다.
- Git 이력과 `.git`은 반입하지 않는다. 최초 반입 소스에는 로컬 수정이 없다.
- 원본의 ignore 규칙에 걸리는 추적 파일도 누락하지 않는다. 최초 Git 등록 시 반입한
  원본 파일을 명시적으로 추가하며, 이후 빌드 산출물을 함께 강제 추가하지 않는다.
- 업데이트는 새 태그의 커밋이나 패키지 배포 버전을 확인하고 기존 원본 및 로컬 수정과 비교한 뒤 수행한다.
  반입 내용과 해당 소스 목록을 함께 갱신하며 원격 브랜치의 최신 상태를 자동으로 따르지 않는다.
- 로컬 수정이 생기면 원본 대비 변경 근거와 `local_modifications`를 함께 기록한다.

## 빌드와 검증 범위

소스 스냅샷 5개는 각 고정 커밋의 추적 파일을 반입했다.
각 커밋에는 Git 서브모듈 항목이 없다.
원본 저장소 안에 이미 포함된 보조 패키지, 예제, 테스트와 외부 코드는 내부 구조대로 유지한다.

하위 의존성은 [gRPC 검증 구성](../checks/grpc-smoke/Cargo.toml),
[PostgreSQL 검증 구성](../checks/postgres-smoke/Cargo.toml),
[JSON/날짜 검증 구성](../checks/json-date-smoke/Cargo.toml)과
Flax 루트의 CMake 구성에 필요한 범위를 확보한다.
Cargo의 오프라인 해결에 필요한 대상별 패키지도 보존한다.
모든 upstream 예제, 테스트, 선택 기능과 대상 플랫폼의 빌드를 보장하는 범위는 아니다.

`scripts/verify-sources.py`는 다섯 저장소의 Git 트리 해시와 원본 파일 수 및
Cargo 패키지의 파일별 SHA-256을 검사한다.
`build/cargo-registry/`는
분류된 패키지를 Cargo가 읽도록 실행 스크립트가 만드는 임시 심볼릭 링크 목록이며,
실제 원본 소스는 이 디렉토리의 분류 경로에서 관리한다.
