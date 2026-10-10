# 코드 중심 교차 검증

- 검토자: Claude
- 모델명/버전: Claude Sonnet 5 (모델 ID: claude-sonnet-5). 시스템 환경 정보로 직접 확인한 값이며, 전달받은 호출 옵션의 `--model sonnet`은 별칭이다. 추론 강도(`--effort high`)는 이 세션에서 독립적으로 확인할 수 있는 파라미터가 아니므로 호출자가 전달한 값 그대로 기록하며 자체 확인은 불가로 남긴다. CLI 버전 2.1.283은 모델 버전이 아니다.
- 검토 대상: `/home/olbbemi/Project/Flax/specs/dependencies/json-date-dependencies/verification-report.md` (같은 디렉토리의 discussion-report.md, design-report.md, implementation-report.md을 선행 근거로 함께 확인)

## 실행 대상과 근거

- 실행 대상/전달 방식: 호출자(Codex)는 "Claude CLI 직접 호출"(`--model sonnet --effort high --output-format json --no-session-persistence --strict-mcp-config --mcp-config {"mcpServers":{}} --tools Read,Glob,Grep,Write`)을 전달 방식으로 명시했다. `build/json-date-verification/claude-review-sandbox-failure.json`에 남은 최초 시도(session_id `aafa2ef4-0446-4cc1-b4c5-8d8d35fe7796`)는 `terminal_reason: "api_error"`, `is_error:true`, `result: "API Error: Can't reach the API server — check your internet or DNS (EAI_AGAIN)"`로 종료되어, 헤드리스 CLI가 샌드박스에서 네트워크(DNS)에 도달하지 못해 실패했음을 보여준다. 이후 네트워크 권한을 받아 같은 옵션으로 재호출한 결과가 같은 디렉토리의 `claude-review.json`에 기록되어 있다. 이 파일을 다시 읽은 결과 더 이상 빈 파일이 아니며, `is_error:false`, `subtype:"success"`, `terminal_reason:"completed"`, `modelUsage`의 모델 키 `claude-sonnet-5`, `duration_ms:390746`을 담은 완결된 결과를 보여준다. 이 파일의 `session_id`(`daa196cd-4d6b-426b-b645-ec724c3007d8`)는 최초 검토를 수행한 세션의 ID와 정확히 일치한다. 따라서 이 재호출은 "별도의 대화형 대체 세션"이 아니라, 재시도된 헤드리스 CLI 실행 자체였다고 정정한다. 이전 검토 시점에 `claude-review.json`이 빈 파일(0바이트)로 관찰된 것은 실행이 산출물을 내지 못했다는 의미가 아니라, 출력 리다이렉션이 프로세스 종료·버퍼 플러시 이전 시점에 관찰되었기 때문으로 판단한다. 다만 이 JSON 자체에는 프로세스 종료 코드(`exit_code`) 필드가 없어, 호출자(Codex)가 전달한 "종료 코드 0"은 호출자의 관찰값으로 기록하며, 이 세션이 JSON 판독만으로 독립적으로 재확인한 값은 아니다.
- 호출 명령과 옵션: 위 옵션 문자열은 호출자가 전달한 그대로이며, 실제 이 검토 세션의 도구 권한(Read/Glob/Grep/Write만 가능, Bash 불가)은 전달받은 `--tools Read,Glob,Grep,Write`와 일치한다. 위에서 확인한 `session_id` 일치를 근거로, 이 세션은 전달받은 옵션으로 재호출된 헤드리스 CLI 실행 자체로 정정한다.
- 확인한 실행 결과: 지정된 대상 전체를 Read/Glob/Grep로 읽고, 이 리뷰 파일 하나를 신규 작성했다. 코드/명세/로그를 수정하지 않았다. Bash가 없어 `cargo test`, `verify-sources.py`, DB/gRPC 러너 등 어떤 명령도 독립적으로 재실행하지 못했으며, 아래 결과는 전부 기존에 보관된 로그/아티팩트의 판독과 소스 코드 직접 대조, 그리고 수동 계산(시각 변환) 검증에 근거한다.

