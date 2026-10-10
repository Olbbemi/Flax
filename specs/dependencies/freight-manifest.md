# Freight Manifest

## [Rosemary 저장 의존성 공급](rosemary-storage/)

- stages: [discussion, design, implementation, verification, qa]
- reference_reports: 없음

확정 요구사항은 [논의](rosemary-storage/discussion-report-001.md),
구조와 판정 기준은 [설계](rosemary-storage/design-report-001.md)를 따른다.
[구현](rosemary-storage/implementation-report-001.md)은 사전 실행을,
[검증](rosemary-storage/verification-report-001.md)은 최종 실행과 리뷰 대응을 기록한다.
현재 결과와 미완료 후속 작업은 [최종 QA](rosemary-storage/qa-report-001.md)에서 확인한다.

각 단계의 환경 관찰과 미확인 항목은 해당 단계 시점의 기록이다.
Git에서 제외되는 로컬 요청서와 실행 로그의 유무를 단계 완료 상태로 해석하지 않는다.
[검토자 리뷰](rosemary-storage/verification-001-review-001.md)는 당시의 원문이며,
지적의 해소 여부와 최종 호출 결과는 검증 기록을 따른다.

## [JSON/날짜 의존성 공급](json-date-dependencies/)

- stages: [discussion, design, implementation, verification, qa]
- reference_reports:
  - [Rosemary 공급 논의](rosemary-storage/discussion-report-001.md)
  - [Rosemary 공급 설계](rosemary-storage/design-report-001.md)
  - [Rosemary 공급 최종 QA](rosemary-storage/qa-report-001.md)

요청 범위, 요구사항과 제약 및 설계 인계는 [논의](json-date-dependencies/discussion-report.md)에 정리한다.
기존 Rosemary 공급의 소스 관리와 소비 경로를 참고하며, 신규 두 라이브러리의 버전과 기능은 별도로 확인한다.
고정 구성, 원본 배치와 검증/QA 계획 및 준비 근거는 [설계](json-date-dependencies/design-report.md)를 따른다.
[구현](json-date-dependencies/implementation-report.md)은 원본 반입과 독립 소비 테스트,
최종 코드 실행 및 기존 소비의 사전 실행 근거를 기록한다.
[검증](json-date-dependencies/verification-report.md)은 V1-V9의 최종 실행,
원본/잠금 파일 보존과 교차 검토 및 QA 인계를 기록한다.
[QA](json-date-dependencies/qa-report.md)는 고정 구성/소비 안내/검증 경계의 사용자 판단과
현재 공급 커밋/실제 반환 상태를 기록한다.

선행 report의 환경 관찰, 미확인 전제와 다음 단계의 미실행 표시는 해당 단계 종료 당시의 기록이다.
후속 처리 결과는 검증과 QA에서 추적하며 과거 승인을 현재 상태로 소급 변경하지 않는다.
공급 구현/검증, 사용자 QA와 문서의 후속 운영 상태 정리는 완료했다.
공급 자료의 실제 반환과 소비 프로젝트 적용은 QA에 기록한 별도 후속 작업이다.
