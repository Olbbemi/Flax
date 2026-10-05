# 코드 중심 교차 검증

- 검토자: Claude (Claude Code 에이전트)
- 모델명/버전: Sonnet 5 (모델 ID: claude-sonnet-5). 세션 환경 정보로 직접 확인한 값이며 CLI 버전 번호가 아닙니다.
- 검토 대상: verification-report-001.md (기준 선행 report: discussion-report-001.md, design-report-001.md, implementation-report-001.md)

## 실행 대상과 근거

(2026-10-05 보완: 아래 내용은 최초 작성 시 호출 주체를 잘못 서술한 부분을 정정하고, 근거를 발신 주체별로 구분해 보강한 것입니다.)

- 호출 주체: 이 리뷰는 사용자가 현재 세션에서 직접 지시한 것이 아니라, 상위 Codex가 Flax를 작업 디렉토리로 사용해 `claude -p` 명령으로 직접 호출한 결과입니다. 사용자 승인은 Codex 대화에서 Sonnet / high 사용에 대해 받았다고 전달받았습니다.
- 실제 CLI 호출 경과(호출자가 확인해 전달한 근거): 첫 번째 호출은 샌드박스 DNS 오류(EAI_AGAIN)로 종료 코드 1을 반환해 검토를 수행하지 못했습니다. 두 번째 호출은 `require_escalated`로 재시도되어 종료 코드 0을 반환했고, `is_error: false`와 이 리뷰 파일의 작성을 호출자가 직접 확인했습니다. 전달받은 호출 옵션은 `--model sonnet --effort high --output-format json --no-session-persistence --disable-slash-commands --permission-mode dontAsk --tools Read,Write`이며, 허용된 쓰기는 이 리뷰 파일 1건뿐이었습니다. 이 문단 전체는 호출자가 확인해 전달한 근거이며, 검토자가 별도 도구로 재현하거나 재검증한 사실이 아닙니다.
- 검토자가 직접 읽어 확인한 근거: `build/rosemary-verification/review-cli.json`을 직접 읽었습니다. 두 번째 호출의 기록으로 `is_error: false`, `subtype: "success"`, `terminal_reason: "completed"`를 담고 있고, `modelUsage`에 `claude-sonnet-5` 모델 사용량이 기록되어 있으며, `result` 필드에 이 리뷰 파일(`specs/dependencies/rosemary-storage/verification-001-review-001.md`)을 작성했다는 서술이 있습니다. 이 JSON에는 OS 프로세스 종료 코드 필드가 따로 없으므로, "두 번째 호출의 종료 코드 0"이라는 값 자체는 검토자가 이 파일에서 직접 읽어 확인한 사실이 아니라 호출자가 확인해 전달한 근거로 구분해 기록합니다.
- 최초 작성 시의 오류와 정정: 최초 작성 시 이 절에 "사용자가 현재 Claude Code 세션에서 직접 검토를 지시했습니다"와 "이 검토는 별도 프로세스로 기동된 CLI 호출이 아니라 현재 세션 내부에서 수행되었다"고 적었으나, 이는 상위 호출 관점의 실행 사실과 맞지 않는 서술이었으므로 위 내용으로 정정합니다. 이 리뷰는 현재 세션 내부 검토가 아니라, 상위 Codex가 기동한 별도 `claude -p` CLI 호출(두 번째 시도)의 결과물입니다.
- 검토 범위와 쓰기 범위: 검토자는 Read 도구로 아래 "검토 범위와 기준"에 열거한 report, 코드, 설정, 로그 파일을 모두 직접 읽고 대조했습니다. 테스트나 스크립트를 재실행하지 않았으며, 다른 에이전트나 스킬을 호출하지 않았습니다. 쓰기는 이 리뷰 파일 1건만 Write 도구로 수행했습니다.
- 이번 보완 호출: 이번 보완 호출도 전달받은 바로는 같은 모델(Sonnet 5)과 같은 강도(high)로 호출되었습니다. 다만 이번 보완 호출 자체의 종료 코드와 `is_error` 값은 호출이 진행 중이므로 이 문서에서 단정하지 않습니다.

