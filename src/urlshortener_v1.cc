#include "urlshortener_v1.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vector>
#include "json_parser.h"
#include "json_parser_macros.h"

class AnalyticsSnapshotCallbacks : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
    STATE_BROWSERS_A,
    STATE_BROWSERS_K,
    STATE_COUNTRIES_A,
    STATE_COUNTRIES_K,
    STATE_LONGURLCLICKS_K,
    STATE_PLATFORMS_A,
    STATE_PLATFORMS_K,
    STATE_REFERRERS_A,
    STATE_REFERRERS_K,
    STATE_SHORTURLCLICKS_K,
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
  int state_;
};

class AnalyticsSummaryCallbacks : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
    STATE_ALLTIME_K,
    STATE_DAY_K,
    STATE_MONTH_K,
    STATE_TWOHOURS_K,
    STATE_WEEK_K,
  };

  explicit AnalyticsSummaryCallbacks(AnalyticsSummary* data);
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
  AnalyticsSummary* data_;
  int state_;
};

class StringCountCallbacks : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
    STATE_COUNT_K,
    STATE_ID_K,
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
  int state_;
};

class UrlCallbacks : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
    STATE_ANALYTICS_K,
    STATE_CREATED_K,
    STATE_ID_K,
    STATE_KIND_K,
    STATE_LONGURL_K,
    STATE_STATUS_K,
  };

  explicit UrlCallbacks(Url* data);
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
  Url* data_;
  int state_;
};

class UrlHistoryCallbacks : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
    STATE_ITEMSPERPAGE_K,
    STATE_ITEMS_A,
    STATE_ITEMS_K,
    STATE_KIND_K,
    STATE_NEXTPAGETOKEN_K,
    STATE_TOTALITEMS_K,
  };

  explicit UrlHistoryCallbacks(UrlHistory* data);
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
  UrlHistory* data_;
  int state_;
};


void Decode(Reader* src, AnalyticsSnapshot* out_data, ErrorPtr* error) {
  JsonParser p;
  p.PushCallbacks(new AnalyticsSnapshotCallbacks(out_data));
  p.Decode(src, error);
}

AnalyticsSnapshotCallbacks::AnalyticsSnapshotCallbacks(AnalyticsSnapshot* data)
    : data_(data),
      state_(STATE_NONE) {
}

int AnalyticsSnapshotCallbacks::OnNull(JsonParser* p) {
  printf("AnalyticsSnapshotCallbacks::OnNull()\n");
  return 0;
}

int AnalyticsSnapshotCallbacks::OnBool(JsonParser* p, bool value) {
  printf("AnalyticsSnapshotCallbacks::OnBool(%d) %d\n", value, state_);
  return 0;
}

int AnalyticsSnapshotCallbacks::OnNumber(JsonParser* p, const char* s, size_t length) {
  printf("AnalyticsSnapshotCallbacks::OnNumber(%.*s) %d\n", length, s, state_);
  return 0;
}

int AnalyticsSnapshotCallbacks::OnString(JsonParser* p, const unsigned char* s, size_t length) {
  printf("AnalyticsSnapshotCallbacks::OnString(%.*s) %d\n", length, s, state_);
  char* endptr;
  char buffer[32];
  strncpy(&buffer[0], reinterpret_cast<const char*>(s), length);
  switch (state_) {
    case STATE_LONGURLCLICKS_K:
      SET_INT64_AND_RETURN(long_url_clicks);
    case STATE_SHORTURLCLICKS_K:
      SET_INT64_AND_RETURN(short_url_clicks);
    default:
      return 0;
  }
}

int AnalyticsSnapshotCallbacks::OnStartMap(JsonParser* p) {
  printf("AnalyticsSnapshotCallbacks::OnStartMap() %d\n", state_);
  switch (state_) {
    case STATE_NONE:
      state_ = STATE_TOP;
      return 1;
    case STATE_BROWSERS_A:
      PUSH_CALLBACK_REF_ARRAY_AND_RETURN(StringCount, browsers);
    case STATE_COUNTRIES_A:
      PUSH_CALLBACK_REF_ARRAY_AND_RETURN(StringCount, countries);
    case STATE_PLATFORMS_A:
      PUSH_CALLBACK_REF_ARRAY_AND_RETURN(StringCount, platforms);
    case STATE_REFERRERS_A:
      PUSH_CALLBACK_REF_ARRAY_AND_RETURN(StringCount, referrers);
    default:
      return 0;
  }
}

