#include "error.h"

ErrorPtr EOFError(new MessageError("EOF"));

MessageError::MessageError(const char* message)
    : message_(message) {
}

std::string MessageError::ToString() const {
  return message_;
}

YajlError::YajlError(yajl_handle handle, const char* text, size_t length,
                     const char* extra_info)
    : handle_(handle) {
  yajl_message_ = reinterpret_cast<char*>(yajl_get_error(
        handle, text && length,
        reinterpret_cast<const unsigned char*>(text), length));
  message_ = yajl_message_;
  if (extra_info) {
    message_ += extra_info;
  }
}

YajlError::~YajlError() {
  yajl_free_error(handle_, reinterpret_cast<unsigned char*>(yajl_message_));
}

std::string YajlError::ToString() const {
  return message_;
}