## 검토 범위와 기준

사용자가 지정한 범위는 verification-report-001.md를 discussion-report-001.md, design-report-001.md, implementation-report-001.md 3개 선행 report를 기준으로 코드·설정·로그와 대조하는 코드 중심 교차 검토입니다. 판정 기준은 [design-report-001.md의 검증용 항목과 판정 기준](design-report-001.md#검증용-항목과-판정-기준) 표를 사용했습니다.

직접 읽은 대상은 다음과 같습니다.

- 코드/설정: `scripts/flax.py`, `checks/cargo/test_cargo_modes.py`, `checks/postgres-smoke/Cargo.toml`, `checks/postgres-smoke/Cargo.lock`, `checks/postgres-smoke/run.py`, `checks/postgres-smoke/src/lib.rs`, `checks/postgres-smoke/tests/database.rs`, `checks/postgres-smoke/features-linux.json`, `checks/postgres-smoke/fixtures/ca.pem`, `docs/rosemary-integration.md`, `third_party/README.md`, `third_party/rust-registry.json`(전체, 분할 오프셋으로 끝까지 확인).
- 요청서: `data/todo/20261003-rosemary-postgresql-dependencies.md`, `data/todo/20261005-rosemary-parking-lot-dependency.md`.
- 실행 근거: `build/rosemary-verification/cargo-modes.log`, `source-integrity.log`, `results.json`, `grpc-permitted-result.md`, `grpc.log`, `independent-test.log`, `independent-test-initial.log`, `controlled-failure.log`, `controlled-failure-result.json`, `controlled-failure/logs/20261005T143522Z-54b2f4/commands.log`, `postgres/logs/20261005T143134Z-20c7fc/{tests.log,result.json,environment.json,features.json}`.
- 임시 실행기 사본: `build/rosemary-verification/runners/flax-rosemary-verify.py`, `build/rosemary-verification/runners/flax-rosemary-failure-cleanup.py`.
- (2026-10-05 보완) `build/rosemary-verification/review-cli.json`, `build/rosemary-verification/flax-before.py`, `build/rosemary-verification/independent-sources.json`.

요청받은 항목별 집중 확인 대상은 요구사항·구현 일치, TLS 정상/실패 조건, SCRAM 인증, 명시적 ring 제공자, 풀/트랜잭션, 데이터 왕복, 소스·잠금 파일 보존, protoc 없는 오프라인 소비, 성공/실패 정리, 그리고 기록이 실제 코드보다 넓게 주장하는 부분입니다.

`build/rosemary-verification/independent-metadata.log`는 613.1KB로 도구의 1회 최대 판독 크기(256KB)를 넘어 전체를 읽지 못했으며, 대신 이를 생성한 `flax-rosemary-verify.py`의 해당 검증 로직과 `results.json`의 `independent-metadata: PASS` 기록으로 대조했습니다. 이 부분은 "확인하지 못한 사항"에 별도로 남깁니다.

## 검토 결과

실제 확인한 범위에서, verification-report-001.md의 각 항목별 결과 표와 재현 명령은 아래 코드/로그와 대조했을 때 일관되게 뒷받침되었습니다. 발견한 사항을 항목별로 기록합니다.

### 1. Cargo 모드와 protoc 없는 소비 (일치)

- 대상: `scripts/flax.py:18-69`, `checks/cargo/test_cargo_modes.py`, `build/rosemary-verification/cargo-modes.log`.
- `cargo_config(build, with_protoc=False)`가 `cargo-db-config.toml`을 만들며 `[env]` 블록과 PROTOC/PROTOC_INCLUDE 강제 설정을 생성하지 않는 코드를 확인했습니다. `with_protoc=True`(기존 `cargo`)는 protoc 파일 부재 시 `ValueError('Build protoc first...')`를 그대로 던집니다.
- `test_cargo_modes.py`의 4개 테스트(오프라인 설정, 기존 protoc 필수, 두 설정 파일 비간섭, 공백 경로 CLI 전달)가 `cargo-modes.log`에서 모두 `ok`로 기록되어 있어 verification-report-001.md의 "Cargo 모드: PASS" 행과 일치합니다.
- `checks/postgres-smoke/run.py:224-235`는 `FLAX_PG_*` 환경과 함께 `PROTOC`, `PROTOC_INCLUDE`를 일부러 존재하지 않는 경로(`protoc-must-not-be-used`)로 덮어써서 전달합니다. 이는 설계의 "protoc 없는 DB 소비" 요구를 보고서가 서술한 것보다 더 적극적으로 검증하는 코드이며, 기록이 코드보다 넓게 주장하는 사례는 아닙니다.

### 2. 소스/잠금 파일 보존과 레지스트리 목록 (일치)

- 대상: `third_party/rust-registry.json`, `third_party/README.md`, `build/rosemary-verification/source-integrity.log`, `results.json`, `runners/flax-rosemary-verify.py:34-81`.
- `rust-registry.json`은 최상위에 `"lockfile": "checks/grpc-smoke/Cargo.lock"`(3번째 줄)과, 배열 종료 후 `"lockfiles": ["checks/grpc-smoke/Cargo.lock", "checks/postgres-smoke/Cargo.lock"]`(2058-2061번째 줄)를 함께 가지고 있어, design-report-001.md와 third_party/README.md가 서술한 "기존 `lockfile` 필드 유지 + 신규 `lockfiles` 필드 추가" 요구와 일치합니다.
- `getrandom`은 `third_party/core/getrandom/0.2`와 `third_party/core/getrandom/0.4`로 계열 분리 경로에 존재합니다(534-556번째 줄). git status에 보이는 다수의 `D third_party/core/getrandom/...` 항목은 버전 없는 기존 경로가 버전별 하위 경로로 이동한 결과로 해석되며, 설계의 "비호환 계열 공존" 결정과 일치합니다.
- `source-integrity.log`는 "OK 171 registry packages: file lists and SHA-256 checksums"를 출력했고, `results.json`은 `preserved_registry_packages: 84`, `registry_lock_packages: {grpc-smoke: 84, postgres-smoke: 122}`를 기록합니다. `checks/postgres-smoke/Cargo.lock`을 직접 센 결과 `[[package]]` 항목 126개 중 `source` 필드가 없는 4개(`flax-postgres-smoke`, `tokio`, `tokio-macros`, `tokio-util`, 모두 로컬 patch 경로)를 제외하면 122개로, `results.json`의 수치와 일치합니다.
- `flax-rosemary-verify.py`는 git `HEAD`의 `third_party/rust-registry.json`과 현재本을 대조해 `path`를 제외한 모든 필드가 동일함을 `assert`하고, `checks/grpc-smoke/Cargo.lock`, `third_party/sources.json`, `integration/rust-packages.json`의 바이트 동일성도 함께 검사합니다. verification-report-001.md 본문은 "기존 gRPC 잠금 파일은 HEAD와 바이트 일치"만 서술하고 `sources.json`, `rust-packages.json` 비교는 언급하지 않았는데, 이는 실제 코드가 보고서 서술보다 더 넓게 검사하는 경우이며 보고서가 코드보다 넓게 주장하는 사례는 아닙니다.

### 3. 패키지 분류 배치 (일치)

- 대상: `third_party/rust-registry.json`의 `path` 필드, design-report-001.md의 "DB 드라이버 및 PostgreSQL 표현 패키지는 data, TLS 연결은 networking, 일반 잠금·풀·암호 기반 패키지는 core" 결정.
- 직접 대조한 결과: `deadpool`→core, `deadpool-postgres`→data, `ring`→core, `sha2`→core, `parking_lot`→core, `tokio-postgres`→data, `postgres-protocol`/`postgres-types`→data, `rustls`/`rustls-pki-types`/`rustls-webpki`→networking, `tokio-postgres-rustls`/`tokio-rustls`→networking, `x509-cert`→networking. 설계 결정표와 전부 일치합니다.

### 4. 활성 기능 목록과 금지 패키지 (일치)

- 대상: `checks/postgres-smoke/features-linux.json`, `build/rosemary-verification/postgres/logs/20261005T143134Z-20c7fc/features.json`, `checks/postgres-smoke/run.py:250-259`.
- 두 파일의 내용을 직접 비교한 결과 바이트 수준으로 동일하며, 패키지 수를 직접 센 결과 94개로 verification-report-001.md의 "활성 기능 94개 패키지의 목록이 반환 파일과 동일" 주장과 일치합니다.
- `run.py`의 `forbidden = {'aws-lc-rs', 'aws-lc-sys', 'rustls-native-certs', 'webpki-roots'}` 검사 로직이 존재하며, 실제 94개 목록에도 해당 패키지가 없습니다. "금지 TLS 패키지 없음" 주장과 일치합니다.

### 5. TLS 정상/실패 조건과 명시적 ring 제공자 (일치)

- 대상: `checks/postgres-smoke/tests/database.rs:36-59, 177-274`.
- `connector()`가 `ClientConfig::builder_with_provider(Arc::new(rustls::crypto::ring::default_provider()))`를 사용하고, `tls12_and_tls13_verify_supplied_ca_and_leave_global_provider_unset` 테스트가 호출 전후 `CryptoProvider::get_default().is_none()`을 확인합니다. design-report-001.md의 "Store별 ring 제공자를 전달한 builder 사용, 전역 기본 제공자 미설치" 요구와 일치합니다.
- TLS 실패 4종(`wrong_ca_is_rejected_as_an_untrusted_issuer`, `wrong_target_name_is_rejected_on_the_same_reachable_server`, `expired_certificate_is_rejected_while_plain_scram_still_works`, `tls_required_does_not_fall_back_on_a_plain_only_server`)이 모두 `rejected()` 헬퍼로 연결 실패만 허용하고, `failure_reason()`으로 원인 문자열(`unknownissuer`, `notvalidforname`, `expired`, `doesnotsupporttls`)을 구분합니다. OFF로 재접속하는 코드 경로는 없습니다. design-report-001.md의 "TLS 실패" 판정 기준 및 "TLS ON 실패 시 OFF로 재접속하지 않음" 제약과 일치합니다.
- `tests.log`(20261005T143134Z-20c7fc)에 9개 통합 테스트 전부 `ok`로 기록되어 있어, verification-report-001.md의 "DB 실행의 ... 통합 9개가 모두 통과했다" 주장과 일치합니다(함수 개수를 직접 세어 9개임을 확인했습니다).

### 6. SCRAM 인증 (일치)

- 대상: `checks/postgres-smoke/run.py:149-168`(`accounts()`), `tests/database.rs:144-175`(`scram_authenticates_...`).
- `accounts()`는 `pg_authid.rolpassword LIKE 'SCRAM-SHA-256$%'`와 `pg_hba_file_rules.auth_method='scram-sha-256'`을 모두 검사하며, 3개 클러스터 각각에서 실행됩니다. `controlled-failure/logs/20261005T143522Z-54b2f4/commands.log`에서도 normal/expired/plain 3개 클러스터 모두 `t|t` / `t` 응답을 직접 확인했습니다.
- Rust 테스트는 OFF/ON 각각 정상 인증 후 `wrong_off`/`wrong_on`에 대해 `SqlState::INVALID_PASSWORD`를 확인합니다. SQLSTATE `28P01`은 PostgreSQL의 `invalid_password` 코드와 일치하는 값입니다.

### 7. 풀과 트랜잭션 (일치)

- 대상: `tests/database.rs:116-141, 276-392`.
- `pool()`은 `max_size(2)`, `wait_timeout(100ms)`를 명시적으로 설정합니다. `encrypted_and_plain_pools_coexist_...` 테스트는 ON/OFF 풀을 동시에 보유하고, `on` 풀에서 2개를 채운 뒤 3번째 획득을 외부 `timeout(2s)`로 감싸 `PoolError::Timeout(TimeoutType::Wait)`를 확인하고, `drop` 후 재획득 성공을 확인합니다. verification-report-001.md의 "100ms로 설정한 풀 대기는 Wait Timeout이며 외부 2초 제한 안에 반환됐다. 100ms의 실제 경과 시간을 별도로 측정한 결과는 아니다"라는 서술은 테스트 코드의 실제 한계(설정값만 지정했을 뿐 실측 지연 시간 검증은 없음)를 정확하게 반영하고 있습니다.
- `commit_rollback_and_sql_error_cleanup_...` 테스트는 서로 다른 backend pid를 가진 두 연결로 commit/rollback을 각각 확인하고, `SELECT 1/0`의 `SqlState::DIVISION_BY_ZERO` 발생 후 `rollback`과 `drop(first)` 뒤 새 연결로 후속 질의 성공을 확인합니다. 설계의 "SQL 오류가 난 트랜잭션은 rollback 또는 연결 폐기로 정리한 뒤 후속 질의를 확인" 요구와 일치합니다.

### 8. 데이터 왕복 (일치)

- 대상: `tests/database.rs:394-436`.
- `bytes = vec![0,1,127,128,255,0,42]`로 정확히 7바이트이며, `text = "Rosemary 저장 검증"`(한글 포함), `integer = i32::MIN`, 소수(`1234567890.123...`)와 `u64::MAX`를 `TEXT`로 왕복시킵니다. `BIGSERIAL` 자동 번호(`id BIGSERIAL PRIMARY KEY`)로 재조회합니다. verification-report-001.md의 데이터 행 서술과 정확히 일치합니다.

### 9. 오프라인 소비와 저장소 밖 독립 소비 (일치)

- 대상: `build/rosemary-verification/runners/flax-rosemary-verify.py:83-114`, `independent-test.log`, `independent-test-initial.log`, `results.json`.
- 임시 디렉토리(`/tmp/flax rosemary verify consumer ...`)에 `checks/postgres-smoke/Cargo.toml`에서 `[dev-dependencies]` 이전 부분만 떼어낸 독립 매니페스트를 생성하고, `cargo-db generate-lockfile` 이후 `cargo-db test`를 실행하며 잠금 파일 SHA-256이 실행 전후 동일함을 확인합니다. `metadata`로 모든 패키지의 `manifest_path`가 Flax 루트 하위임을 검사합니다.
- `independent-test-initial.log`에서 `sha2`의 `LowerHex` 미구현으로 인한 `E0277` 최초 실패를, `independent-test.log`에서 수정 후 성공(Exit: 0)을 각각 직접 확인했습니다. verification-report-001.md의 "실패 및 재검사 기록" 서술과 일치합니다.
- `build / 'cargo-db-config.toml'`을 읽어 `'env' not in config and config['net']['offline']`를 검사하는 코드가 있어 "protoc 설치와 env 강제 설정은 없었다" 주장을 코드 수준에서 뒷받침합니다.
- (2026-10-05 보완) `build/rosemary-verification/independent-sources.json`을 직접 읽었습니다. 이 파일은 원본 `independent-metadata.log`의 `packages` 배열 전체를 이름/버전/소스 경로만 추출해 JSON으로 투영했다고 전달받은 축약본이며, 나열된 항목을 직접 센 결과 126개로 파일이 명시한 `package_count: 126`과 일치합니다. 소비자 자신(`independent-rosemary-consumer`, `consumer: true`)을 제외한 나머지 125개 패키지 전부의 `canonical_manifest_path`가 `third_party/` 하위 경로를 가리키고 있어, 기존에 `flax-rosemary-verify.py`의 검증 로직만으로 추정했던 "모든 패키지의 manifest_path가 Flax 루트 하위"라는 주장을 이름/버전/경로 수준에서 보강합니다. 다만 이 파일은 호출자가 원본 613.1KB 로그를 가공해 별도로 생성해 전달한 투영본이며, 검토자가 원본 로그 전체를 직접 읽은 것은 아닙니다. 원본 로그에 있을 수 있는 이름/버전/경로 이외의 다른 내용(의존성 그래프, feature 플래그 등 `cargo metadata`의 나머지 필드)은 여전히 직접 확인하지 못했습니다.

### 10. 성공/실패 정리 (일치)

- 대상: `checks/postgres-smoke/run.py:260-286`, `runners/flax-rosemary-failure-cleanup.py`, `controlled-failure-result.json`, `controlled-failure/logs/20261005T143522Z-54b2f4/commands.log`.
- 정상 실행은 `logs/20261005T143134Z-20c7fc/result.json`에서 `exit_code: 0, cleanup_ok: true, work_removed: true`를 확인했습니다.
- 의도적 실패 시나리오는 `PATH`에 `--version`만 실제 cargo로 전달하고 그 외 모든 호출에 종료 73을 반환하는 가짜 `cargo`를 배치합니다. `commands.log`에서 `Controlled verification failure after cluster preparation` / `Exit: 73` 직후 normal/expired/plain 3개 클러스터가 역순으로 모두 `pg_ctl ... stop` → `server stopped`로 종료되는 것을 직접 확인했습니다(`server stopped` 문자열 3회, `failure-cleanup.py`의 `assert`와 일치). `controlled-failure-result.json`의 `expected_exit_code: 1, all_three_servers_stopped: true, work_removed: true`와 일치합니다.
- `commands.log` 전체를 확인한 결과 `CREATE ROLE ... PASSWORD`의 실제 값이나 개인 키 PEM 블록이 로그에 출력되지 않았습니다. 계정 생성 SQL은 `psql` 표준입력으로 전달되고 `execution.run()`은 표준입력 내용을 로그에 기록하지 않는 구조이므로, "비밀번호와 개인 키를 로그에 남기지 않는다"는 주장이 코드 구조상 뒷받침됩니다.

### 11. 경미한 관찰 사항 (결함은 아니나 기록)

- 대상: `checks/postgres-smoke/run.py:149-161`(`Cluster.accounts`).
- `postgresql.conf` 설정값에는 `configuration_value()`로 싱글쿼트를 이스케이프하지만, `CREATE ROLE flax_consumer LOGIN PASSWORD '{password}' ...` SQL 문자열에는 동일한 이스케이프를 적용하지 않습니다. 현재는 `password = secrets.token_urlsafe(32)`가 생성하는 문자집합(영숫자, `-`, `_`)에 싱글쿼트가 포함되지 않아 실질적인 SQL 삽입 위험은 없습니다. 다만 이 안전성은 토큰 생성 함수의 문자집합에 암묵적으로 의존하고 있으며, discussion/design/verification 어느 report에도 이 의존성이 명시되어 있지 않습니다. 기능 결함은 아니지만, 비밀번호 생성 방식이 바뀔 경우를 대비한 명시적 이스케이프나 문서화가 없다는 점을 기록해 둡니다.

## 확인하지 못한 사항

- `build/rosemary-verification/independent-metadata.log`(613.1KB)는 Read 도구의 1회 최대 판독 크기(256KB)를 초과하여 전체 내용을 직접 읽지 못했습니다. 대신 이를 생성한 `flax-rosemary-verify.py`의 `cargo metadata` 처리 로직(모든 패키지의 `manifest_path`가 Flax 루트 하위인지 검사)과 `results.json`의 `independent-metadata: PASS` 기록으로 대조했습니다. 로그 원문의 세부 내용 자체를 직접 확인하지는 못했습니다. (2026-10-05 보완) 이후 `build/rosemary-verification/independent-sources.json`(원본 로그의 `packages` 배열을 이름/버전/소스 경로만 추출해 투영한 축약본, 126개 패키지 전체 투영)을 직접 읽어 이름/버전/경로 수준의 범위를 보강했습니다. 자세한 내용은 위 "9. 오프라인 소비와 저장소 밖 독립 소비" 항목의 보완 기록을 참고하십시오. 다만 이 축약본을 읽은 것으로 원본 로그 전체를 직접 읽은 것을 대신할 수는 없으며, 이름/버전/경로 이외의 원본 필드는 여전히 미확인 상태로 남습니다.
- `scripts/flax.py`의 `cargo_config()`에 있는 `[resolver] incompatible-rust-versions = "fallback"` 설정이 이번 Rosemary 작업으로 새로 추가된 것인지, 그 이전부터 존재했던 것인지는 git 이력 조회 도구(Bash/grep 등)가 주어지지 않아 확인하지 못했습니다. 이 설정이 Rust/Cargo 1.89.0에서 선언된 rust-version보다 높은 패키지의 해석 실패를 조용히 완화시킬 수 있다는 점에서, discussion-report-001.md의 "고정 버전 또는 Rust/Cargo 1.89.0에서 요청 구성이 성립하지 않으면 실패 근거와 변경안을 제시한다"는 제약과의 관계를 판단할 근거가 부족합니다. 이번 검증에서 직접 실패가 관찰되지는 않았으므로 현재 결과를 무효화하는 사안은 아니나, 기존 코드와의 관계를 단정하지 않습니다. (2026-10-05 보완) `build/rosemary-verification/flax-before.py`(호출자가 `git show HEAD:scripts/flax.py`로 얻었다고 전달한 기존 코드)와 현재 `scripts/flax.py`를 직접 대조했습니다. 두 파일 모두 `cargo_config()` 내부 동일한 위치에 `'[resolver]', 'incompatible-rust-versions = "fallback"',` 줄을 포함하고 있어, 이 설정은 이번 Rosemary 작업으로 새로 추가된 것이 아니라 HEAD 시점(이번 작업 이전)부터 이미 존재했던 설정임을 확인했습니다. 다만 `flax-before.py`가 실제로 HEAD 버전과 일치한다는 전제 자체는 호출자가 전달한 정보에 의존하며, 검토자가 git 이력 조회 도구로 직접 재현한 것은 아닙니다. 이 확인으로 유래 자체에 대한 의문은 해소되었으나, HEAD 이전 더 오래된 시점에 이 설정이 어떤 근거로 도입되었는지는 범위 밖입니다.
- `checks/cargo`, `checks/hooks` 등 이번 작업과 직접 관련 없는 기존 회귀 테스트(구현 기록이 언급한 "기존 공용 경로 및 훅 단위 검사 10개")는 사용자가 지정한 검토 대상 목록에 포함되지 않아 별도로 확인하지 않았습니다.
- 이 검토는 사용자 지시에 따라 어떤 테스트나 스크립트도 재실행하지 않았습니다. 따라서 로그에 기록된 결과가 현재 작업 트리 상태에서도 동일하게 재현되는지는 직접 재검증하지 않았고, 로그와 코드의 정합성만 대조했습니다. macOS Apple Silicon 등 미검증 플랫폼에 대한 판단은 범위 밖이며 별도로 확인하지 않았습니다.

## 종합 의견

확인한 범위에서, verification-report-001.md의 항목별 결과 표, 재현 명령, 실행 근거 경로는 실제 코드(`scripts/flax.py`, `checks/postgres-smoke/*`, `third_party/rust-registry.json` 등)와 실행 로그(`build/rosemary-verification/**`)로 뒷받침되며, 서로 모순되는 서술이나 실제 코드보다 넓게 주장하는 부분은 발견하지 못했습니다. TLS 정상/실패 조건, SCRAM 인증, 명시적 ring 제공자, 풀/트랜잭션, 데이터 왕복, 소스·잠금 파일 보존, protoc 없는 오프라인 소비, 성공/실패 정리 항목 모두 design-report-001.md의 판정 기준에 1:1로 대응하는 코드와 로그를 확인했습니다. 레지스트리 패키지 수(171/122/94)와 분류 배치도 직접 재계산하여 보고서의 수치와 일치함을 확인했습니다.

경미한 관찰로 기록한 SQL 비밀번호 이스케이프 부재는 현재 문자집합상 실질적 위험은 없으나 암묵적 의존이므로 참고용으로 남깁니다. `resolver.incompatible-rust-versions = "fallback"` 설정은 2026-10-05 보완 확인으로 이번 작업 이전부터 존재했던 설정임이 확인되었으므로, 더 이상 유래가 불명확한 "확인하지 못한 사항"은 아닙니다. 다만 그 확인은 호출자가 전달한 HEAD 스냅샷(`flax-before.py`)에 의존하며, 검토자가 git 이력 조회 도구로 직접 재현한 것은 아니라는 한계를 함께 기록해 둡니다.

이 종합 의견은 확인한 범위에 대한 검토자의 판단이며, 최종 사용자 승인이나 QA의 주관적 판단을 대신하지 않습니다.
