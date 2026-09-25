# Flax

외부 오픈소스의 소스, 버전, 패치와 빌드 구성을 한곳에서 관리하는 프로젝트다.

## 역할과 구성

- 사용할 외부 오픈소스를 가져와 기준 버전과 로컬 수정 사항을 관리한다.
- 각 구성 요소의 출처, 라이선스, 업데이트 이력과 패치를 기록한다.
- Cress, Walnut, Iris에서 사용할 의존성의 빌드 구성을 제공한다.

자체 공통 코드는 Cress, 금융 기능은 Walnut, 음성 기능은 Iris가 담당한다.
Flax는 자체 서비스 로직이나 전체 시스템의 배포 구성을 담당하지 않는다.
외부 소스는 `third_party/<분류>/<라이브러리>/`에 벤더링한다. 라이브러리별 Git
저장소나 서브모듈 대신 원본 소스 파일을 Flax에서 직접 추적한다. 소비 프로젝트는
Flax를 서브모듈로 연결한다.

분류와 관리 기준은 [외부 소스 안내](third_party/README.md), 반입한 버전과 원본
커밋은 [소스 목록](third_party/sources.json)에서 확인한다.

## 빌드와 소비 프로젝트 연결

[Cress 연결 안내](docs/cress-integration.md)에 필요한 환경, Cargo 설정과 C++ 연결
방법을 정리한다. Flax 루트에서 다음 명령으로 네이티브 도구를 빌드하고 Rust gRPC
연동을 검사한다.

```sh
python3 scripts/flax.py build-native --jobs 2
python3 scripts/flax.py cargo test --manifest-path checks/grpc-smoke/Cargo.toml --locked --offline
```

실행 스크립트는 빌드한 `protoc`, 로컬 Rust 패키지와 벤더링한 하위 의존성을 연결한다.
소비 프로젝트는 자체 `Cargo.toml`과 `Cargo.lock`을 관리하고 같은 스크립트로 Cargo를
실행한다. 생성되는 경로 설정, 캐시와 빌드 결과는 `build/`에 두며 Git에 넣지 않는다.

## 이름 선정 이유

- 원문 식물명: `Dried Flax`
- 꽃말 전체: `Utility.`
- 번역: 유용성.
- 해석: 여러 프로젝트에 필요한 외부 구성 요소를 재사용 가능한 형태로 제공한다.

저장소 이름은 `Dried Flax`에서 `Dried`를 생략한 `Flax`로 정했다.
이 근거는 `Dried Flax` 항목에 한정하며, 별도 `Flax` 항목의 꽃말과 혼용하지 않는다.
역할과의 연결은 프로젝트의 해석이다.

출처: Kate Greenaway, [Language of Flowers (1884), 꽃 이름별 목록 D](https://www.gutenberg.org/files/31591/31591-h/31591-h.htm).

## 현재 상태

Tokio 1.53.1, tonic 0.14.6, prost 0.14.4와 Protobuf 36.2의 원본 소스를 반입했다.
Protobuf용 Abseil 20250512.1과 기본 Rust gRPC 구성에 필요한 레지스트리 패키지
84개도 포함한다. Protobuf 정적 라이브러리와 `protoc`의 CMake 빌드, Rust의 오프라인
의존성 연결 및 Rust/C++ 소비 검증 구성을 제공한다. TLS와 압축 등 추가 기능 및
gRPC C++/Python 구성은 현재 프로필에 포함하지 않는다.
