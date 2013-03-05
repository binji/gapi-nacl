#ifndef IO_H_
#define IO_H_

#include "error.h"

class Reader {
 public:
  virtual ~Reader() {}
  virtual size_t Read(void* buf, size_t count, ErrorPtr* error) = 0;
};

class Writer {
 public:
  virtual ~Writer() {}
  virtual size_t Write(const void* buf, size_t count, ErrorPtr* error) = 0;
};

class Closer {
 public:
  virtual ~Closer() {}
  virtual void Close(ErrorPtr* error) = 0;
};

class MemoryReader : public Reader {
 public:
  MemoryReader(const void* buf, size_t size);
  virtual size_t Read(void* buf, size_t count, ErrorPtr* error);

 private:
  const void* buf_;
  size_t size_;
  size_t offs_;
};

size_t Copy(Writer* dst, Reader* src, ErrorPtr* error);

#endif  // IO_H_
