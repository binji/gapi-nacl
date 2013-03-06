#ifndef JSON_PARSER_H_
#define JSON_PARSER_H_

#include <assert.h>
#include <string>
#include <vector>
#include "error.h"
#include "io.h"
#include "yajl/yajl_parse.h"

class JsonParser;

class JsonCallbacks {
 public:
  virtual ~JsonCallbacks() {}
  virtual int OnNull(JsonParser* p, ErrorPtr* ptr) = 0;
  virtual int OnBool(JsonParser* p, bool value, ErrorPtr* ptr) = 0;
  virtual int OnNumber(
      JsonParser* p, const char* s, size_t len, ErrorPtr* ptr) = 0;
  virtual int OnString(
      JsonParser* p, const unsigned char* s, size_t len, ErrorPtr* ptr) = 0;
  virtual int OnStartMap(JsonParser* p, ErrorPtr* ptr) = 0;
  virtual int OnMapKey(
      JsonParser* p, const unsigned char* s, size_t len, ErrorPtr* ptr) = 0;
  virtual int OnEndMap(JsonParser* p, ErrorPtr* ptr) = 0;
  virtual int OnStartArray(JsonParser* p, ErrorPtr* ptr) = 0;
  virtual int OnEndArray(JsonParser* p, ErrorPtr* ptr) = 0;
};

class JsonParser : public Writer, public Closer {
 public:
  JsonParser();
  ~JsonParser();

  void Decode(Reader* src, ErrorPtr* error);

  virtual size_t Write(const void* buf, size_t count, ErrorPtr* error);
  virtual void Close(ErrorPtr* error);

  void PushCallbacks(JsonCallbacks* callbacks);
  bool PopCallbacks();

 private:
  void SetErrorFromStatus(ErrorPtr* error, yajl_status status,
                          const char* text, size_t length);

  int OnNull(JsonParser* p);
  int OnBool(JsonParser* p, bool value);
  int OnNumber(JsonParser* p, const char* s, size_t length);
  int OnString(JsonParser* p, const unsigned char* s, size_t length);
  int OnStartMap(JsonParser* p);
  int OnMapKey(JsonParser* p, const unsigned char* s, size_t length);
  int OnEndMap(JsonParser* p);
  int OnStartArray(JsonParser* p);
  int OnEndArray(JsonParser* p);

  JsonCallbacks* top_callbacks() {
    assert(!callbacks_stack_.empty());
    return callbacks_stack_.back();
  }

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
  yajl_handle handle_;
  ErrorPtr error_;

 private:
  std::vector<JsonCallbacks*> callbacks_stack_;
};

#endif  // JSON_PARSER_H_
