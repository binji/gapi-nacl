#include "io.h"

size_t Copy(Writer* dst, Reader* src, ErrorPtr* error) {
  const size_t BUFFER_SIZE = 32*1024;
  char buffer[BUFFER_SIZE];
  size_t total_written = 0;
  while (true) {
    size_t nread = src->Read(&buffer[0], BUFFER_SIZE, error);
    if (nread > 0) {
      size_t nwrote = dst->Write(&buffer[0], nread, error);
      total_written += nwrote;
      if (error && *error)
        break;
      if (nread != nwrote && error) {
         error->reset(new MessageError("Short write"));
        break;
      }
    }
    if (error && *error == EOFError) {
      error->reset();
      break;
    }
    if (error && *error)
      break;
  }
  return total_written;
}