## 검토 범위와 기준

[설계의 테스트 계획](design-report.md#테스트-계획) V1-V9를 판정 기준으로 삼고, [검증 기록](verification-report.md)의 각 판정과 실제 근거 파일을 대조했다. 사용자 요청에 따라 다음을 직접 읽었다.

- `specs/dependencies/json-date-dependencies/`의 discussion/design/implementation/verification-report.md 전체.
- `checks/json-date-smoke/`의 Cargo.toml, Cargo.lock, src/lib.rs, fixtures/daily.json, fixtures/manifest.json, features-linux.json.
- `third_party/rust-registry.json`의 신규 5개 패키지 항목과 전체 176개 집계.
- `third_party/data/serde_json`, `third_party/data/chrono`, `third_party/data/zmij`, `third_party/core/num-traits`, `third_party/core/autocfg`의 Cargo.toml(생성본)과 라이선스 파일, `.cargo-checksum.json`/`.cargo_vcs_info.json` 존재.
- `scripts/flax.py`, `scripts/verify-sources.py` 전체.
- `docs/json-date-integration.md`, 루트 `README.md`, `third_party/README.md`.
- `build/json-date-verification/`의 `json-date.log`, `source-integrity.log`, `cargo-modes.log`, `grpc.log`, `grpc-authorized.log`, `metadata.json`(부분, grep), `features.json`, `artifact-checks.json`, `report-checks.json`, `claude-review.json`, `claude-review-sandbox-failure.json`.
- `build/json-date-verification/postgres/logs/20261010T002536Z-dd4c2e/`의 `result.json`, `tests.log`와 `20261010T002212Z-aa20cb/`의 `result.json`, `commands.log`(최초 실패 근거).

집중 확인 사항은 사용자 지시에 따라 (1) 설계 V1-V9와 실제 검증 결과의 일치, (2) 정수 정밀도와 날짜/시각 경계, (3) 최소 기능 구성과 공급 그래프, (4) 오프라인 소비, (5) 기존 소스 보존, (6) 테스트의 실제 검증 범위와 누락이다. 요청받은 범위는 전부 읽었으며, 실행 범위와 요청 범위의 차이는 Bash 불가로 인한 미실행(아래 "확인하지 못한 사항")으로 구분한다.

## 검토 결과

지적할 결함은 발견하지 못했다. 아래는 직접 대조하여 확인한 세부 근거이며, 지적이 아니라 검증 결과를 뒷받침하는 확인 기록이다.

1. **V1 (원본 무결성)** — `third_party/rust-registry.json`의 `"name":` 수를 직접 집계하면 176개이며, `artifact-checks.json`의 `all_registry_entries: 176`, `old_registry_entries_preserved: 171`과 일치한다. 신규 5개(`autocfg`, `chrono`, `num-traits`, `serde_json`, `zmij`)의 `path`/`package_sha256`/`license`가 레지스트리와 `third_party/<분류>/<패키지>/.cargo-checksum.json` 및 실제 라이선스 파일(`LICENSE-MIT`, `LICENSE-APACHE`, `chrono/LICENSE.txt`)의 존재와 대응한다. `source-integrity.log`의 "OK 176 registry packages: file lists and SHA-256 checksums"는 `scripts/verify-sources.py`가 정상 종료했음을 보여준다. 다만 이 스크립트는 `rust-registry.json`의 `package_sha256`과 로컬 `.cargo-checksum.json`의 내부 일치만 오프라인으로 검사하며, crates.io 배포 체크섬과의 최초 대조(설계 1단계)는 준비 단계에서 수행된 것으로 이번 검증 기록이 서술하고 있을 뿐, 이번 로그 자체에서 네트워크 재대조를 재현하지는 않는다. 이는 설계가 의도한 오프라인 경계와 일치하므로 결함은 아니다.
2. **V2/V8 (오프라인 소비, protoc 없는 경로)** — `json-date.log`는 `build/json-date-verification/fresh`라는 새 경로에서 `cargo-db test`가 14개 의존성(`proc-macro2`, `unicode-ident`, `quote`, `serde_core`, `autocfg`, `zmij`, `serde_json`, `serde`, `itoa`, `memchr`, `num-traits`, `syn`, `chrono`, `serde_derive`)만 컴파일하고 7개 테스트가 통과했음을 보여준다. `scripts/flax.py`의 `cargo_config()`를 직접 읽은 결과, `with_protoc=False`일 때는 `cargo-db-config.toml`을 쓰고 `[env] PROTOC` 블록을 넣지 않으며, `[net] offline = true`와 별도 `CARGO_HOME`/`CARGO_TARGET_DIR`(`--build-dir` 하위)을 강제한다. 이는 "protoc 없는 새 출력 경로의 오프라인 소비"라는 V2 서술과 코드 수준에서 부합한다.
3. **V3/V4 (정수 정밀도)** — `checks/json-date-smoke/fixtures/daily.json`의 값(266500/276000/264500/276000/13741073/3726945890883)과 `src/lib.rs`의 `daily_json_bytes_preserve_date_and_exact_integer_fields` 단언이 설계 V3의 기대값과 정확히 일치한다. `integers_beyond_float_precision_roundtrip_as_exact_json_numbers`는 `9007199254740993`(2^53+1, f64 정밀도 경계 초과)과 `18446744073709551615`(`u64::MAX`)를 문자열에서 `str::parse::<u64>()`로 직접 해석하고 `serde_json::to_vec`로 재직렬화한 바이트가 원래 숫자 문자열과 동일함을 검증한다. `out_of_range_and_invalid_integer_strings_are_rejected`는 2^64, 음수, 소수, 빈 문자열을 모두 거부하는지 확인한다. `json-date.log`에서 해당 세 테스트가 모두 `ok`로 통과했다.
4. **V5/V6 (날짜/시각 경계)** — `fixtures/manifest.json`의 `retrieved_at: "2026-10-02T09:09:35.581009+09:00"`을 UTC microseconds로 직접 수동 계산했다. 2024-01-01T00:00:00Z epoch(1704067200)에서 2026-10-02T00:09:35.581009Z까지 1005일(2024년 366일+2025년 365일+2026년 1~9월 274일) 경과이며, `1704067200 + 1005*86400 + 575.581009 = 1790899775.581009`초, microseconds로 `1790899775581009`가 정확히 산출된다. 이는 테스트와 verification-report가 주장하는 `1_790_899_775_581_009`와 일치하며, offset(+09:00)과 `Z` 표현이 같은 값으로 변환되는지도 `explicit_offset_and_utc_times_produce_identical_microseconds`에서 직접 확인했다. `calendar_formats_agree_and_validate_leap_days`는 `20261001`/`2026-10-01` 동일성과 `20240229`(윤일) 성공, `20230229`/`20261301`/`20260431`(존재하지 않는 날짜) 거부를 모두 포함한다. `malformed_json_and_rfc3339_are_rejected`는 잘못된 JSON, 형식이 틀린 시각, **offset이 없는** RFC3339("2026-10-02T00:09:35.581009")까지 거부 대상으로 포함하여 "명시적 offset만 허용"이라는 F2/F4 범위를 코드 수준에서 실제로 경계 검사하고 있다.
5. **V7 (최소 기능/공급 그래프)** — `features-linux.json`과 `build/json-date-verification/features.json`은 바이트 단위로 동일하며, 14개 의존성과 `serde_json=[std]`, `chrono=[alloc,std]`, `num-traits=[]` 기록이 `json-date.log`의 실제 컴파일 목록과 일치한다. `build/json-date-verification/metadata.json`에는 `wasm-bindgen`, `js-sys`, `clock`, `wasmbind` 문자열이 존재하지만, 이는 `cargo metadata`가 각 패키지의 전체 매니페스트(`chrono`의 `[features]`/`[target.'cfg(wasm32)'...]` 선언 전체)를 `packages[].dependencies`/`packages[].features`에 그대로 포함하기 때문이며, `third_party/data/chrono/Cargo.toml`을 직접 대조한 결과 해당 패키지들은 `target_arch = "wasm32"`에 한정된 선택적(optional) 의존성으로 선언되어 있을 뿐, 실제 컴파일 로그와 Cargo.lock에는 전혀 등장하지 않는다. 따라서 "시간대/wasm 패키지 없음"이라는 보고 서술은 실제 활성화된 의존성 그래프 기준으로 정확하며, metadata.json을 피상적으로 문자열 검색만 하면 오인할 수 있다는 점을 기록해 둔다(결함 아님, 독자를 위한 참고 사항).
6. **V9/기존 소스 보존** — 대화 시작 시점의 `git status` 스냅샷을 대조하면 수정된 파일은 `README.md`, `docs/rosemary-integration.md`, `specs/dependencies/freight-manifest.md`, `third_party/README.md`, `third_party/rust-registry.json`뿐이고, `checks/grpc-smoke/Cargo.lock`, `checks/postgres-smoke/Cargo.lock`, `scripts/flax.py`, `integration/rust-packages.json`, `third_party/sources.json`은 변경 목록에 없다. 이는 구현/검증 기록이 주장하는 "기존 잠금 파일 2개와 공급 도구/기존 원본 선언은 HEAD와 동일"을 독립된 자료(세션 시작 시점 git 상태)로 뒷받침한다.
7. **DB/gRPC 회귀와 최초 실패 구분** — `build/json-date-verification/grpc.log`는 `PermissionDenied, message: "Operation not permitted"`로 실패했고 `grpc-authorized.log`는 같은 테스트가 통과했다. postgres도 `20261010T002212Z-aa20cb/result.json`이 `exit_code: 1`(인증서 만료 검증까지는 성공하고 이후 실패), `20261010T002536Z-dd4c2e/result.json`이 `exit_code: 0, cleanup_ok: true, work_removed: true`로 성공했으며 `tests.log`에 단위 3개/통합 9개 `ok`가 기록되어 있다. 두 사례 모두 최초 실패 로그를 보존한 채 재실행 성공을 별도로 기록하고 있어, 설계가 요구한 "환경 제한 실패와 성공 실행의 구분, 통과로 위장하지 않음" 기준을 충족한다.
8. **보고서 구조 자동 점검** — `build/json-date-verification/report-checks.json`은 이번 4개 report에 대한 구조/완료 체크리스트/링크 검사가 전부 `PASS`(102)이고 외부 URL 3건만 `SKIP`임을 보여준다. 이 자동 점검은 "실제 승인, 설계 타당성, 내용 충실도는 판정하지 않는다"는 자체 한계를 명시하고 있으므로, 이번 코드 중심 교차 검토가 그 질적 판단을 보완한다.

## 확인하지 못한 사항

- Bash를 비롯한 실행 권한이 없어 `cargo-db test`, `verify-sources.py`, `checks/cargo` 유닛, `postgres-smoke/run.py`, `grpc-smoke` 테스트를 이 세션에서 독립적으로 재실행하지 못했다. 위 모든 판단은 기존에 보관된 로그/아티팩트 판독과 소스 직접 대조, 그리고 날짜/시각 변환의 수동 계산에 근거한다.
- `scripts/verify-sources.py`가 수행하는 체크섬 대조는 로컬 `rust-registry.json`과 `.cargo-checksum.json` 간의 내부 일치 확인이며, crates.io가 배포한 원본 체크섬과의 최초 네트워크 대조(설계의 1단계)는 이번 검토에서 재확인하지 않았다. 해당 대조는 준비 단계(`build/json-date-preparation/`)의 산출물로 서술되어 있을 뿐, 이번에 지정된 검토 대상 목록(verification-report.md 본문과 `build/json-date-verification/` 하위)에는 그 네트워크 대조의 1차 로그가 포함되어 있지 않아 직접 읽지 않았다.
- `build/json-date-verification/metadata.json`은 한 줄로 압축된 대용량 JSON이라 `Read`로 전체를 열람하지 못했고, `Grep`으로 필요한 패키지명/기능 문자열만 발췌해 대조했다. 전체 구조(resolve 노드 전체 등)를 한 번에 통람하지는 못했다.
- `/home/olbbemi/.codex/plugins/.../skills/code-development/references/ai_agents/review-execution.md`는 권한이 없어 읽지 못했다(도구 호출이 거부됨). 이 리뷰의 절차가 해당 참조 문서의 세부 지침과 정확히 일치하는지는 그 문서 없이 템플릿만으로 판단했다.
- `claude-review.json`의 `session_id`가 이 검토 세션과 일치함을 근거로 재호출된 헤드리스 CLI가 성공적으로 완료되었음은 확인했으나, 그 JSON에는 프로세스 종료 코드(`exit_code`) 필드가 없다. 호출자(Codex)가 전달한 "종료 코드 0"은 호출자의 관찰값으로 기록하며, 이 세션이 JSON 판독만으로 독립적으로 재확인한 값은 아니다.
- Walnut 프로젝트의 실제 원본 응답/manifest 파일과 `checks/json-date-smoke/fixtures/`의 내용이 정확히 "발췌"인지는 Walnut 체크아웃을 읽지 않아 교차 확인하지 않았다. Flax 쪽 코드와 수치만으로 자기 일관성은 확인했다.

## 종합 의견

지정된 범위(설계 V1-V9, 소비 코드, 공급 레지스트리, 문서, 보관된 실행 로그/아티팩트)를 코드와 로그 수준에서 직접 대조한 결과, verification-report.md의 V1-V9 판정과 실제 근거 파일 사이에 불일치나 누락을 발견하지 못했다. 정수 정밀도(2^53 경계, u64::MAX)와 날짜/시각 경계(명시적 offset 필수, 윤일, 잘못된 달력 날짜) 테스트는 경계 조건을 실제로 다루고 있으며, UTC microseconds 변환값은 독립적인 수동 계산으로도 재현되었다. 최소 기능 구성(`std`, `alloc,std`, 빈 기능)과 실제 컴파일 의존성 그래프(14개)가 선언/로그/metadata 기록 간에 서로 맞물려 있고, 기존 소스·잠금 파일 보존은 세션 시작 시점의 git 상태로도 뒷받침된다. DB/gRPC의 최초 샌드박스 실패와 재실행 성공은 통과로 위장되지 않고 구분되어 있다.

다만 이번 검토는 Bash 없이 기존 산출물을 판독하는 방식으로 수행되었다. 전달받은 옵션의 최초 CLI 호출은 네트워크(DNS) 오류로 실패했으나(`claude-review-sandbox-failure.json`), 이후 네트워크 권한을 받은 동일 옵션의 재호출이 성공했고(`claude-review.json`: `is_error:false`, `subtype:"success"`, `session_id`가 이 세션과 일치) 그 재호출이 이 검토를 수행했다고 정정한다 — 별도의 대화형 대체 세션이 아니다. 다만 그 JSON에는 프로세스 종료 코드 필드가 없어, 재호출의 "종료 코드 0"은 호출자(Codex)가 전달한 관찰값으로만 기록하며 이 세션이 독립적으로 재확인한 값은 아니다. crates.io 원본과의 최초 네트워크 대조는 여전히 재확인 범위 밖이었다. 이 종합 의견은 사용자의 최종 승인이나 QA의 주관적 판단을 대신하지 않는다.
