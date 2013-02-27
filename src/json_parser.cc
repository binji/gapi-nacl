#include "json_parser.h"

JsonParser::JsonParser() {
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
