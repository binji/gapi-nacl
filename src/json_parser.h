#ifndef JSON_PARSER_H_
#define JSON_PARSER_H_

#include <assert.h>
#include <vector>
#include "yajl/yajl_parse.h"

class JsonParser;

class JsonCallbacks {
 public:
  virtual int OnNull(JsonParser* p) = 0;
  virtual int OnBool(JsonParser* p, bool value) = 0;
  virtual int OnNumber(JsonParser* p, const char* s, size_t len) = 0;
  virtual int OnString(JsonParser* p, const unsigned char* s, size_t len) = 0;
  virtual int OnStartMap(JsonParser* p) = 0;
  virtual int OnMapKey(JsonParser* p, const unsigned char* s, size_t len) = 0;
  virtual int OnEndMap(JsonParser* p) = 0;
  virtual int OnStartArray(JsonParser* p) = 0;
  virtual int OnEndArray(JsonParser* p) = 0;

 protected:
  int top() { return context_stack_.empty() ? 0 : context_stack_.back(); }
  void Push(int state) { context_stack_.push_back(state); }
  void Pop() { context_stack_.pop_back(); }

 private:
  std::vector<int> context_stack_;
};

class JsonParser : public JsonCallbacks {
 public:
  JsonParser();

  virtual int OnNull(JsonParser* p);
  virtual int OnBool(JsonParser* p, bool value);
  virtual int OnNumber(JsonParser* p, const char* s, size_t length);
  virtual int OnString(JsonParser* p, const unsigned char* s, size_t length);
  virtual int OnStartMap(JsonParser* p);
  virtual int OnMapKey(JsonParser* p, const unsigned char* s, size_t length);
  virtual int OnEndMap(JsonParser* p);
  virtual int OnStartArray(JsonParser* p);
  virtual int OnEndArray(JsonParser* p);

  JsonCallbacks* top_callbacks() {
    assert(!callbacks_stack_.empty());
    return callbacks_stack_.back();
  }

  void PushCallbacks(JsonCallbacks* callbacks);
  bool PopCallbacks();

 private:
#define THUNK0(NAME) \
  static int Thunk##NAME(void* ctx) { \
    JsonParser* p = static_cast<JsonParser*>(ctx); \
    return p->NAME(p); \
  }
#define THUNK1(NAME, T0) \
  static int Thunk##NAME(void* ctx, T0 arg0) { \
    JsonParser* p = static_cast<JsonParser*>(ctx); \
    return p->NAME(p, arg0); \
  }
#define THUNK2(NAME, T0, T1) \
  static int Thunk##NAME(void* ctx, T0 arg0, T1 arg1) { \
    JsonParser* p = static_cast<JsonParser*>(ctx); \
    return p->NAME(p, arg0, arg1); \
  }

  THUNK0(OnNull);
  THUNK1(OnBool, int);
  THUNK2(OnNumber, const char*, size_t);
  THUNK2(OnString, const unsigned char*, size_t);
  THUNK0(OnStartMap);
  THUNK2(OnMapKey, const unsigned char*, size_t);
  THUNK0(OnEndMap);
  THUNK0(OnStartArray);
  THUNK0(OnEndArray);

#undef THUNK0
#undef THUNK1
#undef THUNK2

  static yajl_callbacks s_callbacks;

 private:
  std::vector<JsonCallbacks*> callbacks_stack_;
};

#endif  // JSON_PARSER_H_
