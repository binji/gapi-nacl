#ifndef IO_H_
#define IO_H_

#include <stdio.h>
#include <vector>
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
  explicit MemoryReader(const std::vector<char>& data);
  virtual size_t Read(void* buf, size_t count, ErrorPtr* error);

 private:
  const void* buf_;
  size_t size_;
  size_t offs_;
};

class FileReader : public Reader {
 public:
  explicit FileReader(const char* filename);
  ~FileReader();
  virtual size_t Read(void* buf, size_t count, ErrorPtr* error);

 private:
  FILE* file_;
};

class MemoryWriter : public Writer {
 public:
  MemoryWriter();
  ~MemoryWriter();
  virtual size_t Write(const void* buf, size_t count, ErrorPtr* error);

  const std::vector<char>& data() const { return data_; }

 private:
  std::vector<char> data_;
};

size_t Copy(Writer* dst, Reader* src, ErrorPtr* error);
int Compare(Reader* r1, Reader* r2, ErrorPtr* error);

#endif  // IO_H_
