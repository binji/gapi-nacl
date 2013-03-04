#ifndef ERROR_H_
#define ERROR_H_

#include <string>
#include <tr1/memory>
#include "yajl/yajl_parse.h"

class Error {
 public:
  virtual ~Error() {}
  virtual std::string ToString() const = 0;
};
typedef std::tr1::shared_ptr<Error> ErrorPtr;

class MessageError : public Error {
 public:
  MessageError(const char* message);
  virtual std::string ToString() const;

 private:
  std::string message_;
};

class YajlError : public Error {
 public:
  YajlError(yajl_handle handle);
  virtual ~YajlError();
  virtual std::string ToString() const;

 private:
  yajl_handle handle_;
  char* message_;
};

extern ErrorPtr EOFError;

#endif  // ERROR_H_
