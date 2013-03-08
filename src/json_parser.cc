#include "json_parser.h"

JsonParser::JsonParser() {
  // NULL => use the default C alloc funcs (malloc, realloc, free).
  handle_ = yajl_alloc(&s_callbacks, NULL, this);
}

JsonParser::~JsonParser() {
  for (size_t i = 0; i < callbacks_stack_.size(); ++i)
    delete callbacks_stack_[i];
  yajl_free(handle_);
}

void JsonParser::Decode(Reader* src, ErrorPtr* out_error) {
  ErrorPtr error;
  Copy(this, src, &error);
  if (error) {
    if (out_error)
      *out_error = error;
    return;
  }
  Close(out_error);
}

size_t JsonParser::Write(const void* buf, size_t count, ErrorPtr* error) {
  yajl_status status =
      yajl_parse(handle_, static_cast<const unsigned char*>(buf), count);
  SetErrorFromStatus(error, status, static_cast<const char*>(buf), count);
  return yajl_get_bytes_consumed(handle_);
}

void JsonParser::Close(ErrorPtr* error) {
  yajl_status status = yajl_complete_parse(handle_);
  SetErrorFromStatus(error, status, NULL, 0);
}

void JsonParser::SetErrorFromStatus(ErrorPtr* error, yajl_status status,
                                    const char* text, size_t length) {
  if (!error)
    return;

  switch (status) {
    case yajl_status_ok:
      error->reset();
      break;

    case yajl_status_client_canceled:
      error->reset(new YajlError(handle_, text, length,
                                 error_->ToString().c_str()));
      break;

    case yajl_status_error:
      error->reset(new YajlError(handle_, text, length));
      break;

    default:
      error->reset(new MessageError("Unknown YAJL status."));
      break;
  }
}

int JsonParser::OnNull() {
  return top_callbacks()->OnNull(this, &error_);
}

int JsonParser::OnBool(bool value) {
  return top_callbacks()->OnBool(this, value, &error_);
}

int JsonParser::OnNumber(const char* s, size_t length) {
  return top_callbacks()->OnNumber(this, s, length, &error_);
}

int JsonParser::OnString(const unsigned char* s, size_t length) {
  return top_callbacks()->OnString(this, s, length, &error_);
}

int JsonParser::OnStartMap() {
  return top_callbacks()->OnStartMap(this, &error_);
}

int JsonParser::OnMapKey(const unsigned char* s, size_t length) {
  return top_callbacks()->OnMapKey(this, s, length, &error_);
}

int JsonParser::OnEndMap() {
  return top_callbacks()->OnEndMap(this, &error_);
}

int JsonParser::OnStartArray() {
  return top_callbacks()->OnStartArray(this, &error_);
}

int JsonParser::OnEndArray() {
  return top_callbacks()->OnEndArray(this, &error_);
}

bool JsonParser::HasCallbacks() const {
  return !callbacks_stack_.empty();
}

void JsonParser::PushCallbacks(JsonCallbacks* callbacks) {
  callbacks_stack_.push_back(callbacks);
}

bool JsonParser::PopCallbacks() {
  if (callbacks_stack_.empty())
    return false;
  delete callbacks_stack_.back();
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