int AnalyticsSnapshotCallbacks::OnMapKey(JsonParser* p, const unsigned char* s, size_t length) {
  printf("AnalyticsSnapshotCallbacks::OnMapKey(%.*s) %d\n", length, s, state_);
  if (length == 0) return 0;
  switch (s[0]) {
    case 'b':
      CHECK_MAP_KEY("browsers", 8, STATE_BROWSERS_K);
      return 0;
    case 'c':
      CHECK_MAP_KEY("countries", 9, STATE_COUNTRIES_K);
      return 0;
    case 'l':
      CHECK_MAP_KEY("longUrlClicks", 13, STATE_LONGURLCLICKS_K);
      return 0;
    case 'p':
      CHECK_MAP_KEY("platforms", 9, STATE_PLATFORMS_K);
      return 0;
    case 'r':
      CHECK_MAP_KEY("referrers", 9, STATE_REFERRERS_K);
      return 0;
    case 's':
      CHECK_MAP_KEY("shortUrlClicks", 14, STATE_SHORTURLCLICKS_K);
      return 0;
    default:
      return 0;
  }
}

int AnalyticsSnapshotCallbacks::OnEndMap(JsonParser* p) {
  printf("AnalyticsSnapshotCallbacks::OnEndMap() %d\n", state_);
  return p->PopCallbacks() ? 1 : 0;
}

int AnalyticsSnapshotCallbacks::OnStartArray(JsonParser* p) {
  printf("AnalyticsSnapshotCallbacks::OnStartArray() %d\n", state_);
  switch (state_) {
    case STATE_REFERRERS_K:
      state_ = STATE_REFERRERS_A;
      return 1;
    case STATE_COUNTRIES_K:
      state_ = STATE_COUNTRIES_A;
      return 1;
    case STATE_PLATFORMS_K:
      state_ = STATE_PLATFORMS_A;
      return 1;
    case STATE_BROWSERS_K:
      state_ = STATE_BROWSERS_A;
      return 1;
    default:
      return 0;
  }
}

int AnalyticsSnapshotCallbacks::OnEndArray(JsonParser* p) {
  printf("AnalyticsSnapshotCallbacks::OnEndArray() %d\n", state_);
  switch (state_) {
    case STATE_REFERRERS_A:
      state_ = STATE_TOP;
      return 1;
    case STATE_COUNTRIES_A:
      state_ = STATE_TOP;
      return 1;
    case STATE_PLATFORMS_A:
      state_ = STATE_TOP;
      return 1;
    case STATE_BROWSERS_A:
      state_ = STATE_TOP;
      return 1;
    default:
      return 0;
  }
}


void Decode(Reader* src, AnalyticsSummary* out_data, ErrorPtr* error) {
  JsonParser p;
  p.PushCallbacks(new AnalyticsSummaryCallbacks(out_data));
  p.Decode(src, error);
}

AnalyticsSummaryCallbacks::AnalyticsSummaryCallbacks(AnalyticsSummary* data)
    : data_(data),
      state_(STATE_NONE) {
}

int AnalyticsSummaryCallbacks::OnNull(JsonParser* p) {
  printf("AnalyticsSummaryCallbacks::OnNull()\n");
  return 0;
}

int AnalyticsSummaryCallbacks::OnBool(JsonParser* p, bool value) {
  printf("AnalyticsSummaryCallbacks::OnBool(%d) %d\n", value, state_);
  return 0;
}

int AnalyticsSummaryCallbacks::OnNumber(JsonParser* p, const char* s, size_t length) {
  printf("AnalyticsSummaryCallbacks::OnNumber(%.*s) %d\n", length, s, state_);
  return 0;
}

int AnalyticsSummaryCallbacks::OnString(JsonParser* p, const unsigned char* s, size_t length) {
  printf("AnalyticsSummaryCallbacks::OnString(%.*s) %d\n", length, s, state_);
  return 0;
}

