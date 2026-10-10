# Flax

여러 프로젝트에서 사용할 외부 오픈소스의 소스와 고정 버전, 로컬 수정 및 빌드 구성을 관리한다.

## 역할과 구성

원본 소스는 `third_party/`에 일반 파일로 보관하고 Git으로 직접 추적한다.
라이브러리별 Git 저장소나 서브모듈은 두지 않는다.
소비 프로젝트는 Flax를 서브모듈로 연결하여 필요한 의존성을 사용한다.

Flax는 Cress, Walnut, Iris와 Rosemary의 의존성 공급과 연결 구성을 담당한다.
자체 공통 코드는 Cress, 금융 기능은 Walnut, 음성 기능은 Iris가 담당한다.
제품의 서비스 로직과 전체 시스템의 배포 구성은 Flax에 포함하지 않는다.

## 주요 오픈소스

| 용도 | 주요 라이브러리 |
| --- | --- |
| 비동기 실행과 I/O | Tokio |
| gRPC 통신과 Protobuf 메시지 및 코드 생성 | tonic, prost, Protobuf |
| PostgreSQL 접속과 연결 풀 | tokio-postgres, deadpool-postgres |
| TLS와 암호화 및 해시 | rustls, ring, sha2 |
| 동기화와 잠금 | parking_lot |
| JSON 해석과 출력, 날짜와 시각 변환 | serde_json, chrono |

이 목록은 직접 사용하는 주요 구성을 설명한다.
각 라이브러리에 필요한 하위 의존성과 빌드용 패키지도 함께 보관한다.
하위 패키지는 같은 원본 프로젝트의 구성 요소이거나 다른 프로젝트의 라이브러리일 수 있다.
소비 프로젝트가 선언한 의존성, 기능과 대상 환경에 따라 필요한 부분을 선택하므로,
보관된 모든 소스를 한 프로그램에서 사용하는 것은 아니다.

주요 라이브러리의 버전과 용도, 분류 및 원본 관리 기준은
[외부 소스 안내](third_party/README.md)에서 확인한다.

## 디렉토리와 Git 관리 범위

| 경로 | 역할 | Git 관리 |
| --- | --- | --- |
| `third_party/` | 외부 원본 소스, 라이선스와 출처 및 버전 목록 | 포함 |
| `scripts/` | 빌드, 의존성 연결과 원본 검사 및 공용 경로 준비 | 포함 |
| `integration/` | 소비 도구가 참조하는 패키지 연결 설정 | 포함 |
| `checks/` | 소스 공급과 연결 동작을 확인하는 검증 코드 및 입력 자료 | 포함 |
| `tools/` | 프로젝트 Git 훅 등 저장소 관리 도구 | 포함 |
| `docs/` | 소비 프로젝트의 준비, 빌드, 연결과 검증 안내 | 포함 |
| `specs/` | 요구사항, 설계와 구현 및 검증과 QA 기록 | 포함 |
| `data/todo/` | 공용 경로에서 접근하는 로컬 할 일과 요청 | 제외 |
| `build/` | 생성된 설정, 캐시, 빌드 결과와 실행 로그 | 제외 |

루트의 README, CMake 구성과 `.gitignore`도 Git으로 관리한다.
관리 대상은 변경한 파일과 그 변경에 필요한 관련 파일을 함께 커밋한다.
외부 원본에 포함된 문서, 예제와 테스트는 원본 보존 대상이며 빌드 산출물과 구분한다.

## 빌드와 소비 프로젝트 연결

소비 프로젝트는 자체 `Cargo.toml`과 `Cargo.lock`을 관리하고,
Flax의 실행 스크립트를 통해 로컬 소스와 오프라인 의존성을 연결한다.
생성되는 설정, 캐시와 빌드 결과는 `build/`에 둔다.

[Cress 연결 안내](docs/cress-integration.md)는 Rust gRPC와 C++ Protobuf의
준비 환경, 코드 생성, 빌드와 연결 방법을 설명한다.
Flax 루트에서 네이티브 도구를 빌드하고 Rust gRPC 연동을 검사하는 명령은 다음과 같다.

```sh
python3 scripts/flax.py build-native --jobs 2
python3 scripts/flax.py cargo test --manifest-path checks/grpc-smoke/Cargo.toml --locked --offline
```

[Rosemary 연결 안내](docs/rosemary-integration.md)는 PostgreSQL, TLS와 잠금 의존성의
고정 버전, 기능과 오프라인 소비 방법을 설명한다.
DB 전용 소비에는 Protobuf 빌드 없이 `cargo-db`를 사용한다.
Flax 루트에서 DB 의존성을 빌드하고 실제 연결을 검사하는 명령은 다음과 같다.

