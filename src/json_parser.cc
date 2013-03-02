#include "json_parser.h"

namespace {

class YajlError : public Error {
 public:
  YajlError(yajl_handle handle);
  virtual std::string ToString() const;

 private:
  std::string message_;
};

YajlError::YajlError(yajl_handle handle) {
}

std::string YajlError::ToString() const {
}


}  // namespace

MessageError::MessageError(const char* message)
    : message_(message) {
}

std::string MessageError::ToString() const {
  return message_;
}

JsonParser::JsonParser() {
  // NULL => use the default alloc funcs (malloc, realloc, free).
  handle_ = yajl_alloc(s_callbacks, NULL, this);
}

JsonParser::~JsonParser() {
  yajl_free(handle_);
}

size_t JsonParser::Write(const void* buf, size_t count, Error** error) {
  yajl_status status =
      yajl_parse(handle_, reinterpret_cast<const unsigned char*>(buf), count);
  SetErrorFromStatus(error, status);
  return yajl_get_bytes_consumed(handle_);
}

bool JsonParser::Flush(Error** error) {
  yajl_status status = yajl_complete_parse(handle_);
  SetErrorFromStatus(error, status);
  return yajl_status_ok;
}

void JsonParser::SetErrorFromStatus(Error** error, yajl_status status) {
  if (!error)
    return;

  switch (status) {
    case yajl_status_ok:
      *error = NULL;
      break;

    case yajl_status_client_cancelled:
      *error = new MessageError("Client cancelled.");
      break;

    case yajl_status_error:
      *error = new YajlError(handle_);
      break;

    default:
      *error = new MessageError("Unknown YAJL status.");
      break;
  }
}

int JsonParser::OnNull(JsonParser* p) {
  return top_callbacks()->OnNull(p);
}

int JsonParser::OnBool(JsonParser* p, bool value) {
  return top_callbacks()->OnBool(p, value);
}

int JsonParser::OnNumber(JsonParser* p, const char* s, size_t length) {
  return top_callbacks()->OnNumber(p, s, length);
}

int JsonParser::OnString(JsonParser* p, const unsigned char* s, size_t length) {
  return top_callbacks()->OnString(p, s, length);
}

int JsonParser::OnStartMap(JsonParser* p) {
  return top_callbacks()->OnStartMap(p);
}

int JsonParser::OnMapKey(JsonParser* p, const unsigned char* s, size_t length) {
  return top_callbacks()->OnMapKey(p, s, length);
}

int JsonParser::OnEndMap(JsonParser* p) {
  return top_callbacks()->OnEndMap(p);
}

int JsonParser::OnStartArray(JsonParser* p) {
  return top_callbacks()->OnStartArray(p);
}

int JsonParser::OnEndArray(JsonParser* p) {
  return top_callbacks()->OnEndArray(p);
}

void JsonParser::PushCallbacks(JsonCallbacks* callbacks) {
  callbacks_stack_.push_back(callbacks);
}

bool JsonParser::PopCallbacks() {
  if (callbacks_stack_.empty())
    return false;
  callbacks_stack_.pop_back();
  return true;
}

yajl_callbacks JsonParser::s_callbacks = {
  &JsonParser::ThunkOnNull,
  &JsonParser::ThunkOnBool,
  NULL,
  NULL,
  &JsonParser::ThunkOnNumber,
  &JsonParser::ThunkOnString,
  &JsonParser::ThunkOnStartMap,
  &JsonParser::ThunkOnMapKey,
  &JsonParser::ThunkOnEndMap,
  &JsonParser::ThunkOnStartArray,
  &JsonParser::ThunkOnEndArray,
};