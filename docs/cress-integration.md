# Cress에서 Flax 사용

Flax를 서브모듈로 가져온 후 로컬 Protobuf 도구를 빌드하고, Flax의 Cargo 실행
스크립트로 Rust 프로젝트를 빌드한다. 이 문서의 `deps/flax`는 소비 프로젝트가
선택할 수 있는 배치 예시다. 다른 경로에서도 스크립트가 자신의 위치를 기준으로
소스를 찾는다.

## 준비 환경과 제공 범위

- Linux, Python 3, CMake 3.16 이상, C++17을 지원하는 C/C++ 컴파일러와 Make.
- 검증 기준 Rust/Cargo 1.89.0. 도구 체인은 시스템에 설치하며 Flax에 벤더링하지 않는다.
- 기본 Rust gRPC 클라이언트/서버와 Protobuf 코드 생성에 필요한 소스를 제공한다.
- 네 원본 저장소에 더해 Abseil 20250512.1과 Cargo 하위 패키지를 벤더링한다.
  [원본 소스 목록](../third_party/sources.json), [Cargo 패키지 목록](../third_party/rust-registry.json),
  [검증 구성의 잠금 파일](../checks/grpc-smoke/Cargo.lock)로 버전과 출처를 확인한다.
- 현재 프로필은 로컬 HTTP/2 연결을 검증하며 TLS, 압축, 다른 대상 OS와 크로스 컴파일은
  검증 범위에 포함하지 않는다. 해당 기능을 추가하면 필요한 의존성을 추가하고 다시 검증한다.
- C++에서는 Protobuf 라이브러리와 `protoc`를 제공한다. gRPC C++과 Python용 gRPC
  패키지는 아직 반입하지 않았다.

## 1. 네이티브 도구 빌드

Cress 루트에서 실행한다.

```sh
python3 deps/flax/scripts/flax.py build-native --jobs 2
```

출력 위치는 Flax의 `build/` 아래다.

| 경로 | 내용 |
| --- | --- |
| `build/native/` | CMake 빌드 디렉토리 |
| `build/install/bin/protoc` | 호스트에서 실행하는 Protobuf 컴파일러 |
| `build/install/include/` | Protobuf와 Abseil 등의 헤더 및 표준 `.proto` |
| `build/install/lib/` | 정적 라이브러리와 CMake 패키지 설정 |

네이티브 빌드는 Flax에 포함된 Abseil과 Protobuf만 사용하며 의존성을 다운로드하지 않는다.
선택 기능인 zlib 압축과 원본 테스트/예제는 비활성화한다. 빌드 결과물은 Git에 넣지 않는다.

출력 위치를 바꾸려면 이후 명령에서도 같은 `--build-dir`을 지정한다.

```sh
python3 deps/flax/scripts/flax.py --build-dir /absolute/output/path build-native --jobs 2
```

## 2. Cress의 Cargo 의존성 선언

Cress의 패키지 `Cargo.toml`에 실제 사용하는 항목을 선언한다. 아래는 서버와
클라이언트 코드 생성을 모두 사용하는 최소 구성이다.

```toml
[dependencies]
tokio = { version = "=1.53.1", features = ["macros", "rt-multi-thread", "net", "sync", "time"] }
tonic = "=0.14.6"
tonic-prost = "=0.14.6"
prost = "=0.14.4"

[build-dependencies]
tonic-prost-build = "=0.14.6"
```

