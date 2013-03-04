#include "error.h"

ErrorPtr EOFError(new MessageError("EOF"));

MessageError::MessageError(const char* message)
    : message_(message) {
}

std::string MessageError::ToString() const {
  return message_;
}

YajlError::YajlError(yajl_handle handle)
    : handle_(handle) {
  message_ = reinterpret_cast<char*>(yajl_get_error(handle, 0, NULL, 0));
}

YajlError::~YajlError() {
  yajl_free_error(handle_, reinterpret_cast<unsigned char*>(message_));
}

std::string YajlError::ToString() const {
  return message_;
}
