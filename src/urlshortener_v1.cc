#include "urlshortener_v1.h"
#include <stdlib.h>
#include <string.h>
#include <vector>
#include "json_parser.h"

class AnalyticsSnapshotCallbacks : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
    STATE_BROWSERS_KEY,
    STATE_BROWSERS_ARRAY,
    STATE_COUNTRIES_KEY,
    STATE_COUNTRIES_ARRAY,
    STATE_LONG_URL_CLICKS_KEY,
    STATE_PLATFORMS_KEY,
    STATE_PLATFORMS_ARRAY,
    STATE_REFERRERS_KEY,
    STATE_REFERRERS_ARRAY,
    STATE_SHORT_URL_CLICKS_KEY,
  };

  explicit AnalyticsSnapshotCallbacks(AnalyticsSnapshot* data);
  virtual int OnNull(JsonParser* p);
  virtual int OnBool(JsonParser* p, bool value);
  virtual int OnNumber(JsonParser* p, const char* s, size_t length);
  virtual int OnString(JsonParser* p, const unsigned char* s, size_t length);
  virtual int OnStartMap(JsonParser* p);
  virtual int OnMapKey(JsonParser* p, const unsigned char* s, size_t length);
  virtual int OnEndMap(JsonParser* p);
  virtual int OnStartArray(JsonParser* p);
  virtual int OnEndArray(JsonParser* p);

 private:
  AnalyticsSnapshot* data_;
};

AnalyticsSnapshotCallbacks::AnalyticsSnapshotCallbacks(
    AnalyticsSnapshot* data)
    : data_(data) {
}

int AnalyticsSnapshotCallbacks::OnNull(JsonParser* p) {
  return 0;  // fail
}

int AnalyticsSnapshotCallbacks::OnBool(JsonParser* p, bool value) {
  return 0;  // fail
}

int AnalyticsSnapshotCallbacks::OnNumber(JsonParser* p, const char* s,
                                         size_t length) {
  char* endptr;
  char buffer[32];
  strncpy(&buffer[0], s, length);
  switch (top()) {
    case STATE_SHORT_URL_CLICKS_KEY:
      data_->count = strtoll(&buffer[0], &endptr, 10);
      return endptr == s + length;
    case STATE_LONG_URL_CLICKS_KEY:
      data_->count = strtoll(&buffer[0], &endptr, 10);
      return endptr == s + length;
    default:
      return 0;
  }
}

int AnalyticsSnapshotCallbacks::OnString(JsonParser* p, const unsigned char* s,
                                         size_t length) {
  return 0;  // fail
}

int AnalyticsSnapshotCallbacks::OnStartMap(JsonParser* p) {
  return 0;  // fail
}

int AnalyticsSnapshotCallbacks::OnMapKey(JsonParser* p, const unsigned char* s,
                                         size_t length) {
  if (length == 0) return 0;
  switch (top()) {
    case STATE_TOP:
      switch (s[0]) {
        case 'b':
          if (length != 8 ||
              strncmp(reinterpret_cast<const char*>(s), "browsers", 8) != 0)
            return 0;
          Push(STATE_BROWSERS_KEY);
          return 1;
        case 'c':
          if (length != 9 ||
              strncmp(reinterpret_cast<const char*>(s), "countries", 9) != 0)
            return 0;
          Push(STATE_COUNTRIES_KEY);
          return 1;
        default:
          return 0;
      }
    default:
      return 0;
  }
}

int AnalyticsSnapshotCallbacks::OnEndMap(JsonParser* p) {
  return 0;  // fail
}

int AnalyticsSnapshotCallbacks::OnStartArray(JsonParser* p) {
  return 0;  // fail
}

int AnalyticsSnapshotCallbacks::OnEndArray(JsonParser* p) {
  return 0;  // fail
}


class StringCountCallbacks : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
    STATE_COUNT_KEY,
    STATE_ID_KEY,
  };

  explicit StringCountCallbacks(StringCount* data);
  virtual int OnNull(JsonParser* p);
  virtual int OnBool(JsonParser* p, bool value);
  virtual int OnNumber(JsonParser* p, const char* s, size_t length);
  virtual int OnString(JsonParser* p, const unsigned char* s, size_t length);
  virtual int OnStartMap(JsonParser* p);
  virtual int OnMapKey(JsonParser* p, const unsigned char* s, size_t length);
  virtual int OnEndMap(JsonParser* p);
  virtual int OnStartArray(JsonParser* p);
  virtual int OnEndArray(JsonParser* p);

 private:
  StringCount* data_;
};

StringCountCallbacks::StringCountCallbacks(StringCount* data)
    : data_(data) {
}

int StringCountCallbacks::OnNull(JsonParser* p) {
  return 0;  // fail
}

int StringCountCallbacks::OnBool(JsonParser* p, bool value) {
  return 0;  // fail
}

int StringCountCallbacks::OnNumber(JsonParser* p, const char* s,
                                   size_t length) {
  char* endptr;
  char buffer[32];
  strncpy(&buffer[0], s, length);
  switch (top()) {
    case STATE_COUNT_KEY:
      data_->count = strtoll(&buffer[0], &endptr, 10);
      return endptr == s + length;
    default:
      return 0;
  }
}

int StringCountCallbacks::OnString(JsonParser* p, const unsigned char* s,
                                   size_t length) {
  switch (top()) {
    case STATE_ID_KEY:
      data_->id.assign(reinterpret_cast<const char*>(s), length);
      return 1;
    default:
      return 0;
  }
}

int StringCountCallbacks::OnStartMap(JsonParser* p) {
  switch (top()) {
    case STATE_NONE:
      Push(STATE_TOP);
      return 1;
    default:
      return 0;
  }
}

int StringCountCallbacks::OnMapKey(JsonParser* p, const unsigned char* s,
                                   size_t length) {
  if (length == 0) return 0;
  switch (top()) {
    case STATE_TOP:
      switch (s[0]) {
        case 'c':
          if (length != 5 ||
              strncmp(reinterpret_cast<const char*>(s), "count", 5) != 0)
            return 0;
          Push(STATE_COUNT_KEY);
          return 1;
        case 'i':
          if (length != 2 ||
              strncmp(reinterpret_cast<const char*>(s), "id", 2) != 0)
            return 0;
          Push(STATE_ID_KEY);
          return 1;
        default:
          return 0;
      }
    default:
      return 0;
  }
}

int StringCountCallbacks::OnEndMap(JsonParser* p) {
  switch (top()) {
    case STATE_TOP:
      Pop();
      return 1;
    default:
      return 0;
  }
}

int StringCountCallbacks::OnStartArray(JsonParser* p) {
  return 0;  // fail
}

int StringCountCallbacks::OnEndArray(JsonParser* p) {
  return 0;  // fail
}
