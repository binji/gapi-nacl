#include "json_generator.h"
#define __STDC_FORMAT_MACROS  // For PRI* macros
#include <inttypes.h>

JsonGenerator::JsonGenerator(Writer* dst)
    : dst_(dst) {
  // NULL => use the default C alloc funcs (malloc, realloc, free).
  handle_ = yajl_gen_alloc(NULL);
  yajl_gen_config(handle_, yajl_gen_print_callback, ThunkOnPrint, this);
  // TODO(binji): allow configuration
  yajl_gen_config(handle_, yajl_gen_beautify, 0);
  yajl_gen_config(handle_, yajl_gen_indent_string, "  ");
  yajl_gen_config(handle_, yajl_gen_escape_solidus, 0);
  yajl_gen_config(handle_, yajl_gen_validate_utf8, 1);
}

JsonGenerator::~JsonGenerator() {
  yajl_gen_free(handle_);
}

bool JsonGenerator::GenNull(ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_null(handle_);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenBool(bool value, ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_bool(handle_, value);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenInt32(int32_t value, ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_integer(handle_, value);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenUint32(uint32_t value, ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_integer(handle_, value);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenInt64(int64_t value, ErrorPtr* error) {
  char buffer[32];
  int length = snprintf(&buffer[0], 32, "%"PRId64, value);
  yajl_gen_status status = yajl_gen_string(
      handle_, reinterpret_cast<const unsigned char*>(buffer), length);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenUint64(uint64_t value, ErrorPtr* error) {
  char buffer[32];
  int length = snprintf(&buffer[0], 32, "%"PRIu64, value);
  yajl_gen_status status = yajl_gen_string(
      handle_, reinterpret_cast<const unsigned char*>(buffer), length);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenFloat(float value, ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_double(handle_, value);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenDouble(double value, ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_double(handle_, value);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenString(const char* s, size_t length, ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_string(
      handle_, reinterpret_cast<const unsigned char*>(s), length);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenString(const std::string& s, ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_string(
      handle_, reinterpret_cast<const unsigned char*>(s.data()), s.length());
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenStartMap(ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_map_open(handle_);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenEndMap(ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_map_close(handle_);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenStartArray(ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_array_open(handle_);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

bool JsonGenerator::GenEndArray(ErrorPtr* error) {
  yajl_gen_status status = yajl_gen_array_close(handle_);
  SetErrorFromStatus(error, status);
  return status == yajl_gen_status_ok;
}

void JsonGenerator::SetErrorFromStatus(ErrorPtr* error,
                                       yajl_gen_status status) {
  if (!error)
    return;

  switch (status) {
    case yajl_gen_status_ok:
      error->reset();
      break;

    case yajl_gen_keys_must_be_strings:
      error->reset(new MessageError("Keys must be strings"));
      break;

    case yajl_max_depth_exceeded:
      error->reset(new MessageError("Max depth exceeded"));
      break;

    case yajl_gen_in_error_state:
      error->reset(new MessageError("Gen* called in error state"));
      break;

    case yajl_gen_generation_complete:
      error->reset(new MessageError("Generation complete"));
      break;

    case yajl_gen_invalid_number:
      error->reset(new MessageError("Invalid number"));
      break;

    case yajl_gen_no_buf:
      error->reset(new MessageError("No buffer"));
      break;

    case yajl_gen_invalid_string:
      error->reset(new MessageError("Invalid string"));
      break;

    default:
      error->reset(new MessageError("Unknown error"));
      break;
  }
}

void JsonGenerator::ThunkOnPrint(void* ctx, const char* s, size_t length) {
  static_cast<JsonGenerator*>(ctx)->OnPrint(s, length);
}

void JsonGenerator::OnPrint(const char* s, size_t length) {
  dst_->Write(s, length, &error_);
}
