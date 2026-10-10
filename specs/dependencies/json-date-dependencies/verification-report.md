---
status: completed
base_on: implementation-report.md
---

# JSON/날짜 의존성 공급 검증

## 단계 결과

### 작업 모델과 승인

주 작업은 [논의의 모델 승인](discussion-report.md#작업-모델과-승인)을 재사용한다.
사용자가 구현 결과, 검증 진행과 `Claude Sonnet / high` 교차 검토 제안에
"네 이견없음"이라고 응답하여 검토 모델과 담당 범위도 승인했다.
검토 대상은 공급 코드/소비 테스트, 설계 일치와 검사 근거다.
공용 모델 기준의 일반 코드 검토 범위에 따라 Sonnet과 high를 선택했다.
Claude Code 2.1.283이 설치되어 있음을 직접 확인했다.
Sonnet은 호출 별칭이며 CLI 결과의 modelUsage에서 실제 `claude-sonnet-5`를 확인했다.
추론 강도는 호출 옵션 `--effort high`로 지정했고 검토 범위를 변경하지 않았다.

### 복귀 및 재검토 기록

최초 검증이며 선행 설계와 구현의 변경은 없다.

- 회귀 계기가 된 report: 해당 없음.

### 검증 대상과 기준의 참조

[구현 기록](implementation-report.md)의 completed 상태, 체크리스트 6개와
사용자의 구현 종료/검증 진입 승인을 확인하고 정형 검사 PASS 후 진입했다.
[설계의 V1-V9 및 QA 계획](design-report.md#테스트-계획)을 그대로 사용한다.
원본 5개, 레지스트리 176개, 독립 소비와 문서 및 기존 회귀가 대상이다.

### 검사 항목과 결과

최종 구현 상태에서 새 출력 경로 `build/json-date-verification/fresh`를 처음 생성하고
Rust/Cargo 1.89.0, Ubuntu 24.04.4 x86_64에서 실행했다.
새 CARGO_HOME과 target으로 오프라인 컴파일했으며 그 경로에는 protoc가 없다.
구현 중의 사전 실행과 별도로 소비/원본/Cargo 모드/DB/gRPC 검사를 수행했다.

| ID | 판정 | 실제 결과와 근거 |
| --- | --- | --- |
| V1 | 통과 | 아카이브 5개의 SHA-256이 레지스트리와 일치하고 원본 209개 파일의 바이트가 보관 파일과 일치. 생성 체크섬 5개를 포함해 214개 파일. 라이선스 보존. 원본 검사에서 Git 스냅샷 5개 및 레지스트리 176개 전체 파일 목록/체크섬 일치 |
| V2 | 통과 | 새 캐시/출력 경로의 cargo-db test --locked --offline 성공. 소비 테스트 7개 실행. 새 잠금 파일 SHA-256은 구현 시점과 동일하며 protoc 미설치 확인 |
| V3 | 통과 | 일봉 JSON 바이트 검사에서 rt_cd/symbol/행 수/2026-10-01 및 가격 4개, 거래량과 거래대금의 설계 값 일치 |
| V4 | 통과 | 9007199254740993 및 u64::MAX의 JSON 숫자 출력과 재해석 값 일치. 범위 초과/음수/소수/빈 문자열 거부 |
| V5 | 통과 | 최소 manifest의 날짜/파일/수집 시각 해석, typed JSON 및 2개 JSONL 레코드 왕복 성공 |
| V6 | 통과 | YYYYMMDD와 YYYY-MM-DD 날짜 동일, 두 시각 모두 1790899775581009, 윤일 성공과 잘못된 날짜/JSON/RFC3339 거부 |
| V7 | 통과 | metadata의 실제 의존성 14개와 features-linux.json이 정확히 일치. serde_json=[std], chrono=[alloc,std], num-traits=[]. 시간대/wasm 패키지 없음 |
| V8 | 통과 | Cargo 모드 4개, PostgreSQL 단위 3개 및 DB 통합 9개, gRPC 1개 통과. 기존 잠금 파일 2개와 공급 도구/기존 원본 선언은 HEAD와 동일 |
| V9 | 통과 | 고정 버전/분류/레지스트리/소비 선언/잠금 파일/기능 및 안내 명령을 실제 파일과 대조. 기존 171개 레지스트리 항목이 모두 그대로 보존됨 |

재현 명령은 다음과 같다.

```sh
python3 scripts/flax.py --build-dir build/json-date-verification/fresh cargo-db test --manifest-path checks/json-date-smoke/Cargo.toml --locked --offline
python3 scripts/flax.py --build-dir build/json-date-verification/fresh cargo-db metadata --manifest-path checks/json-date-smoke/Cargo.toml --format-version 1 --locked --offline
python3 -B scripts/verify-sources.py
python3 -B -m unittest discover -s checks/cargo -v
python3 -B checks/postgres-smoke/run.py --build-dir build/json-date-verification/postgres
python3 scripts/flax.py cargo test --manifest-path checks/grpc-smoke/Cargo.toml --locked --offline
```

`build/json-date-verification/`의 json-date.log, source-integrity.log,
cargo-modes.log, metadata.json, features.json 및 artifact-checks.json에 실행/대조 근거를 보관한다.
DB 성공 근거는 postgres/logs/20261010T002536Z-dd4c2e/tests.log와 result.json이다.
result.json은 exit_code=0, cleanup_ok=true, work_removed=true다.
gRPC 성공은 grpc-authorized.log에 있다.

DB 최초 실행은 소켓 권한 오류로 실패했으며
postgres/logs/20261010T002212Z-aa20cb/에 실패/정리 근거를 남겼다.
gRPC 최초 실행도 소켓 권한 오류로 종료 코드 101이었으며 grpc.log에 보존했다.
두 검사는 별도 허용된 샌드박스 밖 localhost 실행으로 재검증하여 통과했다.
환경 제한 실패를 성공 실행과 구분하며 최초 실패 기록을 제거하지 않았다.

### 제외 및 미검증 사항

V1-V9에 미실행이나 판정 불가 항목은 없다.
제품 E2E, Walnut 전체 482행 파싱/저장/조회 및 DB QA는
[승인된 설계](design-report.md#e2e-테스트-적용-여부와-범위)에서 Flax 범위 밖으로 정했다.
외부 원본의 모든 자체 테스트와 선택 기능, 다른 OS/툴체인 조합은 확인하지 않았다.
이 결과는 고정된 Linux 최소 기능 소비와 기존 회귀에 한정한다.
사용자 QA와 실제 소비 프로젝트 리비전 갱신/반환 인계는 아직 완료하지 않았다.

### 검증 결론

실행한 V1-V9는 모두 기준을 충족했다.
구현 변경이 필요한 결함은 현재 검사에서 발견하지 않았다.
코드 중심 교차 검토에서 공급 코드/소비 테스트의 결함 지적은 없었다.
실행 방식에 대한 리뷰의 잘못된 설명은 CLI 원본 결과와 대조하여 검토자가 정정했다.

## 인계 사항

### 단계와 인계 대상

`dependencies/json-date-dependencies`의 검증 결과 전체를 같은 작업의 QA 단계에 전달한다.

### QA에 전달할 내용

[설계의 QA용 항목](design-report.md#qa용-항목과-판정-기준)에 따라
고정 버전/기능, 원본 분류와 소비 문서, V1-V9 근거 및 제품 검증의 경계를 사용자와 대조한다.
자동 검사 통과가 사용자 QA를 대신하지 않는다.
DB/gRPC의 최초 환경 오류와 성공 재실행, 자료 정리 및 범위 밖 항목도 함께 전달한다.

### 받은 인계의 처리 결과

[구현의 검증 인계](implementation-report.md#검증에-전달할-내용)에 따라
아카이브/파일 동일성, 기능/잠금 파일 보존과 소비 안내를 실제 대조했다.
원본 .gitignore에 걸리는 serde_json/zmij/autocfg의 Cargo.lock 3개는 물리적으로 보존했다.
최초 Git 등록 시 명시적 추가가 필요하다는 조건은 유지한다.
이번 단계에서는 Git 등록/커밋/푸시를 수행하지 않았다.

### 인계할 확인 항목

검증용 항목의 미해결은 없다.
QA에는 설계가 정한 사용자 검토를 전달한다.
공급 리비전과 소비 프로젝트의 고정 리비전 갱신은 반환 인계 시 별도로 확인한다.

## 완료 체크리스트

### 작업과 확인 대상

V1-V9의 실제 실행/판정과 범위, 교차 검토 및 QA 인계가 사용자 확인 대상이다.
사용자가 검증 결과/교차 검토와 6개 완료 항목 및 QA 인계를 확인했다.

### 단계 완료 및 인계 확인

- [x] 설계에서 정한 검증용 항목과 실제 검사 대상, 판정 기준이 연결되어 있다.
  - 확인 근거: 설계 V1-V9와 항목별 실제 판정을 연결했다. 사용자 확인 완료.
- [x] 최종 구현 상태의 유닛 테스트 재실행과 필요한 변경 후 재검증을 포함한 항목별 실행 결과와 판정 근거가 기록되어 있고, 실패, 미실행, 판정 불가가 통과와 구분되어 있다.
  - 확인 근거: 새 7개와 기존 17개 통과, 소켓 제한 실패와 허용된 재실행을 구분했다. 사용자 확인 완료.
- [x] 제외 항목에는 설계에서 합의한 제외 이유가 연결되어 있다.
  - 확인 근거: 제품 E2E 비적용과 Walnut 제품 검증의 범위를 연결했다. 사용자 확인 완료.
- [x] 완료 구분이 all_passed 또는 handoff이며, 선택한 이유와 근거가 기록되어 있다.
  - 확인 근거: V1-V9 통과에 따른 all_passed를 확인했다. 사용자 확인 완료.
- [x] handoff인 경우, 남은 항목을 받을 단계/번들, 확인 방법과 진행 조건 및 현재 완료의 타당성을 사용자와 합의했다.
  - 확인 근거: all_passed이므로 추가 미검증 인계 조건은 해당 없음. 사용자 확인 완료.
- [x] 검증 결과 전체와 QA 진행에 영향을 주는 사항을 인계 내용에서 확인할 수 있다.
  - 확인 근거: 전체 검사와 범위/환경 조건, 문서 및 QA 계획을 인계에 연결했다. 사용자 확인 완료.

### 일괄 반영 기록

| 묶음 | 대상 항목 | 반영 시각 |
| --- | --- | --- |
| B1 | 검증 완료 및 QA 인계 6개 항목 전체 | 2026-10-10 09:46:17 (KST) |

## 사용자 승인

### 완료 구분

all_passed

검증용 V1-V9가 모두 통과했다.
범위 밖 제품 검증과 사용자 QA를 자동 검증 완료에 포함하지 않는다.

### 사용자 판단

기준 선행 report는 [구현 기록](implementation-report.md)이다.
검증 결과/교차 검토를 설명하고 QA 진행을 질문했다.
사용자가 "네"라고 응답하여 검증 종료와 QA 진행을 승인했다.
공급 리비전 생성은 별도 Git 운영 요청에 따른다.

### 보완 요청과 처리 결과

[Claude 리뷰](verification-report-review-001.md)를 직접 CLI 호출로 받았다.
최초 샌드박스 호출은 DNS/API 오류(EAI_AGAIN), 종료 코드 1 및 is_error=true였고
claude-review-sandbox-failure.json에 보존했다.
허용된 네트워크 환경의 재실행은 종료 코드 0, is_error=false, subtype=success였다.
claude-review.json의 modelUsage는 claude-sonnet-5이며 실제 리뷰 파일도 생성되었다.

호출 옵션은 --model sonnet --effort high --output-format json --no-session-persistence,
--strict-mcp-config 및 빈 mcpServers 설정, --tools Read,Glob,Grep,Write였다.
Flax 자료/리뷰 템플릿 읽기와 지정 리뷰 파일 하나의 쓰기만 허용했다.
검토자의 독립 테스트 재실행은 권한 범위에 넣지 않았으므로 로그/코드 대조 검토로 한정한다.

검토자는 V1-V9 대응, 정수 정밀도와 시각 변환, 기능/그래프, 보존 및 실패/성공 구분에서
결함을 발견하지 못했다고 반환했다.
작성자도 실제 테스트/아카이브/metadata 대조와 항목별 비교한 결과 그 코드 판정에 동의한다.
다만 최초 실패와 리뷰 작성 중 빈 출력 파일을 보고 별도 대화형 세션이 대체 수행했다고 쓴
실행 설명은 실제 성공 CLI 결과와 맞지 않아 수용하지 않았다.
검토자에게 해당 설명만 정정하도록 요청했고 후속 CLI도 종료 코드 0,
is_error=false, subtype=success 및 claude-sonnet-5로 반환했다.
claude-review-followup.json에 결과가 있으며 검토자가 기존 리뷰의 실행 설명을 정정했다.
코드 판정은 그대로 유지했으며 신규 코드 결함이나 구현 보완 요구는 없다.
리뷰의 코드 판정과 검토 근거는 보존했다.

### 남은 사항과 인계 조건

교차 검토와 리뷰 파일의 실행 설명 정정은 완료했다.
사용자 확인/검증 종료 승인을 받아 QA로 진행한다.
사용자 QA와 공급 리비전/반환 인계는 아직 완료하지 않았다.