`build.rs`에서는 Cress가 소유하거나 전달받은 `.proto`를 지정한다.

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("cargo:rerun-if-changed=proto/service.proto");
    println!("cargo:rerun-if-env-changed=PROTOC");
    tonic_prost_build::compile_protos("proto/service.proto")?;
    Ok(())
}
```

실제 서비스 정의는 이 예시와 별도로 담당 프로젝트에서 관리한다. Flax의 검증용
`echo.proto`는 서비스 계약으로 사용하지 않는다.

## 3. Cargo 실행

처음 연결할 때 소비 프로젝트 루트에서 실행한다.

```sh
python3 deps/flax/scripts/flax.py cargo generate-lockfile --offline
python3 deps/flax/scripts/flax.py cargo build --locked --offline
```

이후에는 소비 프로젝트의 `Cargo.lock`도 버전 관리하고 `--locked`를 사용한다.
기존 의존성이 있는 프로젝트에서는 기존 잠금 파일과 Flax가 제공하는 버전의 충돌을
먼저 확인한다. 새 기능 때문에 목록에 없는 패키지가 필요하면 오프라인 해결이 실패하며,
Flax에 해당 소스와 버전을 추가한 후 다시 빌드한다.

실행 스크립트는 다음을 적용한다.

- [rust-packages.json](../integration/rust-packages.json)에 지정한 패키지를 로컬 경로로
  재정의한다. tonic이 참조하는 prost와 Tokio도 동일한 소스를 사용한다.
- 나머지 crates.io 의존성도 벤더링된 디렉토리로 대체하고 네트워크 접근을 끈다.
- `PROTOC`와 `PROTOC_INCLUDE`를 Flax 빌드 결과에 연결한다.
- `CARGO_HOME`과 `CARGO_TARGET_DIR`를 Flax의 `build/` 안에 지정한다.
  사용자 홈의 Cargo 설정과 캐시에 의존하지 않는다.

생성되는 `build/cargo-config.toml`에는 현재 체크아웃의 절대 경로가 들어간다.
커밋하지 않으며, 실행할 때 다시 생성하므로 체크아웃 경로를 바꿔도 사용할 수 있다.
Cargo는 하위 서브모듈의 설정을 자동으로 상속하지 않으므로 일반 `cargo build` 대신
위 스크립트를 통해 실행해야 한다. 소비 프로젝트 자체에서 같은 `[patch]`와
source replacement를 직접 구성해도 되지만 두 방식의 설정이 충돌하지 않게 관리한다.

## 4. C++ 연결

설치된 CMake 패키지를 사용한다.

```cmake
find_package(Protobuf CONFIG REQUIRED)
target_link_libraries(my_target PRIVATE protobuf::libprotobuf)
```

소비 프로젝트의 CMake 구성 시 `CMAKE_PREFIX_PATH`에 Flax의
`build/install` 절대 경로를 전달한다. 코드 생성은 설치된 `protobuf_generate()`와
`protobuf::protoc` 타깃으로 연결할 수 있다.

## Flax 자체 검증

Flax 루트에서 실행한다.

```sh
python3 scripts/verify-sources.py
python3 scripts/flax.py build-native --jobs 2
python3 scripts/flax.py cargo test --manifest-path checks/grpc-smoke/Cargo.toml --locked --offline
cmake -S checks/protobuf-smoke -B build/protobuf-smoke -DCMAKE_PREFIX_PATH="$PWD/build/install"
cmake --build build/protobuf-smoke --parallel 2
ctest --test-dir build/protobuf-smoke --output-on-failure
```

Rust 검증은 실제 `protoc`로 생성한 메시지 및 서비스 코드를 컴파일한 뒤 임의의
로컬 포트에서 gRPC 클라이언트와 서버를 실행한다. 문자열과 바이너리 데이터의 왕복,
잘못된 요청의 상태 코드 전달, 서버 종료를 확인한다. C++ 검증은 설치된 패키지만
찾아 코드 생성, 링크와 직렬화 왕복을 확인한다.

### 확인한 결과

2026-09-25, Linux 환경의 Rust/Cargo 1.89.0, CMake 3.25.3, GCC C++ 11.5.0에서 확인했다.

| 검사 | 결과 |
| --- | --- |
| 원본 저장소 5개의 Git 트리 및 레지스트리 패키지 84개의 체크섬 | 통과 |
| 로컬 Abseil과 Protobuf의 빌드 및 설치 | 통과, `libprotoc 36.2` |
| 빈 전용 Cargo 캐시에서 벤더링 소스만으로 Rust 빌드와 코드 생성 | 통과 |
| Rust gRPC 메시지 왕복과 오류 상태 전달 | 1개 테스트 통과 |
| 설치된 CMake 패키지를 사용하는 C++ 코드 생성 및 직렬화 왕복 | 1개 테스트 통과 |
| 저장소 밖의 공백 포함 경로에서 독립 Cargo 잠금 파일 생성과 빌드 | 통과 |
| 독립 소비 프로젝트의 의존성 경로 확인 | 96개 의존성 모두 Flax 내부 소스로 연결 |

gRPC 실행 검사는 초기 샌드박스에서 로컬 포트 생성이 차단되었고, 루프백 통신을
허용한 환경에서 재실행해 통과했다. 원본 Protobuf의 Java 생성기 컴파일 중 GCC의
`-Wstringop-overread` 경고가 있었으며 빌드는 성공했다. 해당 원본에는 수정하지 않았다.

## 버전 갱신

1. 원본 라이브러리는 태그와 커밋 SHA를 확인해 반입하고 `sources.json`을 갱신한다.
2. 선택한 기능을 검증 구성에 반영하고 Cargo 잠금 파일을 갱신한다. 이때
   `integration/rust-packages.json`의 로컬 경로를 `[patch.crates-io]`로 구성한 임시
   Cargo 설정을 `--config`로 전달한다. 그 설정에서는 source replacement와 offline
   설정을 제외한다. 유지보수 과정에서만 원본 레지스트리에 접근하며, 일반 소비 빌드는
   오프라인 구성을 유지한다.
3. `cargo vendor --locked`로 해당 잠금 파일의 레지스트리 패키지를 확보한다.
   위와 동일한 로컬 patch 설정을 적용하고 임시 출력 디렉토리를 사용한다.
   라이선스와 `.cargo-checksum.json`을 유지하고 패키지의 주된 역할에 맞게 배치한 뒤
   `rust-registry.json`에 경로, 버전, 출처와 패키지 체크섬을 기록한다.
4. 원본 무결성, 네이티브 빌드, Rust와 C++ 소비 검증을 실행한다.

레지스트리 패키지는 배포된 crate 소스이며 원본 저장소 전체와는 구분한다.
같은 패키지의 호환되지 않는 두 계열이 동시에 필요할 때만 `syn/2`, `syn/3`처럼
라이브러리 디렉토리 아래에 호환 계열을 둔다. 소비 프로젝트는 그 물리 경로를 참조하지 않는다.
