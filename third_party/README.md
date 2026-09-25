# 외부 소스 관리

외부 라이브러리의 고정된 릴리스 소스를 일반 파일로 반입하는 벤더링 구조다.
라이브러리별 `.git` 디렉토리나 Git 서브모듈 연결은 두지 않는다.

## 분류

| 디렉토리 | 범위 | 현재 반입한 소스 |
| --- | --- | --- |
| `core/` | 실행 기반과 범용 기능 | Tokio, Abseil, 실행 및 빌드 보조 패키지 |
| `networking/` | 서버 간 통신과 데이터 전송 | tonic, HTTP/2와 통신 보조 패키지 |
| `data/` | 데이터 표현, 저장과 분석 | Protobuf, prost, 자료구조 및 텍스트 처리 패키지 |
| `media/` | 오디오 처리와 음성 인식 및 생성 | 없음 |
| `web/` | 웹 서버 프레임워크와 화면 구성 | tonic의 하위 의존성인 Axum 및 웹 보조 패키지 |

분류는 한 단계로 유지하며 언어나 세부 기능별로 다시 나누지 않는다. 원본 저장소의
내부 구조는 보존한다. 성격이 겹치면 공식 README, 설계 문서와 실제 제공 기능에서
주된 역할을 확인해 한 곳에 배치한다. 소비 프로젝트가 참조하는 경로에는 버전을 넣지 않는다.
레지스트리 패키지의 두 비호환 계열이 동시에 필요할 때만 라이브러리 디렉토리 안에
계열별 소스를 둔다. 현재 `core/syn/2`, `core/syn/3`, `data/hashbrown/0.15`,
`data/hashbrown/0.17`이 해당하며, 소비 프로젝트는 Cargo 패키지 이름으로 참조한다.

## 반입한 버전

| 원본 저장소 | 버전 | 경로 |
| --- | --- | --- |
| [tokio-rs/tokio](https://github.com/tokio-rs/tokio) | 1.53.1 | `core/tokio/` |
| [grpc/grpc-rust](https://github.com/grpc/grpc-rust) | 0.14.6 (tonic) | `networking/tonic/` |
| [tokio-rs/prost](https://github.com/tokio-rs/prost) | 0.14.4 | `data/prost/` |
| [protocolbuffers/protobuf](https://github.com/protocolbuffers/protobuf) | 36.2 | `data/protobuf/` |
| [abseil/abseil-cpp](https://github.com/abseil/abseil-cpp) | 20250512.1 | `core/abseil-cpp/` |

[sources.json](sources.json)은 원본 URL, 릴리스 태그, 커밋 SHA, Git 트리 SHA,
저장 경로, 라이선스 파일, 로컬 수정 목록과 반입 파일 수를 기록한다. 경로는 Flax
루트를 기준으로 한다. 버전은 표에 적힌 대표 구성 요소의 버전이며, 같은 원본 저장소의
모든 패키지가 동일한 버전을 사용한다는 뜻은 아니다.

[rust-registry.json](rust-registry.json)은 Cargo 레지스트리에서 반입한 패키지 84개의
배포 버전, 원본 저장소, 가능한 경우 원본 커밋, 라이선스 식별자와 패키지 체크섬을
기록한다. 원본 패키지의 설명을 분류 근거로 함께 보관한다. crate에 포함된 라이선스와
`.cargo-checksum.json`도 보존한다. 레지스트리 패키지는 배포 소스이며 위 다섯 저장소의
전체 소스 스냅샷과 구분한다.

## 원본 보존과 업데이트

- 고정 커밋의 추적 파일 전체를 반입한다. 라이선스, 고지문, 원본 문서와 빌드 파일을 보존한다.
- Git 이력과 `.git`은 반입하지 않는다. 최초 반입 소스에는 로컬 수정이 없다.
- 원본의 ignore 규칙에 걸리는 추적 파일도 누락하지 않는다. 최초 Git 등록 시 반입한
  원본 파일을 명시적으로 추가하며, 이후 빌드 산출물을 함께 강제 추가하지 않는다.
- 업데이트는 새 태그의 커밋을 확인하고 기존 원본 및 로컬 수정과 비교한 뒤 수행한다.
  반입 내용과 `sources.json`을 함께 갱신하며 원격 브랜치의 최신 상태를 자동으로 따르지 않는다.
- 로컬 수정이 생기면 원본 대비 변경 근거와 `local_modifications`를 함께 기록한다.

## 빌드와 검증 범위

위 다섯 저장소는 각 고정 커밋의 추적 파일을 반입했다. 각 커밋에는 Git 서브모듈 항목이 없다.
원본 저장소 안에 이미 포함된 보조 패키지, 예제, 테스트와 외부 코드는 내부 구조대로 유지한다.

하위 의존성은 [Rust 검증 구성](../checks/grpc-smoke/Cargo.toml)의 기본 gRPC 기능과
Flax 루트의 CMake 구성에 필요한 범위를 확보한다. 모든 upstream 예제, 테스트,
선택 기능과 대상 플랫폼의 빌드를 보장하는 범위는 아니다.

`scripts/verify-sources.py`는 다섯 저장소의 Git 트리 해시와 원본 파일 수 및 Cargo
패키지의 파일별 SHA-256을 검사한다. 실제 빌드와 소비 프로젝트 연결 방법은
[Cress 연결 안내](../docs/cress-integration.md)를 따른다. `build/cargo-registry/`는
분류된 패키지를 Cargo가 읽도록 실행 스크립트가 만드는 임시 심볼릭 링크 목록이며,
실제 원본 소스는 이 디렉토리의 분류 경로에서 관리한다.
