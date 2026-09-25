#include "echo.pb.h"

#include <string>

int main() {
  flax::check::EchoRequest request;
  request.set_text("protobuf consumer");
  request.set_payload(std::string("\0\xff", 2));
  std::string bytes;
  if (!request.SerializeToString(&bytes)) return 1;
  flax::check::EchoRequest parsed;
  if (!parsed.ParseFromString(bytes)) return 2;
  return parsed.text() == request.text() && parsed.payload() == request.payload() ? 0 : 3;
}
