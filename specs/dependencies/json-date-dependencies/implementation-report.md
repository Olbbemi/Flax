---
status: completed
base_on: design-report.md
---

# JSON/날짜 의존성 공급 구현

구현 중 실행과 다음 단계의 미실행 표시는 구현 단계 당시의 기록이다.
최종 판정은 [검증](verification-report.md), 현재 후속 상태는 [QA](qa-report.md)를 따른다.

## 단계 결과

### 작업 모델과 승인

[논의의 모델 승인](discussion-report.md#작업-모델과-승인)을 재사용한다.
모델, 강도와 담당 범위를 변경하지 않는다.
검증 단계의 교차 검토 모델은 아직 승인받거나 실행하지 않았다.

### 복귀 및 재검토 기록

최초 구현이며 복귀 및 선행 명세 변경은 해당 없음.

- 회귀 계기가 된 report: 해당 없음.

### 입력 설계와 구현 결과

[승인된 설계](design-report.md)의 고정 구성과 V1-V9를 기준으로 구현했다.
completed 상태와 체크리스트/승인 근거를 대조하고 정형 검사를 통과한 뒤 구현했다.

| 설계 대상 | 실제 구현과 근거 |
| --- | --- |
| 원본 5개 공급 | serde_json 1.0.151, chrono 0.4.45, zmij 1.0.23, num-traits 0.2.19, autocfg 1.5.1을 지정 분류 경로에 반입. 라이선스와 배포 소스 파일 및 체크섬 보존 |
| 레지스트리 정본 | [rust-registry.json](../../../third_party/rust-registry.json)에 출처/커밋/체크섬/라이선스와 새 잠금 파일 추가. 기존 171개 항목을 그대로 보존하고 총 176개로 갱신 |
| 독립 소비 | [Cargo.toml](../../../checks/json-date-smoke/Cargo.toml), [Cargo.lock](../../../checks/json-date-smoke/Cargo.lock)에 정확한 버전과 최소 기능 고정 |
| JSON/정수/날짜 검증 | [소비 테스트](../../../checks/json-date-smoke/src/lib.rs)에 실제 라이브러리를 사용하는 7개 검사 작성. [최소 입력](../../../checks/json-date-smoke/fixtures/)을 독립 보관 |
| 실제 기능 기록 | [features-linux.json](../../../checks/json-date-smoke/features-linux.json)에 의존성 14개의 기능 기록. serde_json=[std], chrono=[alloc,std], num-traits=[] 확인 |
| 소비 안내 | [JSON/날짜 안내](../../../docs/json-date-integration.md)와 루트/외부 소스 README 갱신. Rosemary 안내의 171개를 당시 공급 수로 명확히 표현 |

기존 원본 171개 항목과 gRPC/PostgreSQL 잠금 파일, scripts/flax.py,
integration/rust-packages.json 및 sources.json은 변경하지 않았다.
새 CLI, 제품 파서나 DB 스키마를 추가하지 않았다.

### 변경 대상

- Flax `third_party/`: 원본 5개, 레지스트리 메타데이터 및 외부 소스 안내 추가/갱신.
- Flax `checks/json-date-smoke/`: 독립 소비 선언과 잠금 파일, 테스트, 최소 입력과 활성 기능 추가.
- Flax `docs/`와 루트 README: JSON/날짜 소비 안내 및 전체 목록 설명 갱신.
- Flax `specs/dependencies/json-date-dependencies/`와 manifest: 단계 승인과 구현 근거 연결.
- 로컬 요청 기록: 진행 결과 반영. 생성 설정/캐시/로그와 할 일은 Git 제외 상태 유지.

### 테스트 작성과 구현 중 확인 결과

#### TDD 유닛 테스트 수행 결과

##### 결과 요약

이번 구현은 외부 원본의 공급이며 라이브러리 내부 기능을 새로 구현하는 작업이 아니다.
소비 테스트와 입력을 먼저 작성하고 기존 Flax 디렉토리 소스로 실행했다.
미공급 chrono 때문에 의존성 해결이 종료 코드 101로 실패했다.
원본/레지스트리를 추가한 뒤 같은 소비 테스트 7개가 모두 통과했다.
rustfmt로 테스트 원문을 정리한 최종 코드 상태에서도 7개가 통과했다.

실패 메시지는 `no matching package found`, `searched package name: chrono`이며
누락한 공급 기능과 대응한다.
전체 테스트가 의존성 해결 단계에서 막혔으므로 개별 함수의 assertion 실패를 관찰했다고 기록하지 않는다.
기존 Cargo 모드 검사 4개도 통과했다.

##### 동작별 상세 근거

아래 7개는 같은 미공급 의존성 실패를 공유하며 원본 반입 후 실제 실행되었다.

| 테스트 | 조건과 확인 결과 |
| --- | --- |
| daily_json_bytes_preserve_date_and_exact_integer_fields | 현재 응답의 필드 구조에서 symbol과 rt_cd, 2026-10-01 및 가격/거래량/거래대금의 정확한 u64 값 확인 |
| integers_beyond_float_precision_roundtrip_as_exact_json_numbers | 9007199254740993 및 u64::MAX가 문자열에서 정확히 해석되고 JSON 숫자와 재해석 값으로 보존됨 |
| out_of_range_and_invalid_integer_strings_are_rejected | u64 범위 초과, 음수, 소수와 빈 문자열이 표준 정수 파서에서 거부됨 |
| manifest_and_jsonl_records_roundtrip_with_collection_time | 최소 manifest의 날짜/파일/수집 시각 해석과 JSON 및 두 JSONL 레코드의 typed 왕복 확인 |
| explicit_offset_and_utc_times_produce_identical_microseconds | 요청의 +09:00/Z 시각이 모두 1790899775581009로 변환됨 |
| calendar_formats_agree_and_validate_leap_days | 두 날짜 형식의 동일성, 유효한 윤일과 잘못된 달력 날짜의 거부 확인 |
| malformed_json_and_rfc3339_are_rejected | 잘못된 JSON, RFC3339 및 offset 없는 시각을 각 라이브러리 오류로 거부 |

##### 재현 정보

Ubuntu 24.04.4 x86_64, Rust/Cargo 1.89.0에서 실행했다.
원본 준비와 소비를 구분하며, 반입 이후의 검사에는 네트워크를 사용하지 않는다.

```sh
python3 scripts/flax.py --build-dir build/json-date-implementation/green cargo-db test --manifest-path checks/json-date-smoke/Cargo.toml --locked --offline
python3 -B -m unittest discover -s checks/cargo -v
python3 -B scripts/verify-sources.py
```

새 출력 경로의 별도 CARGO_HOME과 target을 사용하며 해당 경로에 protoc install은 없다.
미공급 실패는 `build/json-date-implementation/red.log`, 최초 통과는 `green.log`,
최종 코드 상태 통과는 `green-final.log`에 보관한다.
활성 기능의 원본 metadata와 원본 무결성/모드 검사 로그도 같은 생성물 경로에 있다.

#### 통합/E2E 테스트 작성 상태

설계에 따른 독립 소비 테스트와 입력의 작성 및 실행 준비를 마쳤다.
7개 검사는 실제 serde, serde_json과 chrono를 연결하여 실행하며 mock이나 외부 서버가 없다.
제품 E2E는 승인된 설계에서 적용 대상이 아니며 추가하지 않았다.

기존 통합 검사는 구현 중 사전 실행으로 다음 결과를 확보했다.

| 사전 실행 | 관찰 결과 | 근거 |
| --- | --- | --- |
| 원본 검사 | 기존 Git 스냅샷 5개의 트리/파일 수와 레지스트리 176개의 파일 목록/SHA-256 일치 | `build/json-date-implementation/source-integrity.log` |
| gRPC | 생성 클라이언트/서버의 메시지와 상태 교환 1개 성공 | `build/json-date-regression/grpc.log` |
| PostgreSQL | 기존 라이브러리 단위 3개와 실제 DB 통합 9개 성공, 임시 서버/DB/비밀번호/개인 키 정리 성공 | `build/json-date-regression/postgres/logs/20261010T001537Z-0ea1ba/`의 tests.log 및 result.json |

DB/gRPC 최초 샌드박스 실행은 소켓 생성 제한으로 실패했다.
승인된 샌드박스 밖 localhost 실행에서 성공했으며 실패와 재실행을 구분한다.
DB result.json의 exit_code=0, cleanup_ok=true 및 work_removed=true를 확인했다.
이 사전 실행 결과는 검증 단계의 설계 기준 판정과 사용자 QA를 대체하지 않는다.

#### 검증 및 QA 실행 준비와 인계

실행 명령과 라이브러리별 검증 범위는 [소비 안내](../../../docs/json-date-integration.md),
최종 판정 기준과 사용자 참여 방식은 [설계의 테스트 계획](design-report.md#테스트-계획)을 따른다.
새 검증 fixture는 Walnut의 로컬 입력에서 필요한 공개 필드만 추출한 파일이며,
검사 실행에 Walnut 체크아웃을 요구하지 않는다.
이름과 버전이 고정된 원본 아카이브 및 배포 메타데이터는 `build/json-date-preparation/`에 있다.

### 설계와의 차이 및 남은 사항

요구사항이나 고정 버전/기능 및 소비 계약의 변경은 없다.
원본 반입과 소비 검증 코드 및 문서에 미구현 사항은 없다.
원본 보관 파일은 총 214개이며 세 패키지의 원본 Cargo.lock은 각 원본 .gitignore에 걸린다.
기존 원본 보존 규약에 따라 최초 Git 등록 시 이 파일도 명시적으로 추가해야 한다.
이 사실을 이유로 원본 .gitignore나 라이선스를 수정하지 않았다.

## 인계 사항

### 단계와 인계 대상

`dependencies/json-date-dependencies`의 구현 산출물을 같은 작업의 검증 단계에 전달한다.
원본 5개/레지스트리 176개, 새 소비 구성과 V1-V9 및 기존 회귀가 검증 대상이다.

### 검증에 전달할 내용

위 구현 대응표와 재현 정보 및 통합 사전 실행 근거를 참조한다.
원본 아카이브/반입 파일의 동일성, 실제 기능과 잠금 파일 보존 및 소비 문서의 대응을 V1-V9로 판정한다.
원본 파일의 등록 범위와 Git 제외 생성물도 함께 대조한다.
검증 단계의 교차 검토와 사용자 QA는 아직 진행하지 않았다.
반환 리비전과 프로젝트 간 실제 인계 결과는 해당 작업을 수행한 뒤 기록한다.

## 완료 체크리스트

### 작업과 확인 대상

위 변경 대상, TDD/최종 코드 실행 근거와 검증 인계가 확인 대상이다.
확인 근거는 사용자 승인 영역 및 B1에 기록한다.

### 단계 완료 및 인계 확인

- [x] 이번 구현 범위의 합의된 설계가 코드에 반영되어 있다.
  - 확인 근거: 고정 5개 원본과 독립 소비/문서를 설계 대응표에 연결했다.
- [x] 실패 확인, 구현 후 통과 및 필요한 정리 후 확인 결과가 상세 근거와 재현 정보로 정리되어 있다.
  - 확인 근거: 미공급 의존성 실패와 반입 후 7개 통과, 최종 정리 후 7개 통과 로그가 있다.
- [x] 최종 코드 상태의 새 테스트와 영향받는 기존 단위 검사를 실행하고 결과를 기록했다.
  - 확인 근거: 새 7개와 기존 Cargo 모드 4개가 통과했다.
- [x] 적용할 통합 테스트 코드가 작성되었고 작성/실행 준비 상태가 구분되어 있다.
  - 확인 근거: 독립 소비 구성과 입력을 작성했고 통합 사전 실행 및 E2E 비적용을 구분했다.
- [x] 설계와의 차이, 미구현 사항 및 남은 제약이 정리되어 있다.
  - 확인 근거: 설계 변경과 미구현 사항은 없으며 원본 Git 등록 조건과 localhost 실행 권한을 인계했다.
- [x] 검증/QA의 범위, 실행 방법, 환경/입력과 판정 기준 및 준비 정보를 인계에서 확인할 수 있다.
  - 확인 근거: 소비 안내와 설계 V1-V9, 로그 위치를 연결했다.

### 일괄 반영 기록

| 묶음 | 대상 항목 | 반영 시각 |
| --- | --- | --- |
| B1 | 구현 완료 및 인계 6개 항목 전체 | 2026-10-10 09:21:59 (KST) |

## 사용자 승인

### 사용자 판단

기준 선행 report는 [설계](design-report.md)이다.
사용자는 새 원본/소비 구성/문서와 상세 수행 근거 및 검증 인계를 승인했다.
구현 결과 승인과 검증 진행 및 Claude Sonnet / high 제안에 "네 이견없음"이라고 응답했다.

### 보완 요청과 처리 결과

현재 구현에 대한 사용자 보완 요청은 없다.
교차 검토는 설계에서 정한 검증 단계에 연결하며 아직 실행하지 않았다.

### 남은 사항과 인계 조건

구현 결과/체크리스트 확인과 단계 종료 승인을 받아 검증 단계로 진행한다.
검증과 사용자 QA, 반환 리비전 및 실제 프로젝트 인계는 아직 완료하지 않았다.
