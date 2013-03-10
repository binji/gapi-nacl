#include "io.h"
#include <algorithm>
#include <string.h>

MemoryReader::MemoryReader(const void* buf, size_t size)
    : buf_(buf),
      size_(size),
      offs_(0) {
}

MemoryReader::MemoryReader(const std::vector<char>& data)
    : buf_(&data[0]),
      size_(data.size()),
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

MemoryWriter::MemoryWriter() {
}

MemoryWriter::~MemoryWriter() {
}

size_t MemoryWriter::Write(const void* buf, size_t count, ErrorPtr* error) {
  size_t old_size = data_.size();
  data_.resize(old_size + count);
  memcpy(&data_[old_size], buf, count);
  return count;
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

int Compare(Reader* r1, Reader* r2, ErrorPtr* out_error) {
  const size_t BUFFER_SIZE = 32*1024;
  char buffer1[BUFFER_SIZE];
  char buffer2[BUFFER_SIZE];
  int bufend1 = 0;
  int bufend2 = 0;
  ErrorPtr error1;
  ErrorPtr error2;
  while (true) {
    size_t nread1 = r1->Read(&buffer1[bufend1], BUFFER_SIZE - bufend1, &error1);
    size_t nread2 = r2->Read(&buffer2[bufend2], BUFFER_SIZE - bufend2, &error2);
    bufend1 += nread1;
    bufend2 += nread2;
    int minend = std::min(bufend1, bufend2);
    int result = memcmp(&buffer1[0], &buffer2[0], minend);
    if (minend > 0 && result != 0) {
      // Find location of error.
      if (out_error) {
        for (int i = 0; i < minend; ++i) {
          if (buffer1[i] != buffer2[i]) {
            // Found it, give error some context.
            const int kContextChars = 20;
            std::string context1(&buffer1[std::max(0, i - kContextChars)],
                                 &buffer1[std::min(i + kContextChars, bufend1)]);
            std::string context2(&buffer2[std::max(0, i - kContextChars)],
                                 &buffer2[std::min(i + kContextChars, bufend2)]);
            out_error->reset(new MessageError(
                  "Unequal, \"..." + context1 +
                  "...\" != \"..." + context2 + "...\""));
            break;
          }
        }
      }
      return result;
    }
    if (error1 || error2)
      break;
    memmove(&buffer1[0], &buffer1[minend], bufend1 - minend);
    memmove(&buffer2[0], &buffer2[minend], bufend2 - minend);
    bufend1 -= minend;
    bufend2 -= minend;
  }

  if (bufend1 == bufend2) {
    if (error1 == EOFError && error2 == EOFError)
      return 0;

    if (error1 == EOFError) {
      if (error2 && out_error)
        *out_error = error2;
      return -1;
    } else if (error2 == EOFError) {
      if (error1 && out_error)
        *out_error = error1;
      return 1;
    }
  } else {
    if (out_error) {
      if (error1 == EOFError && error2 == EOFError) {
        out_error->reset();
      } else if (error1 == EOFError) {
        if (error2)
          *out_error = error2;
      } else if (error2 == EOFError) {
        if (error1)
          *out_error = error1;
      } else if (error1) {
        *out_error = error1;
      } else {
        *out_error = error2;
      }
    }

    return bufend1 < bufend2 ? -1 : 1;
  }
}
