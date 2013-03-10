#include "error.h"

ErrorPtr EOFError(new MessageError("EOF"));

MessageError::MessageError(const char* message)
    : message_(message) {
}

MessageError::MessageError(const std::string& message)
    : message_(message) {
}

std::string MessageError::ToString() const {
  return message_;
}

YajlError::YajlError(yajl_handle handle, const char* text, size_t length,
                     const char* extra_info) {
  unsigned char* yajl_message = yajl_get_error(
      handle, text && length,
      reinterpret_cast<const unsigned char*>(text), length);
  message_ = reinterpret_cast<const char*>(yajl_message);
  if (extra_info) {
    message_ += extra_info;
  }
  yajl_free_error(handle, yajl_message);
}

std::string YajlError::ToString() const {
  return message_;
}
