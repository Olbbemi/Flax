---
status: completed
base_on: implementation-report-001.md
---

# Rosemary 저장 의존성 공급 검증

이 문서는 최종 공급 코드에 대한 실행 검증과 코드 교차 검토의 결과를 기록한다.
검토 원문에 남은 당시의 미확인 사항과 정정 경과는 아래 최종 대조 결과를 함께 읽는다.
QA와 문서 보완 및 현재 반환 상태는 [최종 QA](qa-report-001.md)를 따른다.

## 단계 결과

### 작업 모델과 승인

[논의의 작업 모델 승인](discussion-report-001.md#작업-모델과-승인)을 재사용한다.
실행 검증은 GPT-6.1 Sol / high이며 적용 확인은 사용자 확인에 따른다.
별도 코드 교차 검토는 사용자 승인에 따라 Claude Sonnet / high로 수행했다.
TLS 경계 조건과 검사 누락을 중심으로 검토하며 원본 변경은 검토 범위에 포함하지 않는다.
실제 호출 결과의 modelUsage는 `claude-sonnet-5`이며 리뷰의 모델 표기와 일치한다.
CLI 별칭 sonnet과 실제 모델 ID를 구분한다.

### 복귀 및 재검토 기록

최초 검증이며 명세 및 구현으로의 회귀는 없음.

- 회귀 계기가 된 report: 해당 없음.

### 검증 대상과 기준의 참조

[implementation-report-001.md](implementation-report-001.md)의 구현과 승인 근거를 확인했다.
대상은 Flax 소스 공급, Cargo 모드, PostgreSQL 및 잠금 소비 검사와 반환 문서다.
[설계의 검증용 항목과 판정 기준](design-report-001.md#검증용-항목과-판정-기준)을 적용한다.
요구사항을 추가하거나 이미 합의한 버전 및 기능을 변경하지 않았다.

### 검사 항목과 결과

구현 단계의 사전 실행과 별도로 최종 구현 상태에서 다음 검사를 수행했다.
코드 변경은 없으며 이번 임시 검사 자료의 오류는 아래 실패 및 재검사 기록에 구분한다.

| 설계 대상 | 실제 검사와 결과 | 판정 |
| --- | --- | --- |
| Cargo 모드 | Python 계약 검사 4개 재실행. protoc 없는 설정, 오프라인 소스와 환경, 기존 오류 및 설정 분리, 공백 경로 인자 전달 성공 | PASS |
| 원본과 목록 | upstream Git 트리 5개와 registry 171개의 파일 목록 및 SHA-256 성공. 기존 84개 메타데이터는 경로 이동을 제외하고 동일 | PASS |
| 잠금 파일과 라이선스 | gRPC의 registry 84개와 DB의 122개가 공급 목록의 버전 및 체크섬에 대응. 로컬 patch와 라이선스 기록도 존재. 기존 gRPC 잠금 파일은 구현 기록의 비교 기준 리비전과 바이트 일치 | PASS |
| 오프라인 소비 | 새 DB build-dir와 빈 Cargo 캐시에서 --locked --offline 빌드 및 검사 성공. protoc 설치 경로 없음. 별도 공백 경로 소비에서도 자체 잠금 파일로 성공 | PASS |
| 인증 | 서버 3개의 SCRAM TCP 규칙과 제한 계정의 SCRAM 저장 형식 확인. ON/OFF 질의 성공. 잘못된 비밀번호는 SqlState::INVALID_PASSWORD, 28P01 | PASS |
| TLS 정상 | 전달된 PEM 바이트와 명시적 ring 제공자를 사용. pg_stat_ssl에서 TLSv1.2와 TLSv1.3 각각 확인 | PASS |
| TLS 실패 | 정상 접속으로 준비 상태 확인 후 잘못된 CA/이름/만료 인증서 거부. TLS 미지원 서버의 Require 연결 거부. 원인을 각각 대조 | PASS |
| 암호 제공자 | ClientConfig에 ring 제공자 명시. 사용 전후 전역 기본 제공자 없음. 활성 기능 94개 패키지의 목록이 반환 파일과 동일하며 금지 TLS 패키지 없음 | PASS |
| 풀 | ON/OFF 풀 동시 보유와 각 연결의 ssl 상태 확인. 서로 다른 backend 2개를 보유한 뒤 세 번째 획득이 Wait Timeout. 반환 후 재획득 성공 | PASS |
| 트랜잭션 | 서로 다른 backend에서 commit한 행 1개, rollback한 행 0개 확인. 22012 SQL 오류 뒤 rollback 및 풀 반환 후 후속 질의 성공 | PASS |
| 데이터 | bytea 정확한 7바이트, 소수 및 u64::MAX의 NUMERIC/TEXT 왕복, 한글 문자열 및 i32::MIN 일치. BIGSERIAL 자동 번호로 조회 | PASS |
| 보조 기능 | PEM 파싱 및 잘못된 PEM 거부, abc의 SHA-256, RwLock의 복수 읽기/배타 쓰기/갱신/guard 해제 후 재취득 등 Rust 단위 검사 3개 성공 | PASS |
| 기존 소비 회귀 | 기존 cargo 명령으로 gRPC 생성 클라이언트와 서버의 교환 검사 1개 성공 | PASS |
| 정상 및 실패 정리 | 정상 실행 뒤 서버 3개 종료 및 작업 디렉토리 제거. 서버 준비 뒤 의도적인 Cargo 실패에서도 비정상 결과를 유지하고 서버 3개와 비밀 자료 제거 | PASS |
| 안내와 반환 자료 | 소비 및 설치 명령, 실제 기능 합침, 환경/결과/정리 기록과 공개 타입 경계를 대조. 문서의 범위가 실제 검사와 일치 | PASS |

#### 환경과 재현 명령

Ubuntu 24.04.4 x86_64, Python 3.12.3, Rust/Cargo 1.89.0,
PostgreSQL/psql 16.15, GCC 13.3.0, OpenSSL 3.0.13에서 수행했다.
[실제 환경](../../../build/rosemary-verification/postgres/logs/20261005T143134Z-20c7fc/environment.json)을 보관했다.

```sh
python3 -B -m unittest discover -s checks/cargo -v
python3 -B scripts/verify-sources.py
python3 -B checks/postgres-smoke/run.py --build-dir build/rosemary-verification/postgres
python3 -B scripts/flax.py cargo test --manifest-path checks/grpc-smoke/Cargo.toml --locked --offline
```

DB 실행의 Rust 단위 3개 및 통합 9개가 모두 통과했다.
DB 실행기는 새 서버, 계정과 인증서로 준비하며 비밀번호와 개인 키를 작업 디렉토리 밖에 저장하지 않는다.
TLS OFF와 ON의 풀도 같은 런타임 안에서 함께 확인했다.
100ms로 설정한 풀 대기는 Wait Timeout이며 외부 2초 제한 안에 반환됐다.
100ms의 실제 경과 시간을 별도로 측정한 결과는 아니다.

원본 및 소비 검증의 [임시 실행기 사본](../../../build/rosemary-verification/runners/flax-rosemary-verify.py)을 보관했으며,
소스 및 잠금 파일 대조 뒤 저장소 밖 임시 디렉토리에서 소비 선언과 자체 잠금 파일을 생성했다.
최종 성공 실행은 `build/rosemary-verification/independent consumer corrected/`의 빈 캐시를 사용했다.
테스트 전용 Tokio 추가 기능을 넣지 않았고,
`--locked --offline` 시험 전후 잠금 파일의 SHA-256이 동일했다.
모든 의존성의 manifest 경로가 Flax 안에 있으며 protoc 설치와 env 강제 설정은 없었다.
소비 임시 디렉토리는 시험 종료 때 제거했다.

정리 실패 조건의 [임시 실행기 사본](../../../build/rosemary-verification/runners/flax-rosemary-failure-cleanup.py)도 보관했다.
버전 조회만 실제 Cargo로 전달하고 이후 호출은 종료 73을 반환하는 임시 실행 파일을 PATH에 둔다.
검증용 서버 3개와 계정 준비가 끝난 뒤 Cargo 실패를 유발했다.
runner가 종료 1을 반환하고 로그에 server stopped가 3개 있으며,
cleanup_ok와 work_removed가 true임을 대조했다.
이 실패는 제품 결함이 아니라 설계의 실패 정리 조건을 확인하는 입력이다.

#### 실행 근거

아래 build 경로는 당시의 로컬 실행 근거이며 Git에서 제외된다.
다른 체크아웃에 로그가 없다는 사실만으로 실패나 미실행을 추론하지 않는다.
기록된 판정과 재현 명령을 구분하고 재실행 방법은 위 명령 및 소비 안내를 따른다.

- [Cargo 모드 결과](../../../build/rosemary-verification/cargo-modes.log).
- [원본 검사 결과](../../../build/rosemary-verification/source-integrity.log).
- [원본 보존 및 두 잠금 파일 대조 결과](../../../build/rosemary-verification/results.json).
- [gRPC 허용 환경 재실행 기록](../../../build/rosemary-verification/grpc-permitted-result.md).
- [DB와 기본 소비 결과](../../../build/rosemary-verification/postgres/logs/20261005T143134Z-20c7fc/tests.log).
- [DB 명령 기록](../../../build/rosemary-verification/postgres/logs/20261005T143134Z-20c7fc/commands.log).
- [최종 Linux 기능 목록](../../../build/rosemary-verification/postgres/logs/20261005T143134Z-20c7fc/features.json).
- [DB 정상 정리 결과](../../../build/rosemary-verification/postgres/logs/20261005T143134Z-20c7fc/result.json).
- [독립 소비 시험](../../../build/rosemary-verification/independent-test.log) 및 [소스 경로 metadata](../../../build/rosemary-verification/independent-metadata.log).
- [의도적 실패의 정리 결과](../../../build/rosemary-verification/controlled-failure-result.json) 및 [출력](../../../build/rosemary-verification/controlled-failure.log).

#### 실패 및 재검사 기록

gRPC의 최초 실행은 샌드박스 소켓 생성에서 PermissionDenied, Operation not permitted로 실패했다.
[최초 실패 로그](../../../build/rosemary-verification/grpc.log)를 보존했다.
같은 명령을 허용된 샌드박스 외부 환경에서 다시 실행하여 검사 1개가 성공했고 종료 0을 확인했다.
DB와 실패 정리 시험도 소켓 권한이 허용된 환경에서 실행했다.
환경 제한의 최초 실패를 통과로 바꾸지 않고 최종 허용 환경의 결과와 구분한다.

임시 검증 실행기에 다음 두 오류가 있었으며 공급 코드의 오류와 구분한다.

1. 로컬 패키지의 workspace 상속 version을 문자열로 가정하여 TypeError가 발생했다.
   상위 workspace의 실제 version을 읽도록 임시 실행기를 수정하고 대조를 완료했다.
2. 독립 소비 fixture에서 sha2의 출력 전체에 LowerHex를 요구하여 E0277이 발생했다.
   실제 공급 구성의 단위 검사처럼 바이트별 16진수로 변환하도록 fixture를 수정했다.
   [실패 로그](../../../build/rosemary-verification/independent-test-initial.log)를 보존하고
   새 빈 캐시에서 독립 소비 시험을 다시 실행해 성공했다.

Flax 코드, 요청 버전 및 명세는 수정하지 않았다.
실행 완료 후 diff의 공백 검사는 성공했다.

### 제외 및 미검증 사항

승인된 설계에 따라 제품 E2E, Rosemary Store/Track/SQL 계약,
멱등성, 성능, 종료 기아 및 lost wakeup 판단은 제외한다.
macOS Apple Silicon과 다른 OS에서 실제 빌드 및 실행은 수행하지 않았다.
대상별 소스는 두 잠금 파일의 완결성으로 확인하며 타 플랫폼 실행 성공으로 일반화하지 않는다.

필수 실행 검사 중 최종 실패, 미실행과 판정 불가는 없다.
교차 검토는 코드와 로그의 정합성을 확인했으며 검토자가 테스트를 별도로 실행하지 않았다.
큰 원본 metadata 로그 전체는 검토자의 판독 크기 제한으로 직접 읽지 못했다.
작성자는 전체 JSON을 파싱하여 126개 패키지의 경로를 확인하고
[완전한 소스 경로 투영 자료](../../../build/rosemary-verification/independent-sources.json)를 추가로 전달했다.
검증은 구현 기록의 공급 작업 트리에 대해 수행했다.
소비용 커밋과 프로젝트 간 인계 상태는 최종 QA의 인계 사항을 따른다.

### 검증 결론

설계에서 지정한 실행 검사는 모두 기준을 충족했다.
소스와 잠금 파일 보존, DB 전용 오프라인 소비, 실제 DB 정상/실패 조건 및 정리를 확인했다.
코드 교차 검토에서 기능 결함이나 설계와 모순된 결과는 발견되지 않았다.
리뷰의 실행 정보 보완과 추가 근거 대조도 완료했다.

## 인계 사항

### QA에 전달할 내용

[설계의 QA용 항목](design-report-001.md#qa용-항목과-판정-기준)에 따라
사용자가 [Rosemary 소비 안내](../../../docs/rosemary-integration.md),
소스 및 활성 기능 목록과 위 결과를 확인할 수 있도록 지원한다.
두 요청서의 공급 완료 조건과 검사 범위, 설치 및 소비 명령의 재현 가능성을 확인한다.
QA에는 검증 범위와 소비용 리비전 및 실제 인계 상태를 구분하여 전달했다.
별도 제품 동작과 타 플랫폼 시험을 QA에 추가하지 않는다.

## 완료 체크리스트

### 작업과 확인 대상

두 요청서에 대한 고정 의존성 공급과 Linux 소비 검증 결과를 확인한다.

### 단계 완료 및 이관 확인

- [x] 설계에서 정한 검증용 항목과 실제 검사 대상, 판정 기준이 연결되어 있다.
  - 확인 근거: 검증 기준 참조와 항목별 검사 표.
- [x] 최종 구현 상태의 유닛 테스트 재실행과 필요한 변경 후 재검증을 포함한 항목별 실행 결과와 판정 근거가 기록되어 있고, 실패, 미실행, 판정 불가가 통과와 구분되어 있다.
  - 확인 근거: Python 4개, Rust 3개 및 DB 9개의 실행과 임시 검사 자료 오류 및 재검사 기록.
- [x] 제외 항목에는 설계에서 합의한 제외 이유가 연결되어 있다.
  - 확인 근거: 제외 및 미검증 사항과 설계의 플랫폼 및 제품 경계.
- [x] 완료 구분이 all_passed 또는 qa_handoff이며, 선택한 이유와 근거가 기록되어 있다.
  - 확인 근거: 최종 실행 검사 모두 PASS이며 교차 검토에서도 기능 결함은 발견되지 않았다.
- [x] qa_handoff인 경우, 남은 항목을 QA에서 확인할 방법과 진행 조건을 사용자와 합의했다.
  - 확인 근거: all_passed의 실행 결과이므로 추가 미검증 이관 조건은 해당 없음.
- [x] 검증 결과 전체와 QA 진행에 영향을 주는 사항을 인계 내용에서 확인할 수 있다.
  - 확인 근거: QA 인계 및 작업 트리/리비전, 제외 범위 설명.

### 일괄 반영 기록

- B1: 단계 완료 및 이관 확인의 6개 항목 전체.
  - 반영 시각: 2026-10-06 00:06:26 (KST).
  - 근거: 사용자가 검증 결과와 리뷰 대응 의견을 기준으로 QA 진행을 승인했다.

## 사용자 승인

### 완료 구분

all_passed
설계의 필수 실행 검사가 모두 통과했고 교차 검토에서 기능 결함은 발견되지 않았다.
검토자의 확인 한계와 참고 의견은 아래에 구분한다.

### 사용자 판단

기준 선행 파일은 implementation-report-001.md다.
사용자가 검사 결과, 리뷰 의견 및 아래 작성자 판단과 QA 인계의 6개 항목을 승인했다.
검증 당시의 비밀번호 생성 조건을 유지하여 코드 변경 없이 참고 관찰로 남기는 의견을 함께 확인했다.

### 보완 요청과 처리 결과

사용자가 코드 교차 검토에 Claude Sonnet / high 사용을 승인했다.
[리뷰](verification-001-review-001.md)는 실제 코드와 로그를 대조하여 기능 결함은 없다고 판단했다.
원본 작성자는 리뷰를 수정하지 않고 항목별 실제 근거를 다시 확인했다.

#### 실행 결과와 정보 대조

Claude Code 2.1.283을 Flax에서 `claude -p`로 직접 호출했다.
사용한 모델 별칭은 sonnet, 강도는 high이며 실제 반환 모델 ID는 claude-sonnet-5다.
Read/Write 도구를 사용하고 쓰기 범위는 리뷰 파일 하나로 제한했다.

첫 호출은 샌드박스 DNS 오류 EAI_AGAIN으로 종료 1이며 리뷰가 생성되지 않았다.
허용된 샌드박스 외부 재호출은 종료 0, is_error=false와 리뷰 생성을 확인했다.
[최초 실패](../../../build/rosemary-verification/review-cli-sandbox.json)와
[성공 반환](../../../build/rosemary-verification/review-cli.json)을 보존했다.

리뷰 작성자가 직접 CLI 호출 정보와 확인 범위를 구분해 정정하고,
기존 resolver 설정 및 독립 소비의 126개 소스 경로 투영 자료를 추가 대조했다.
[보완 반환](../../../build/rosemary-verification/review-clarification-cli.json)은 종료 0,
is_error=false이며 같은 실제 모델 ID를 확인했다.
리뷰 원문의 보완 호출 진행 중 표시는 작성 시점의 한계이며 이 결과 기록이 최종 호출 결과다.
소스와 테스트 기준의 변경은 없었고 원본 metadata 전체 판독 한계는 유지했다.

#### 지적별 작성자 판단

| 리뷰 관찰 또는 한계 | 실제 대조 및 작성자 의견 | 처리 상태 |
| --- | --- | --- |
| 계정 생성 SQL의 password 이스케이프 부재 | run.py가 secrets.token_urlsafe(32)를 내부 생성한다. 실제 Python 3.12 소스가 URL-safe Base64를 사용하며 작은따옴표가 없다. 외부 비밀번호 입력은 이 실행기의 계약에 없다. 현재 동작의 결함은 아니며 코드 변경은 필요하지 않다고 판단 | 참고 관찰 유지 의견을 사용자와 확인 |
| resolver fallback 설정의 유래 미확인 | [공급 반영 전 실행기](../../../build/rosemary-verification/flax-before.py)와 검증 당시 scripts/flax.py의 동일한 설정을 직접 대조했다. 새 변경이 아니며 직접 버전과 잠금 파일은 요청 값으로 고정되어 실제 Rust/Cargo 1.89.0 컴파일에 성공 | 검토자도 추가 근거를 대조하여 기존 설정임을 확인 |
| 독립 소비 metadata의 크기 제한 | 작성자는 원본 JSON 전체를 파싱했고 모든 의존성의 실제 경로가 Flax 안임을 확인했다. 126개 전체 packages의 이름, 버전과 소스 경로를 누락 없이 투영한 자료를 전달 | 검토자도 126개 투영 자료를 확인. 원본 전체 판독 한계는 보존 |
| 훅 검사 10개를 검토하지 않음 | 공급 작업에서 훅 코드 변경은 없으며 implementation의 실행 결과만 참조한다. 검증의 관련 CLI 4개와 Rust 3개 및 통합 검사는 직접 재실행했고 리뷰에서도 코드/로그를 대조 | 이번 검증의 필수 누락이 아니므로 기존 범위 유지 |
| 검토자 테스트 재실행 없음 | 요청한 역할은 코드와 실행 근거의 교차 검토다. 본 단계의 원본 작성자가 실제 검증을 실행했고 결과를 보존 | 역할과 실제 확인 범위 유지 |

리뷰의 미확인 사항에는 checks/cargo도 함께 언급되어 있으나,
같은 리뷰의 1번 항목에서 해당 코드와 4개 실행 결과를 직접 확인했다고 기록했다.
이번 검증의 Cargo 모드 확인 근거는 실제 코드 및 로그와 리뷰 1번 항목을 따른다.
별도로 검토하지 않은 훅 검사 10개의 범위는 그대로 구분한다.

비밀번호 생성 방식을 외부 입력이나 다른 문자집합으로 바꾸는 요청이 생기면
그때 SQL 처리 조건을 다시 확인해야 한다.

### 남은 사항과 이관 조건

필수 실행 검사와 리뷰 대응의 미처리 항목은 없었다.
검증 결과를 QA로 전달했으며 이후 최종 상태는 위 QA 기록을 따른다.
