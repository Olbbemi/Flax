cmake_minimum_required(VERSION 3.16)
project(FlaxNative LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Build only the selected local sources. No system-library or network fallback.
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Static libraries" FORCE)
set(ABSL_BUILD_TESTING OFF CACHE BOOL "Disable upstream tests" FORCE)
set(ABSL_ENABLE_INSTALL ON CACHE BOOL "Export Abseil targets" FORCE)
set(ABSL_PROPAGATE_CXX_STD ON CACHE BOOL "Propagate C++ standard" FORCE)
add_subdirectory(third_party/core/abseil-cpp)

set(protobuf_LOCAL_DEPENDENCIES_ONLY ON CACHE BOOL "Use local dependencies" FORCE)
set(protobuf_FORCE_FETCH_DEPENDENCIES OFF CACHE BOOL "No dependency downloads" FORCE)
set(protobuf_BUILD_TESTS OFF CACHE BOOL "Disable upstream tests" FORCE)
set(protobuf_BUILD_CONFORMANCE OFF CACHE BOOL "Disable conformance tools" FORCE)
set(protobuf_BUILD_EXAMPLES OFF CACHE BOOL "Disable upstream examples" FORCE)
set(protobuf_WITH_ZLIB OFF CACHE BOOL "Compression is outside this build profile" FORCE)
set(protobuf_INSTALL ON CACHE BOOL "Install libraries, headers and protoc" FORCE)
set(FETCHCONTENT_FULLY_DISCONNECTED ON CACHE BOOL "No dependency downloads" FORCE)
add_subdirectory(third_party/data/protobuf)
