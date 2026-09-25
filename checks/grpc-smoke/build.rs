fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("cargo:rerun-if-changed=proto/echo.proto");
    println!("cargo:rerun-if-env-changed=PROTOC");
    tonic_prost_build::compile_protos("proto/echo.proto")?;
    Ok(())
}
