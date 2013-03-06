#include "io.h"
#include <algorithm>
#include <string.h>

MemoryReader::MemoryReader(const void* buf, size_t size)
    : buf_(buf),
      size_(size),
      offs_(0) {
}

size_t MemoryReader::Read(void* dst, size_t count, ErrorPtr* error) {
  if (offs_ == size_) {
    if (error)
      *error = EOFError;
    return 0;
  }

  count = std::min(size_ - offs_, count);
  memcpy(dst, static_cast<const char*>(buf_) + offs_, count);
  offs_ += count;
  return count;
}

FileReader::FileReader(const char* filename)
   : file_(NULL) {
  file_ = fopen(filename, "rt");
}

FileReader::~FileReader() {
  if (file_)
    fclose(file_);
}

size_t FileReader::Read(void* buf, size_t count, ErrorPtr* error) {
  if (file_ == NULL) {
    error->reset(new MessageError("File not open"));
    return 0;
  }

  size_t nread = fread(buf, 1, count, file_);
  if (error) {
    if (feof(file_))
      *error = EOFError;
    else if (ferror(file_))
      error->reset(new MessageError("Error reading file"));
  }
  return nread;
}

size_t Copy(Writer* dst, Reader* src, ErrorPtr* out_error) {
  const size_t BUFFER_SIZE = 32*1024;
  char buffer[BUFFER_SIZE];
  size_t total_written = 0;
  ErrorPtr error;
  while (true) {
    size_t nread = src->Read(&buffer[0], BUFFER_SIZE, &error);
    if (nread > 0) {
      size_t nwrote = dst->Write(&buffer[0], nread, &error);
      total_written += nwrote;
      if (error)
        break;
      if (nread != nwrote) {
         error.reset(new MessageError("Short write"));
        break;
      }
    }
    if (error == EOFError) {
      error.reset();
      break;
    }
    if (error)
      break;
  }
  if (out_error)
    *out_error = error;
  return total_written;
}