int AnalyticsSummaryCallbacks::OnStartMap(JsonParser* p) {
  printf("AnalyticsSummaryCallbacks::OnStartMap() %d\n", state_);
  switch (state_) {
    case STATE_NONE:
      state_ = STATE_TOP;
      return 1;
    case STATE_ALLTIME_K:
      PUSH_CALLBACK_REF_AND_RETURN(AnalyticsSnapshot, all_time);
    case STATE_DAY_K:
      PUSH_CALLBACK_REF_AND_RETURN(AnalyticsSnapshot, day);
    case STATE_MONTH_K:
      PUSH_CALLBACK_REF_AND_RETURN(AnalyticsSnapshot, month);
    case STATE_TWOHOURS_K:
      PUSH_CALLBACK_REF_AND_RETURN(AnalyticsSnapshot, two_hours);
    case STATE_WEEK_K:
      PUSH_CALLBACK_REF_AND_RETURN(AnalyticsSnapshot, week);
    default:
      return 0;
  }
}

int AnalyticsSummaryCallbacks::OnMapKey(JsonParser* p, const unsigned char* s, size_t length) {
  printf("AnalyticsSummaryCallbacks::OnMapKey(%.*s) %d\n", length, s, state_);
  if (length == 0) return 0;
  switch (s[0]) {
    case 'a':
      CHECK_MAP_KEY("allTime", 7, STATE_ALLTIME_K);
      return 0;
    case 'd':
      CHECK_MAP_KEY("day", 3, STATE_DAY_K);
      return 0;
    case 'm':
      CHECK_MAP_KEY("month", 5, STATE_MONTH_K);
      return 0;
    case 't':
      CHECK_MAP_KEY("twoHours", 8, STATE_TWOHOURS_K);
      return 0;
    case 'w':
      CHECK_MAP_KEY("week", 4, STATE_WEEK_K);
      return 0;
    default:
      return 0;
  }
}

int AnalyticsSummaryCallbacks::OnEndMap(JsonParser* p) {
  printf("AnalyticsSummaryCallbacks::OnEndMap() %d\n", state_);
  return p->PopCallbacks() ? 1 : 0;
}

int AnalyticsSummaryCallbacks::OnStartArray(JsonParser* p) {
  printf("AnalyticsSummaryCallbacks::OnStartArray() %d\n", state_);
  return 0;
}

int AnalyticsSummaryCallbacks::OnEndArray(JsonParser* p) {
  printf("AnalyticsSummaryCallbacks::OnEndArray() %d\n", state_);
  return 0;
}


void Decode(Reader* src, StringCount* out_data, ErrorPtr* error) {
  JsonParser p;
  p.PushCallbacks(new StringCountCallbacks(out_data));
  p.Decode(src, error);
}

StringCountCallbacks::StringCountCallbacks(StringCount* data)
    : data_(data),
      state_(STATE_NONE) {
}

int StringCountCallbacks::OnNull(JsonParser* p) {
  printf("StringCountCallbacks::OnNull()\n");
  return 0;
}

int StringCountCallbacks::OnBool(JsonParser* p, bool value) {
  printf("StringCountCallbacks::OnBool(%d) %d\n", value, state_);
  return 0;
}

int StringCountCallbacks::OnNumber(JsonParser* p, const char* s, size_t length) {
  printf("StringCountCallbacks::OnNumber(%.*s) %d\n", length, s, state_);
  return 0;
}

int StringCountCallbacks::OnString(JsonParser* p, const unsigned char* s, size_t length) {
  printf("StringCountCallbacks::OnString(%.*s) %d\n", length, s, state_);
  char* endptr;
  char buffer[32];
  strncpy(&buffer[0], reinterpret_cast<const char*>(s), length);
  switch (state_) {
    case STATE_COUNT_K:
      SET_INT64_AND_RETURN(count);
    case STATE_ID_K:
      SET_STRING_AND_RETURN(id);
    default:
      return 0;
  }
}

int StringCountCallbacks::OnStartMap(JsonParser* p) {
  printf("StringCountCallbacks::OnStartMap() %d\n", state_);
  switch (state_) {
    case STATE_NONE:
      state_ = STATE_TOP;
      return 1;
    default:
      return 0;
  }
}

