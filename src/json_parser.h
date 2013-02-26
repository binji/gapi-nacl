#ifndef JSON_PARSER_H_
#define JSON_PARSER_H_

#include "yajl/yajl_parse.h"

class JsonCallbacks {
 public:
  virtual int OnNull() = 0;
  virtual int OnBool(bool value) = 0;
  virtual int OnNumber(const unsigned char* s, size_t length) = 0;
  virtual int OnStartMap() = 0;
  virtual int OnMapKey(const unsigned char* s, size_t length) = 0;
  virtual int OnEndMap() = 0;
  virtual int OnStartArray() = 0;
  virtual int OnEndArray() = 0;
};

class JsonParser : public JsonCallbacks {
 public:
 private:
  static int callback_null(void*);
  static int callback_boolean(void*, int);
  static int callback_number(void*, const char*, size_t);
  static int callback_string(void*, const unsigned char*, size_t);
  static int callback_start_map(void*);
  static int callback_map_key(void*, const unsigned char*, size_t);
  static int callback_end_map(void*);
  static int callback_start_array(void*);
  static int callback_end_array(void*);

  static yajl_callbacks s_callbacks;
};

#endif  // JSON_PARSER_H_
