#ifndef JSON_PARSER_MACROS_H_
#define JSON_PARSER_MACROS_H_

#define PUSH_CALLBACK_OBJECT(TYPE, IDENT) \
  p->PushCallbacks(new TYPE##Callbacks(&data_->IDENT))

#define PUSH_CALLBACK_OBJECT_ARRAY(TYPE, IDENT) \
  data_->IDENT.push_back(TYPE##Object()); \
  p->PushCallbacks(new TYPE##Callbacks(data_->IDENT.back()))

#define PUSH_CALLBACK_REF(TYPE, IDENT) \
  data_->IDENT.reset(new TYPE()); \
  p->PushCallbacks(new TYPE##Callbacks(data_->IDENT.get()))

#define PUSH_CALLBACK_REF_ARRAY(TYPE, IDENT) \
  data_->IDENT.push_back(std::tr1::shared_ptr<TYPE>(new TYPE())); \
  p->PushCallbacks(new TYPE##Callbacks(data_->IDENT.back().get()))

#define APPEND_BOOL_AND_RETURN(IDENT) \
  data_->IDENT.push_back(value); \
  return 1

#define SET_BOOL_AND_RETURN(IDENT) \
  data_->IDENT = value; \
  state_ = STATE_TOP; \
  return 1

#define APPEND_INT_AND_RETURN(TYPE, IDENT, FUNC) { \
  TYPE value = FUNC(&buffer[0], &endptr, 10); \
  if (errno == ERANGE) return 0; \
  data_->IDENT.push_back(value); } \
  return 1

#define APPEND_INT32_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(int32_t, IDENT, strtol)

#define APPEND_UINT32_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(uint32_t, IDENT, strtoul)

#define APPEND_INT64_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(int64_t, IDENT, strtoll)

#define APPEND_UINT64_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(uint64_t, IDENT, strtoull)

#define SET_INT_AND_RETURN(TYPE, IDENT, FUNC) { \
  TYPE value = FUNC(&buffer[0], &endptr, 10); \
  if (errno == ERANGE) return 0; \
  data_->IDENT = value; } \
  state_ = STATE_TOP; \
  return 1

#define SET_INT32_AND_RETURN(IDENT) \
  SET_INT_AND_RETURN(int32_t, IDENT, strtol)

#define SET_UINT32_AND_RETURN(IDENT) \
  SET_INT_AND_RETURN(uint32_t, IDENT, strtoul)

#define SET_INT64_AND_RETURN(IDENT) \
  SET_INT_AND_RETURN(int64_t, IDENT, strtoll)

#define SET_UINT64_AND_RETURN(IDENT) \
  SET_INT_AND_RETURN(uint64_t, IDENT, strtoull)

#define APPEND_FP_AND_RETURN(TYPE, IDENT, FUNC) { \
  TYPE value = FUNC(&buffer[0], &endptr); \
  if (errno == ERANGE) return 0; \
  data_->IDENT.push_back(value); } \
  return 1

#define APPEND_FLOAT_AND_RETURN(IDENT) \
  APPEND_FP_AND_RETURN(float, IDENT, strtof)

#define APPEND_DOUBLE_AND_RETURN(IDENT) \
  APPEND_DOUBLE_AND_RETURN(double, IDENT, strtod)

#define SET_FP_AND_RETURN(TYPE, IDENT, FUNC) { \
  TYPE value = FUNC(&buffer[0], &endptr); \
  if (errno == ERANGE) return 0; \
  data_->IDENT = value; } \
  state_ = STATE_TOP; \
  return 1

#define SET_FLOAT_AND_RETURN(IDENT) \
  SET_FP_AND_RETURN(float, IDENT, strtof)

#define SET_DOUBLE_AND_RETURN(IDENT) \
  SET_DOUBLE_AND_RETURN(double, IDENT, strtod)

#define APPEND_STRING_AND_RETURN(IDENT) \
  data_->IDENT.push_back(std::string(s, length)); \
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
