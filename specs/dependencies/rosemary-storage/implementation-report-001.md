---
status: completed
base_on: design-report-001.md
---

# Rosemary 저장 의존성 공급 구현

이 문서는 구현 결과와 구현 중 사전 실행을 기록한다.
사전 실행은 정식 검증 판정과 구분하며 최종 실행 결과는
[검증](verification-report-001.md), 현재 반환 상태는 [최종 QA](qa-report-001.md)를 따른다.

## 단계 결과

### 작업 모델과 승인

[설계의 작업 모델과 승인](design-report-001.md#작업-모델과-승인)을 재사용한다.
구현 단계의 별도 모델이나 에이전트 실행은 없었다.

### 복귀 및 재검토 기록

최초 구현이며 해당 없음.

- 회귀 계기가 된 report: 해당 없음.

### 입력 설계와 구현 결과

[승인된 설계](design-report-001.md)의 다음 요구사항을 구현했다.

| 설계 요구 | 구현 결과 | 근거 |
| --- | --- | --- |
| 고정 버전과 원본 보존 | 기존 84개에 레지스트리 패키지 87개 추가, 총 171개. 기존 이름/버전은 재사용 | [소스 목록](../../../third_party/rust-registry.json), 원본 검사 결과 |
| 비호환 계열 공존 | getrandom, wasi와 windows-sys의 기존 소스를 계열 하위로 이동하고 필요한 다른 계열 추가. const-oid도 두 계열 공급 | 소스 목록의 경로와 파일별 SHA-256 검사 |
| protoc 없는 소비 | cargo-db에서 공통 오프라인 설정 적용, protoc 검사와 강제 환경 설정 제외 | [Cargo 실행기](../../../scripts/flax.py), Python 검사 4개 |
| 기존 소비 유지 | 기존 cargo의 protoc 검사와 환경 연결 유지, 두 설정 파일 분리 | Python 검사, gRPC 사전 실행 |
| 요청 패키지와 기능 | 정확한 직접 버전, ring 버전 및 전이 패키지를 고정 | [선언](../../../checks/postgres-smoke/Cargo.toml), [잠금 파일](../../../checks/postgres-smoke/Cargo.lock) |
| 실제 활성 기능 반환 | Linux 및 검증용 기능 합침을 기록하고 전이 default의 영향을 설명 | [기능 목록](../../../checks/postgres-smoke/features-linux.json), [소비 안내](../../../docs/rosemary-integration.md#공급-버전과-기능) |
| 실 DB 및 TLS 시험 | 임시 서버 3개와 제한된 SCRAM 계정, 새 인증서 준비 및 성공/실패 시험 작성 | [실행기](../../../checks/postgres-smoke/run.py), [DB 검사](../../../checks/postgres-smoke/tests/database.rs) |
| 기본 보조 기능 | PEM, SHA-256과 RwLock 소비 검사 작성 | [Rust 단위 검사](../../../checks/postgres-smoke/src/lib.rs) |
| 설치와 재현 안내 | 소비 명령, 설치, 암호화 조건, 자료와 정리 방법 작성 | [Rosemary 연결 안내](../../../docs/rosemary-integration.md) |

공급 준비의 다운로드와 완성된 소비 경로의 오프라인 빌드는 구분했다.
완성된 경로는 Flax의 원본만 사용하며 소비자의 잠금 파일을 소유하거나 교체하지 않는다.
외부 소비 사전 실행은 별도 임시 프로젝트의 자체 잠금 파일로 수행했다.

### 변경 대상

- Flax `third_party`: 원본 crate와 버전별 경로, 소스 목록 및 관리 안내.
- Flax `scripts`: 기존 Cargo 실행기의 DB 모드 추가.
- Flax `checks/cargo`, `checks/postgres-smoke`: CLI 계약, 기본 소비와 DB 통합 시험 구성.
- Flax `docs`, `README.md`: 공급 및 재현 안내.
- Flax `specs/dependencies`, `data/todo`: 승인된 작업의 구현 기록과 진행 상태.

기존 gRPC 잠금 파일과 upstream 소스 내용은 보존했다.
작업 시작 전 존재한 공용 경로 및 훅 관련 변경은 유지했다.
Rosemary 코드와 전역 설정은 변경하지 않았다.

구현 시점의 비교 기준 리비전은 `492cb81dbeb90d804b9449804a085ac6913b18ec`이다.
공급 반영 전의 기준이므로 이 SHA만 체크아웃하면 이번 공급을 사용할 수 없다.
소비용 리비전과 실제 인계 상태는 최종 QA의 인계 사항을 따른다.

### 테스트 작성과 구현 중 확인 결과

#### TDD 유닛 테스트 수행 결과

##### 결과 요약

Cargo 계약 검사 4개를 먼저 작성했다.
구현 전 새 동작 3개가 실패하고 기존 동작 1개는 통과했다.
구현 후 최종 코드에서 4개 모두 통과했다.

Rust 단위 소비 검사 3개도 작성하고 최종 코드에서 통과했다.
이는 반입한 upstream 기능의 사용 가능성을 확인하는 검사이며,
upstream 구현을 수정하거나 upstream 기능의 TDD를 수행한 것은 아니다.
기존 공용 경로 및 훅 단위 검사 10개도 통과했다.
구현 종료 시점에 관련 유닛 검사 실패, 미실행 및 판정 불가 항목은 없었다.

##### 동작별 상세 근거

| 동작과 조건 | 구현 전 관찰 | 구현 후 결과 |
| --- | --- | --- |
| protoc 없는 DB 설정, 로컬 소스와 offline 적용, PROTOC 강제 설정 없음 | with_protoc 인자가 없어 TypeError | 설정 내용을 파싱하여 source replacement, offline, env 및 설치 경로 부재 확인. 통과 |
| 기존 모드는 protoc 필요 | 기존 ValueError 확인. 통과 | 동일 계약 유지. 통과 |
| 두 모드의 설정 파일 분리 | DB용 인자가 없어 TypeError | DB 생성 후 기존 설정 내용과 경로 유지. 통과 |
| 별도 출력 경로의 CLI 인자 전달 | cargo-db 선택지가 없어 종료 2 | 공백 경로에서 cargo version --verbose 전달, 출력과 DB 설정 생성 확인. 통과 |
| PEM 파싱, SHA-256 및 RwLock | upstream 기능의 실패 확인은 수행하지 않음 | 3개 소비 검사 통과. 새 제품 기능의 TDD 근거로 사용하지 않음 |

CLI 검사는 기존 실행기와 같은 Cargo 하위 명령 전달 계약인 `version --verbose`를 사용한다.
최초 시험의 잘못된 선두 옵션 입력을 정정했으며 구현 전 실패 원인은 cargo-db 명령 부재였다.
Rust 검사 파일에는 rustfmt를 적용했다.

##### 재현 정보

Flax 루트에서 실행한다.

```sh
python3 -B -m unittest discover -s checks/cargo -v
python3 scripts/flax.py --build-dir build/postgres-offline cargo-db test --manifest-path checks/postgres-smoke/Cargo.toml --locked --offline --lib
python3 -B -m unittest discover -s checks/hooks -v
```

Python 검사는 임시 디렉토리의 설정과 소스 목록으로 파일 생성 동작을 격리하고,
임시 디렉토리와 모듈의 ROOT 대체를 시험 종료 때 복구한다.
CLI 검사는 실제 Flax 목록을 사용하지만 임시 출력 경로만 수정한다.
Rust 단위 검사는 DB와 네트워크 없이 공개 인증서, 알려진 입력과 로컬 잠금만 사용한다.
인증서 fixture는 파싱용 공개 CA이며 개인 키가 아니다.

환경은 Ubuntu 24.04.4 x86_64, Python 3.12.3, Rust/Cargo 1.89.0이다.
관련 로그는 다음과 같다.

- [구현 전 실패 로그](../../../build/rosemary-preparation/cargo-modes-red.log).
- [구현 후 Cargo 검사 로그](../../../build/rosemary-preparation/cargo-modes-green.log).
- [오프라인 테스트 컴파일 로그](../../../build/rosemary-preparation/postgres-compile.log).
- [Rust 및 DB 사전 실행 로그](../../../build/postgres-smoke/logs/20261005T141942Z-e7c4ed/tests.log).

DB 구성에 사용하지 않는 gRPC patch 경고는 공통 patch 목록에서 발생한다.
누락 패키지나 네트워크 사용을 뜻하지 않으며 빌드는 오프라인으로 성공했다.

#### 통합/E2E 테스트 작성 상태

DB 통합 검사 9개와 서버 실행기 작성을 완료했다.
인증, TLS의 정상 및 실패 조건, 풀, 트랜잭션과 데이터 왕복을 다룬다.
기존 gRPC smoke는 그대로 사용한다.
승인된 설계의 플랫폼 및 경계에 따라 E2E는 적용하지 않는다.
Rosemary 제품의 최상위 저장 흐름은 이 공급 작업의 대상이 아니다.

#### 검증 및 QA 실행 준비와 인계

PostgreSQL 설치는 sudo 비밀번호가 필요해 에이전트가 직접 수행할 수 없었다.
사용자가 안내한 apt 명령으로 설치했고 실제 버전을 확인했다.
이후 전용 서버와 fixture는 실행기에서 자동 준비했다.

| 실제 사전 실행 환경 | 확인 값 |
| --- | --- |
| OS/CPU | Ubuntu 24.04.4 LTS / x86_64 |
| PostgreSQL 및 psql | 16.15, Ubuntu 16.15-0ubuntu0.24.04.1 |
| Rust 및 Cargo | 1.89.0 |
| C 컴파일러 | GCC 13.3.0 |
| OpenSSL | 3.0.13 |

[환경 기록](../../../build/postgres-smoke/logs/20261005T141942Z-e7c4ed/environment.json)과
[실행 명령 기록](../../../build/postgres-smoke/logs/20261005T141942Z-e7c4ed/commands.log)을 보관했다.
샌드박스의 최초 소켓 생성은 Operation not permitted로 실패했고 해당 실행도 정리했다.
허용된 샌드박스 외부 실행에서는 정상 기동했다.
정식 검증도 루프백 TCP 및 Unix 소켓 권한이 필요하다.

DB 사전 실행에서 Rust 단위 3개와 DB 통합 9개가 모두 통과했다.
구현 단계의 참고 자료이며 검증 단계의 기준별 판정과 실행을 대체하지 않는다.
정상 TLS, 만료 TLS와 평문 서버 모두 제한 계정과 SCRAM TCP 규칙을 확인했다.
서버 3개를 종료하고 DB, 비밀번호와 개인 키를 삭제했다.
[정리 결과](../../../build/postgres-smoke/logs/20261005T141942Z-e7c4ed/result.json)의 exit_code는 0이며
cleanup_ok와 work_removed가 true다.

추가 사전 실행 결과는 다음과 같다.

- 원본 스냅샷 5개와 레지스트리 패키지 171개의 파일 목록 및 해시 검사 성공.
- 저장소 밖 공백 경로의 소비 프로젝트에서 자체 잠금 파일 생성,
  `--locked --offline` 시험과 모든 의존성의 Flax 소스 경로 확인 성공.
  [별도 소비 로그](../../../build/rosemary-preparation/independent-consumer.log)를 보관했다.
  이 소비 구성에는 테스트용 Tokio 추가 기능을 넣지 않았다.
- 기존 gRPC smoke의 생성 클라이언트/서버 교환 검사 1개 성공.
- 기존 공용 경로 및 훅 단위 검사 10개 성공.

검증용 명령과 기대 결과는
[설계의 검증 및 QA 계획](design-report-001.md)과
[소비 안내의 검사 절차](../../../docs/rosemary-integration.md#flax-소비-검사)에 연결한다.
DB 시험은 `python3 -B checks/postgres-smoke/run.py`로 실행하고,
실행별 로그와 각 정상 및 실패 조건, 기능 목록 및 정리 결과를 대조한다.
테스트 비밀번호와 개인 키는 소스, 로그 및 인계 기록에 넣지 않는다.

### 설계와의 차이 및 남은 사항

설계의 버전, 기능과 공급 범위 변경 및 미구현 항목은 없다.
구현 종료 당시 정식 검증과 QA는 후속 단계였으며 이후 두 단계의 완료 결과는 위 최종 기록을 따른다.
macOS Apple Silicon은 공급에 필요한 대상별 소스를 보존하지만 실제 빌드/실행은 확인하지 않았다.
Rosemary의 멱등성, 처리 상태, 성능, 종료 기아 및 lost wakeup 판단은 범위 밖이다.

## 인계 사항

### 단계와 인계 대상

변경 대상과 설계의 공급 계약을 기준으로 구현 결과를 [검증](verification-report-001.md) 단계에 전달했다.

### 검증에 전달할 내용

위 재현 정보와 실행 준비 및 인계에서 명령, 환경, 데이터와 로그를 확인한다.
검증에 전달한 실행 및 판정 대상은 다음과 같다.

1. 소스 무결성 및 기존 버전 보존, 두 잠금 파일에 필요한 대상별 소스 완결성.
2. 고정 잠금 파일, 빈 별도 캐시와 protoc 없는 DB 소비 및 실제 활성 기능.
3. 실제 PostgreSQL의 정상과 실패 TLS/인증, 풀, 트랜잭션, 데이터 왕복 및 보조 기능.
4. 기존 gRPC 소비 호환성과 성공/실패 실행의 서버 및 비밀 자료 정리.
5. 반환 문서, 재현 명령과 소스 경로의 일치 및 미확인 범위.

사전 실행은 참고 자료이며 verification 보고를 대신하지 않는다.
QA에서는 사용자가 반환 자료와 소비 안내를 검토할 수 있도록 에이전트가 실행 및 근거 확인을 보조한다.
소비 커밋 리비전 부재는 작업 트리 공급 상태와 함께 밝혀야 한다.

## 완료 체크리스트

### 작업과 확인 대상

고정 원본 공급, DB용 Cargo 경로와 소비 검사, 기존 경로 유지 및 문서화를 확인한다.

### 단계 완료 및 이관 확인

- [x] 이번 구현 범위의 합의된 설계가 코드에 반영되어 있다.
  - 확인 근거: 입력 설계와 구현 결과의 대응표, 원본 검사 및 소비 구성.
- [x] TDD 유닛 테스트의 실패 확인, 구현 후 통과와 필요한 리팩터링 후 확인 결과가 상세 근거 및 재현 정보와 함께 정리되어 있다.
  - 확인 근거: 동작별 상세 근거와 red/green 로그. upstream 소비 검사는 TDD와 구분했다.
- [x] 최종 코드 상태에서 이번에 작성하거나 수정한 유닛 테스트와 변경 영향을 받는 기존 유닛 테스트를 실행하고 결과를 기록했다.
  - 확인 근거: Cargo 4개, Rust 3개와 기존 훅 10개의 결과 및 재현 정보.
- [x] 적용하기로 한 통합/E2E 테스트 코드가 작성되어 있고, 작성 상태와 실행 준비 상태가 구분되어 있다.
  - 확인 근거: DB 통합 9개와 실행기, 기존 gRPC 검사. E2E 제외는 승인된 설계를 따른다.
- [x] 설계와의 차이, 미구현 사항과 남은 제약이 정리되어 있으며, 필요한 설계 변경은 합의된 절차로 처리되었다.
  - 확인 근거: 설계와의 차이 및 남은 사항. 명세 변경과 미구현은 없다.
- [x] 검증과 QA에 필요한 대상과 범위, 실행 방법, 환경과 데이터, 기대 결과와 판정 기준 및 준비 정보를 인계 내용에서 확인할 수 있다.
  - 확인 근거: 실행 준비, 소비 안내 및 검증에 전달할 내용.

### 일괄 반영 기록

- B1: 단계 완료 및 이관 확인의 6개 항목 전체.
  - 반영 시각: 2026-10-05 23:29:35 (KST).
  - 근거: 사용자가 검증 단계의 의미를 확인한 뒤 구현 결과에 대한 검증 진행을 승인했다.

## 사용자 승인

### 사용자 판단

기준 선행 파일은 design-report-001.md다.
사용자가 위 6개 확인 항목과 구현 결과를 기준으로 verification 진행을 승인했다.
이 구현 승인은 후속 검증 및 QA나 미확인 OS의 실행 성공을 의미하지 않는다.

### 보완 요청과 처리 결과

구현 단계의 보완 요청과 별도 교차 검토는 없었다.
후속 [코드 교차 검토와 대응](verification-report-001.md#보완-요청과-처리-결과)은 검증 단계에 기록했다.

### 남은 사항과 이관 조건

설계와의 차이 및 미구현 항목은 없었다.
검증에 전달한 대상과 실행 조건은 위 인계 사항에 기록했다.