int StringCountCallbacks::OnMapKey(JsonParser* p, const unsigned char* s, size_t length) {
  printf("StringCountCallbacks::OnMapKey(%.*s) %d\n", length, s, state_);
  if (length == 0) return 0;
  switch (s[0]) {
    case 'c':
      CHECK_MAP_KEY("count", 5, STATE_COUNT_K);
      return 0;
    case 'i':
      CHECK_MAP_KEY("id", 2, STATE_ID_K);
      return 0;
    default:
      return 0;
  }
}

int StringCountCallbacks::OnEndMap(JsonParser* p) {
  printf("StringCountCallbacks::OnEndMap() %d\n", state_);
  return p->PopCallbacks() ? 1 : 0;
}

int StringCountCallbacks::OnStartArray(JsonParser* p) {
  printf("StringCountCallbacks::OnStartArray() %d\n", state_);
  return 0;
}

int StringCountCallbacks::OnEndArray(JsonParser* p) {
  printf("StringCountCallbacks::OnEndArray() %d\n", state_);
  return 0;
}


void Decode(Reader* src, Url* out_data, ErrorPtr* error) {
  JsonParser p;
  p.PushCallbacks(new UrlCallbacks(out_data));
  p.Decode(src, error);
}

UrlCallbacks::UrlCallbacks(Url* data)
    : data_(data),
      state_(STATE_NONE) {
}

int UrlCallbacks::OnNull(JsonParser* p) {
  printf("UrlCallbacks::OnNull()\n");
  return 0;
}

int UrlCallbacks::OnBool(JsonParser* p, bool value) {
  printf("UrlCallbacks::OnBool(%d) %d\n", value, state_);
  return 0;
}

int UrlCallbacks::OnNumber(JsonParser* p, const char* s, size_t length) {
  printf("UrlCallbacks::OnNumber(%.*s) %d\n", length, s, state_);
  return 0;
}

int UrlCallbacks::OnString(JsonParser* p, const unsigned char* s, size_t length) {
  printf("UrlCallbacks::OnString(%.*s) %d\n", length, s, state_);
  switch (state_) {
    case STATE_CREATED_K:
      SET_STRING_AND_RETURN(created);
    case STATE_ID_K:
      SET_STRING_AND_RETURN(id);
    case STATE_KIND_K:
      SET_STRING_AND_RETURN(kind);
    case STATE_LONGURL_K:
      SET_STRING_AND_RETURN(long_url);
    case STATE_STATUS_K:
      SET_STRING_AND_RETURN(status);
    default:
      return 0;
  }
}

int UrlCallbacks::OnStartMap(JsonParser* p) {
  printf("UrlCallbacks::OnStartMap() %d\n", state_);
  switch (state_) {
    case STATE_NONE:
      state_ = STATE_TOP;
      return 1;
    case STATE_ANALYTICS_K:
      PUSH_CALLBACK_REF_AND_RETURN(AnalyticsSummary, analytics);
    default:
      return 0;
  }
}

int UrlCallbacks::OnMapKey(JsonParser* p, const unsigned char* s, size_t length) {
  printf("UrlCallbacks::OnMapKey(%.*s) %d\n", length, s, state_);
  if (length == 0) return 0;
  switch (s[0]) {
    case 'a':
      CHECK_MAP_KEY("analytics", 9, STATE_ANALYTICS_K);
      return 0;
    case 'c':
      CHECK_MAP_KEY("created", 7, STATE_CREATED_K);
      return 0;
    case 'i':
      CHECK_MAP_KEY("id", 2, STATE_ID_K);
      return 0;
    case 'k':
      CHECK_MAP_KEY("kind", 4, STATE_KIND_K);
      return 0;
    case 'l':
      CHECK_MAP_KEY("longUrl", 7, STATE_LONGURL_K);
      return 0;
    case 's':
      CHECK_MAP_KEY("status", 6, STATE_STATUS_K);
      return 0;
    default:
      return 0;
  }
}

int UrlCallbacks::OnEndMap(JsonParser* p) {
  printf("UrlCallbacks::OnEndMap() %d\n", state_);
  return p->PopCallbacks() ? 1 : 0;
}