```sh
python3 scripts/flax.py cargo-db build --manifest-path checks/postgres-smoke/Cargo.toml --locked --offline
python3 -B checks/postgres-smoke/run.py
```

DB 연결 검사는 PostgreSQL 16, C 컴파일러와 OpenSSL이 설치된 환경에서
별도 검증 서버를 준비하고 검사 후 정리한다.
PostgreSQL 서버와 Rust 도구 체인은 환경에 설치하며 Flax의 반입 소스에 포함하지 않는다.

[JSON과 날짜 연결 안내](docs/json-date-integration.md)는 serde_json과 chrono의
고정 버전, 최소 기능과 오프라인 소비 방법을 설명한다.
protoc 없는 cargo-db 경로로 기본 JSON/JSONL 및 날짜와 시각 변환을 검사한다.

```sh
python3 scripts/flax.py cargo-db test --manifest-path checks/json-date-smoke/Cargo.toml --locked --offline
```

## 할 일 경로와 Git 훅

할 일과 요청은 `data/todo/`에 보관한다.
이 경로는 Git에서 제외하며 로컬에 유지한다.
공용 접근 경로 `~/.local/share/flax`는 이 체크아웃의 `data/`를 가리킨다.

[Hortulanus](https://github.com/Olbbemi/Hortulanus)의 공통 훅이 설치된 환경에서
최초 clone 시 `tools/scripts/git/post-checkout`이 보관 디렉터리와 링크를 준비한다.
`origin`이 GitHub의 `Olbbemi/Flax`인 기본 작업 트리만 대상으로 하며,
HTTPS와 SSH 주소를 지원한다.
일반 checkout과 추가 worktree 생성에서는 연결을 변경하지 않는다.
같은 대상을 가리키는 유효한 링크는 유지하고,
다른 파일, 디렉터리와 끊어진 링크는 보존한 채 오류로 알린다.

기존 체크아웃이나 훅이 실행되지 않은 clone에서는 Flax 루트에서 수동 연결한다.
`--dry-run`은 충돌과 변경 예정 내용을 확인하며 파일을 변경하지 않는다.

```sh
python3 -B scripts/link_shared_todo.py . --dry-run
python3 -B scripts/link_shared_todo.py .
```

공통 훅이 없는 기존 저장소는 Hortulanus의 업데이트 절차로 연결한다.
`.git/hooks`의 공통 파일은 직접 수정하지 않는다.
프로젝트 훅은 할 일 경로만 준비하며, 세션 시작 시 기록 확인은 에이전트가 수행한다.

훅과 링크 준비 동작은 임시 홈과 로컬 Git 저장소에서 검증한다.

```sh
python3 -B -m unittest discover -s checks/hooks -v
```

## 이름 선정 이유

- 원문 식물명: `Dried Flax`
- 꽃말 전체: `Utility.`
- 번역: 유용성.
- 해석: 여러 프로젝트에 필요한 외부 구성 요소를 재사용 가능한 형태로 제공한다.

저장소 이름은 `Dried Flax`에서 `Dried`를 생략한 `Flax`로 정했다.
이 근거는 `Dried Flax` 항목에 한정하며, 별도 `Flax` 항목의 꽃말과 혼용하지 않는다.
역할과의 연결은 프로젝트의 해석이다.

출처: Kate Greenaway, [Language of Flowers (1884), 꽃 이름별 목록 D](https://www.gutenberg.org/files/31591/31591-h/31591-h.htm).

## 제공 및 검증 범위

Rust gRPC, C++ Protobuf, PostgreSQL과 JSON/날짜 의존성의 오프라인 소비 구성을 제공한다.
PostgreSQL 구성은 SCRAM 인증, ring 기반 TLS, SHA-256과 parking_lot 잠금을 검증한다.
JSON/날짜 구성은 문자열 정수의 정확한 변환, JSON/JSONL 출력과 달력 및 명시적 시간대 변환을 검사한다.
gRPC 구성의 TLS와 압축, gRPC C++/Python 구성은 현재 공급 범위에 포함하지 않는다.

소스를 보관한 범위와 실제 빌드 및 실행을 검증한 범위는 구분한다.
환경, 활성 기능과 검사 결과는 각 소비 안내에서 확인하고,
이번 PostgreSQL 공급의 단계별 결과는
[작업 기록](specs/dependencies/rosemary-storage/qa-report-001.md)에서 확인한다.
JSON/날짜 공급의 최종 실행 및 교차 검토는
[검증 기록](specs/dependencies/json-date-dependencies/verification-report.md),
사용자 확인과 최종 적용 범위는
[QA 기록](specs/dependencies/json-date-dependencies/qa-report.md)에서 확인한다.
