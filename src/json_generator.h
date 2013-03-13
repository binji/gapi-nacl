#ifndef JSON_GENERATOR_H_
#define JSON_GENERATOR_H_

#include <stdint.h>
#include <stdlib.h>
#include <string>
#include "error.h"
#include "io.h"
#include "yajl/yajl_gen.h"

struct JsonGeneratorOptions {
  JsonGeneratorOptions();

  bool beautify;
  bool escape_solidus;
  bool validate_utf8;
  std::string indent_string;
};

class JsonGenerator {
 public:
  explicit JsonGenerator(Writer* dst);
  JsonGenerator(Writer* dst, const JsonGeneratorOptions& options);
  ~JsonGenerator();

  bool GenNull(ErrorPtr* error);
  bool GenBool(bool value, ErrorPtr* error);
  bool GenInt32(int32_t value, ErrorPtr* error);
  bool GenUint32(uint32_t value, ErrorPtr* error);
  bool GenInt64(int64_t value, ErrorPtr* error);
  bool GenUint64(uint64_t value, ErrorPtr* error);
  bool GenFloat(float value, ErrorPtr* error);
  bool GenDouble(double value, ErrorPtr* error);
  bool GenString(const char* s, size_t length, ErrorPtr* error);
  bool GenString(const std::string& s, ErrorPtr* error);
  bool GenStartMap(ErrorPtr* error);
  bool GenEndMap(ErrorPtr* error);
  bool GenStartArray(ErrorPtr* error);
  bool GenEndArray(ErrorPtr* error);

 private:
  void Init(const JsonGeneratorOptions& options);
  void SetErrorFromStatus(ErrorPtr* error, yajl_gen_status status);
  static void ThunkOnPrint(void* ctx, const char* s, size_t length);
  void OnPrint(const char* s, size_t length);

 private:
  yajl_gen handle_;
  Writer* dst_;
  ErrorPtr error_;
};

#endif  // JSON_GENERATOR_H_