int UrlCallbacks::OnStartArray(JsonParser* p) {
  printf("UrlCallbacks::OnStartArray() %d\n", state_);
  return 0;
}

int UrlCallbacks::OnEndArray(JsonParser* p) {
  printf("UrlCallbacks::OnEndArray() %d\n", state_);
  return 0;
}


void Decode(Reader* src, UrlHistory* out_data, ErrorPtr* error) {
  JsonParser p;
  p.PushCallbacks(new UrlHistoryCallbacks(out_data));
  p.Decode(src, error);
}

UrlHistoryCallbacks::UrlHistoryCallbacks(UrlHistory* data)
    : data_(data),
      state_(STATE_NONE) {
}

int UrlHistoryCallbacks::OnNull(JsonParser* p) {
  printf("UrlHistoryCallbacks::OnNull()\n");
  return 0;
}

int UrlHistoryCallbacks::OnBool(JsonParser* p, bool value) {
  printf("UrlHistoryCallbacks::OnBool(%d) %d\n", value, state_);
  return 0;
}

int UrlHistoryCallbacks::OnNumber(JsonParser* p, const char* s, size_t length) {
  printf("UrlHistoryCallbacks::OnNumber(%.*s) %d\n", length, s, state_);
  char* endptr;
  char buffer[32];
  strncpy(&buffer[0], s, length);
  switch (state_) {
    case STATE_ITEMSPERPAGE_K:
      SET_INT32_AND_RETURN(items_per_page);
    case STATE_TOTALITEMS_K:
      SET_INT32_AND_RETURN(total_items);
    default:
      return 0;
  }
}

int UrlHistoryCallbacks::OnString(JsonParser* p, const unsigned char* s, size_t length) {
  printf("UrlHistoryCallbacks::OnString(%.*s) %d\n", length, s, state_);
  switch (state_) {
    case STATE_KIND_K:
      SET_STRING_AND_RETURN(kind);
    case STATE_NEXTPAGETOKEN_K:
      SET_STRING_AND_RETURN(next_page_token);
    default:
      return 0;
  }
}

int UrlHistoryCallbacks::OnStartMap(JsonParser* p) {
  printf("UrlHistoryCallbacks::OnStartMap() %d\n", state_);
  switch (state_) {
    case STATE_NONE:
      state_ = STATE_TOP;
      return 1;
    case STATE_ITEMS_A:
      PUSH_CALLBACK_REF_ARRAY_AND_RETURN(Url, items);
    default:
      return 0;
  }
}

int UrlHistoryCallbacks::OnMapKey(JsonParser* p, const unsigned char* s, size_t length) {
  printf("UrlHistoryCallbacks::OnMapKey(%.*s) %d\n", length, s, state_);
  if (length == 0) return 0;
  switch (s[0]) {
    case 'i':
      CHECK_MAP_KEY("itemsPerPage", 12, STATE_ITEMSPERPAGE_K);
      CHECK_MAP_KEY("items", 5, STATE_ITEMS_K);
      return 0;
    case 'k':
      CHECK_MAP_KEY("kind", 4, STATE_KIND_K);
      return 0;
    case 'n':
      CHECK_MAP_KEY("nextPageToken", 13, STATE_NEXTPAGETOKEN_K);
      return 0;
    case 't':
      CHECK_MAP_KEY("totalItems", 10, STATE_TOTALITEMS_K);
      return 0;
    default:
      return 0;
  }
}

int UrlHistoryCallbacks::OnEndMap(JsonParser* p) {
  printf("UrlHistoryCallbacks::OnEndMap() %d\n", state_);
  return p->PopCallbacks() ? 1 : 0;
}

int UrlHistoryCallbacks::OnStartArray(JsonParser* p) {
  printf("UrlHistoryCallbacks::OnStartArray() %d\n", state_);
  switch (state_) {
    case STATE_ITEMS_K:
      state_ = STATE_ITEMS_A;
      return 1;
    default:
      return 0;
  }
}

int UrlHistoryCallbacks::OnEndArray(JsonParser* p) {
  printf("UrlHistoryCallbacks::OnEndArray() %d\n", state_);
  switch (state_) {
    case STATE_ITEMS_A:
      state_ = STATE_TOP;
      return 1;
    default:
      return 0;
  }
}

