#ifndef JSON_PARSER_H_
#define JSON_PARSER_H_

#include <assert.h>
#include <string>
#include <vector>
#include "yajl/yajl_parse.h"
#include "reader.h"

class Error {
 public:
  virtual ~Error() {}
  virtual std::string ToString() const = 0;
};

class MessageError : public Error {
 public:
  virtual MessageError(const char* message);
  virtual std::string ToString() const;

 private:
  std::string message_;
};

class Reader {
 public:
  virtual ~Reader() {}
  virtual size_t Read(void* buf, size_t count, Error** error) = 0;
};

class Writer {
 public:
  virtual ~Writer() {}
  virtual size_t Write(const void* buf, size_t count, Error** error) = 0;
  virtual bool Flush(Error** error) = 0;
};


class JsonParser;

class JsonCallbacks {
 public:
  virtual ~JsonCallbacks() {}
  virtual int OnNull(JsonParser* p) = 0;
  virtual int OnBool(JsonParser* p, bool value) = 0;
  virtual int OnNumber(JsonParser* p, const char* s, size_t len) = 0;
  virtual int OnString(JsonParser* p, const unsigned char* s, size_t len) = 0;
  virtual int OnStartMap(JsonParser* p) = 0;
  virtual int OnMapKey(JsonParser* p, const unsigned char* s, size_t len) = 0;
  virtual int OnEndMap(JsonParser* p) = 0;
  virtual int OnStartArray(JsonParser* p) = 0;
  virtual int OnEndArray(JsonParser* p) = 0;
};

class JsonParser : public JsonCallbacks, public Writer {
 public:
  JsonParser();
  ~JsonParser();

  virtual size_t Write(const void* buf, size_t count, Error* error);
  virtual bool Flush(Error** error);

  void PushCallbacks(JsonCallbacks* callbacks);
  bool PopCallbacks();

 private:
  void SetErrorFromStatus(Error** error, yajl_status status);

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

 private:
  std::vector<JsonCallbacks*> callbacks_stack_;
};

#endif  // JSON_PARSER_H_
