#ifndef JSON_PARSER_MACROS_H_
#define JSON_PARSER_MACROS_H_

#define PUSH_CALLBACK_REF_AND_RETURN(TYPE, CBTYPE, IDENT) \
  IDENT.reset(new TYPE()); \
  p->PushCallbacks(new CBTYPE(IDENT.get())); \
  return p->OnStartMap()

#define PUSH_CALLBACK_REF_ARRAY_AND_RETURN(TYPE, CBTYPE, IDENT) \
  IDENT.push_back(std::tr1::shared_ptr<TYPE>(new TYPE())); \
  p->PushCallbacks(new CBTYPE(IDENT.back().get())); \
  return p->OnStartMap()

#define APPEND_BOOL_AND_RETURN(IDENT) \
  IDENT.push_back(value); \
  return 1

#define SET_BOOL_AND_RETURN(IDENT, STATE) \
  IDENT = value; \
  state_ = STATE; \
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
  IDENT.push_back(static_cast<TYPE>(value)); } \
  return 1

#define APPEND_INT32_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(int32_t, IDENT, strtol, long int)

#define APPEND_UINT32_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(uint32_t, IDENT, strtoul, unsigned long int)

#define APPEND_INT64_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(int64_t, IDENT, strtoll, long long int)

#define APPEND_UINT64_AND_RETURN(IDENT) \
  APPEND_INT_AND_RETURN(uint64_t, IDENT, strtoull, unsigned long long int)

#define SET_INT_AND_RETURN(TYPE, IDENT, FUNC, FUNC_TYPE, STATE) { \
  CONVERT_AND_CHECK_INT(TYPE, FUNC, FUNC_TYPE) \
  IDENT = static_cast<TYPE>(value); } \
  state_ = STATE; \
  return 1

#define SET_INT32_AND_RETURN(IDENT, STATE) \
  SET_INT_AND_RETURN(int32_t, IDENT, strtol, long int, STATE)

#define SET_UINT32_AND_RETURN(IDENT, STATE) \
  SET_INT_AND_RETURN(uint32_t, IDENT, strtoul, unsigned long int, STATE)

#define SET_INT64_AND_RETURN(IDENT, STATE) \
  SET_INT_AND_RETURN(int64_t, IDENT, strtoll, long long int, STATE)

#define SET_UINT64_AND_RETURN(IDENT, STATE) \
  SET_INT_AND_RETURN(uint64_t, IDENT, strtoull, unsigned long long int, STATE)

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
  IDENT.push_back(value); } \
  return 1

#define APPEND_FLOAT_AND_RETURN(IDENT) \
  APPEND_FP_AND_RETURN(float, IDENT, strtof)

#define APPEND_DOUBLE_AND_RETURN(IDENT) \
  APPEND_FP_AND_RETURN(double, IDENT, strtod)

#define SET_FP_AND_RETURN(TYPE, IDENT, FUNC, STATE) { \
  CONVERT_AND_CHECK_FP(TYPE, FUNC) \
  IDENT = value; } \
  state_ = STATE; \
  return 1

#define SET_FLOAT_AND_RETURN(IDENT, STATE) \
  SET_FP_AND_RETURN(float, IDENT, strtof, STATE)

#define SET_DOUBLE_AND_RETURN(IDENT, STATE) \
  SET_FP_AND_RETURN(double, IDENT, strtod, STATE)

#define APPEND_STRING_AND_RETURN(IDENT) \
  IDENT.push_back( \
      std::string(reinterpret_cast<const char*>(s), length)); \
  return 1

#define SET_STRING_AND_RETURN(IDENT, STATE) \
  IDENT.assign(reinterpret_cast<const char*>(s), length); \
  state_ = STATE; \
  return 1

#define CHECK_MAP_KEY(NAME, LEN, STATE) \
  if (length == LEN && \
      strncmp(reinterpret_cast<const char*>(s), NAME, length) == 0) { \
    state_ = STATE; \
    return 1; }

#define MAP_KEY_ADDL_PROPS(IDENT, TYPE, ITER, STATE) { \
  const char* ss = reinterpret_cast<const char*>(s); \
  std::string key(ss, ss + length); \
  ITER = IDENT.insert(TYPE::value_type(key, TYPE::mapped_type())).first; \
  state_ = STATE; \
  return 1; }


// Encoding

#define CHECK_GEN(NAME) if (!g->Gen##NAME(error)) return false
#define CHECK_GEN1(NAME, ARG) if (!g->Gen##NAME(ARG, error)) return false
#define CHECK_GEN_KEY(KEY, LEN) if (!g->GenString(KEY, LEN, error)) return false
#define CHECK_GEN_STRING(ARG) if (!g->GenString(ARG.data(), ARG.size(), error)) return false
#define CHECK_ENCODE(ARG) if (!Encode(g, ARG, error)) return false
#define GEN_FOREACH(IX, ARRAY) for (size_t IX = 0; IX < ARRAY.size(); ++IX)
#define GEN_FOREACH_ITER(IX, VAR, TYPE) for (TYPE::const_iterator IX = VAR.begin(); IX != VAR.end(); ++IX)

#endif  // JSON_PARSER_MACROS_H_
