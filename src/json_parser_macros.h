#ifndef JSON_PARSER_MACROS_H_
#define JSON_PARSER_MACROS_H_

#define PUSH_CALLBACK_OBJECT_AND_RETURN(TYPE, CBTYPE, IDENT) \
  p->PushCallbacks(new CBTYPE(&data_->IDENT)); \
  return 1

#define PUSH_CALLBACK_OBJECT_ARRAY_AND_RETURN(TYPE, CBTYPE, IDENT) \
  data_->IDENT.push_back(TYPE()); \
  p->PushCallbacks(new CBTYPE(&data_->IDENT.back())); \
  return 1

#define PUSH_CALLBACK_REF_AND_RETURN(TYPE, CBTYPE, IDENT) \
  data_->IDENT.reset(new TYPE()); \
  p->PushCallbacks(new CBTYPE(data_->IDENT.get())); \
  return 1

#define PUSH_CALLBACK_REF_ARRAY_AND_RETURN(TYPE, CBTYPE, IDENT) \
  data_->IDENT.push_back(std::tr1::shared_ptr<TYPE>(new TYPE())); \
  p->PushCallbacks(new CBTYPE(data_->IDENT.back().get())); \
  return 1

#define APPEND_BOOL_AND_RETURN(IDENT) \
  data_->IDENT.push_back(value); \
  return 1

#define SET_BOOL_AND_RETURN(IDENT) \
  data_->IDENT = value; \
  state_ = STATE_TOP; \
  return 1

#define CONVERT_AND_CHECK_INT(TYPE, FUNC, FUNC_TYPE) \
  errno = 0; \
  FUNC_TYPE value = FUNC(&buffer[0], &endptr, 10); \
  if (endptr - &buffer[0] != length) { \
    if (error) error->reset(new MessageError("Unexpected characters at end of integer")); \
    return 0; \
  } else if (errno == ERANGE || \
      value < std::numeric_limits<TYPE>::min() || \
      value > std::numeric_limits<TYPE>::max()) { \
    if (error) error->reset(new MessageError("Integer value out of range")); \
    return 0; \
  }

#define APPEND_INT_AND_RETURN(TYPE, IDENT, FUNC, FUNC_TYPE) { \
  CONVERT_AND_CHECK_INT(TYPE, FUNC, FUNC_TYPE) \
  data_->IDENT.push_back(static_cast<TYPE>(value)); } \
  return 1

#define APPEND_INT32_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(int32_t, IDENT, strtol, long int)

#define APPEND_UINT32_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(uint32_t, IDENT, strtoul, unsigned long int)

#define APPEND_INT64_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(int64_t, IDENT, strtoll, long long int)

#define APPEND_UINT64_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(uint64_t, IDENT, strtoull, unsigned long long int)

#define SET_INT_AND_RETURN(TYPE, IDENT, FUNC, FUNC_TYPE) { \
  CONVERT_AND_CHECK_INT(TYPE, FUNC, FUNC_TYPE) \
  data_->IDENT = static_cast<TYPE>(value); } \
  state_ = STATE_TOP; \
  return 1

#define SET_INT32_AND_RETURN(IDENT) \
  SET_INT_AND_RETURN(int32_t, IDENT, strtol, long int)

#define SET_UINT32_AND_RETURN(IDENT) \
  SET_INT_AND_RETURN(uint32_t, IDENT, strtoul, unsigned long int)

#define SET_INT64_AND_RETURN(IDENT) \
  SET_INT_AND_RETURN(int64_t, IDENT, strtoll, long long int)

#define SET_UINT64_AND_RETURN(IDENT) \
  SET_INT_AND_RETURN(uint64_t, IDENT, strtoull, unsigned long long int)

#define CONVERT_AND_CHECK_FP(TYPE, FUNC) \
  errno = 0; \
  TYPE value = FUNC(&buffer[0], &endptr); \
  if (endptr - &buffer[0] != length) { \
    if (error) error->reset(new MessageError("Unexpected characters at end of float")); \
    return 0; \
  } else if (errno == ERANGE) { \
    if (error) error->reset(new MessageError("Float value out of range")); \
    return 0; \
  }

#define APPEND_FP_AND_RETURN(TYPE, IDENT, FUNC) { \
  CONVERT_AND_CHECK_FP(TYPE, FUNC) \
  data_->IDENT.push_back(value); } \
  return 1

#define APPEND_FLOAT_AND_RETURN(IDENT) \
  APPEND_FP_AND_RETURN(float, IDENT, strtof)

#define APPEND_DOUBLE_AND_RETURN(IDENT) \
  APPEND_FP_AND_RETURN(double, IDENT, strtod)

#define SET_FP_AND_RETURN(TYPE, IDENT, FUNC) { \
  CONVERT_AND_CHECK_FP(TYPE, FUNC) \
  data_->IDENT = value; } \
  state_ = STATE_TOP; \
  return 1

#define SET_FLOAT_AND_RETURN(IDENT) \
  SET_FP_AND_RETURN(float, IDENT, strtof)

#define SET_DOUBLE_AND_RETURN(IDENT) \
  SET_FP_AND_RETURN(double, IDENT, strtod)

#define APPEND_STRING_AND_RETURN(IDENT) \
  data_->IDENT.push_back( \
      std::string(reinterpret_cast<const char*>(s), length)); \
  return 1

#define SET_STRING_AND_RETURN(IDENT) \
  data_->IDENT.assign(reinterpret_cast<const char*>(s), length); \
  state_ = STATE_TOP; \
  return 1

#define CHECK_MAP_KEY(NAME, LEN, STATE) \
  if (length == LEN && \
      strncmp(reinterpret_cast<const char*>(s), NAME, length) == 0) { \
    state_ = STATE; \
    return 1; }

#endif  // JSON_PARSER_MACROS_H_
