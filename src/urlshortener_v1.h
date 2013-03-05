#ifndef URLSHORTENER_V1_H_
#define URLSHORTENER_V1_H_

#include <map>
#include <tr1/memory>
#include <vector>
#include <string>

#include "error.h"
#include "io.h"

struct AnalyticsSnapshot;
struct AnalyticsSummary;
struct StringCount;
struct Url;
struct UrlHistory;

void Decode(Reader* src, AnalyticsSnapshot* out_data, ErrorPtr* error);
void Decode(Reader* src, AnalyticsSummary* out_data, ErrorPtr* error);
void Decode(Reader* src, StringCount* out_data, ErrorPtr* error);
void Decode(Reader* src, Url* out_data, ErrorPtr* error);
void Decode(Reader* src, UrlHistory* out_data, ErrorPtr* error);

struct AnalyticsSnapshot {
  // Top browsers, e.g. "Chrome"; sorted by (descending) click counts. Only
  // present if this data is available.
  std::vector<std::tr1::shared_ptr<StringCount> > browsers;

  // Top countries (expressed as country codes), e.g. "US" or "DE"; sorted by
  // (descending) click counts. Only present if this data is available.
  std::vector<std::tr1::shared_ptr<StringCount> > countries;

  // Number of clicks on all goo.gl short URLs pointing to this long URL.
  int64_t long_url_clicks;

  // Top platforms or OSes, e.g. "Windows"; sorted by (descending) click counts.
  // Only present if this data is available.
  std::vector<std::tr1::shared_ptr<StringCount> > platforms;

  // Top referring hosts, e.g. "www.google.com"; sorted by (descending) click
  // counts. Only present if this data is available.
  std::vector<std::tr1::shared_ptr<StringCount> > referrers;

  // Number of clicks on this short URL.
  int64_t short_url_clicks;

  // {
  //   "type": "object", 
  //   "id": "AnalyticsSnapshot", 
  //   "properties": {
  //     "shortUrlClicks": {
  //       "type": "string", 
  //       "description": "Number of clicks on this short URL.", 
  //       "format": "int64"
  //     }, 
  //     "countries": {
  //       "items": {
  //         "$ref": "StringCount"
  //       }, 
  //       "type": "array", 
  //       "description": "Top countries (expressed as country codes), e.g.
  //           \"US\" or \"DE\"; sorted by (descending) click counts. Only
  //           present if this data is available."
  //     }, 
  //     "platforms": {
  //       "items": {
  //         "$ref": "StringCount"
  //       }, 
  //       "type": "array", 
  //       "description": "Top platforms or OSes, e.g. \"Windows\"; sorted by
  //           (descending) click counts. Only present if this data is
  //           available."
  //     }, 
  //     "browsers": {
  //       "items": {
  //         "$ref": "StringCount"
  //       }, 
  //       "type": "array", 
  //       "description": "Top browsers, e.g. \"Chrome\"; sorted by (descending)
  //           click counts. Only present if this data is available."
  //     }, 
  //     "referrers": {
  //       "items": {
  //         "$ref": "StringCount"
  //       }, 
  //       "type": "array", 
  //       "description": "Top referring hosts, e.g. \"www.google.com\"; sorted
  //           by (descending) click counts. Only present if this data is
  //           available."
  //     }, 
  //     "longUrlClicks": {
  //       "type": "string", 
  //       "description": "Number of clicks on all goo.gl short URLs pointing to
  //           this long URL.",
  //       "format": "int64"
  //     }
  //   }
  // }
};

struct AnalyticsSummary {
  // Click analytics over all time.
  std::tr1::shared_ptr<AnalyticsSnapshot> all_time;

  // Click analytics over the last day.
  std::tr1::shared_ptr<AnalyticsSnapshot> day;

  // Click analytics over the last month.
  std::tr1::shared_ptr<AnalyticsSnapshot> month;

  // Click analytics over the last two hours.
  std::tr1::shared_ptr<AnalyticsSnapshot> two_hours;

  // Click analytics over the last week.
  std::tr1::shared_ptr<AnalyticsSnapshot> week;

  // {
  //   "type": "object", 
  //   "id": "AnalyticsSummary", 
  //   "properties": {
  //     "week": {
  //       "description": "Click analytics over the last week.", 
  //       "$ref": "AnalyticsSnapshot"
  //     }, 
  //     "allTime": {
  //       "description": "Click analytics over all time.", 
  //       "$ref": "AnalyticsSnapshot"
  //     }, 
  //     "twoHours": {
  //       "description": "Click analytics over the last two hours.", 
  //       "$ref": "AnalyticsSnapshot"
  //     }, 
  //     "day": {
  //       "description": "Click analytics over the last day.", 
  //       "$ref": "AnalyticsSnapshot"
  //     }, 
  //     "month": {
  //       "description": "Click analytics over the last month.", 
  //       "$ref": "AnalyticsSnapshot"
  //     }
  //   }
  // }
};

struct StringCount {
  // Number of clicks for this top entry, e.g. for this particular country or
  // browser.
  int64_t count;

  // Label assigned to this top entry, e.g. "US" or "Chrome".
  std::string id;

  // {
  //   "type": "object", 
  //   "id": "StringCount", 
  //   "properties": {
  //     "count": {
  //       "type": "string", 
  //       "description": "Number of clicks for this top entry, e.g. for this
  //           particular country or browser.",
  //       "format": "int64"
  //     }, 
  //     "id": {
  //       "type": "string", 
  //       "description": "Label assigned to this top entry, e.g. \"US\" or
  //           \"Chrome\"."
  //     }
  //   }
  // }
};

struct Url {
  // A summary of the click analytics for the short and long URL. Might not be
  // present if not requested or currently unavailable.
  std::tr1::shared_ptr<AnalyticsSummary> analytics;

  // Time the short URL was created; ISO 8601 representation using the
  // yyyy-MM-dd'T'HH:mm:ss.SSSZZ format, e.g. "2010-10-14T19:01:24.944+00:00".
  std::string created;

  // Short URL, e.g. "http://goo.gl/l6MS".
  std::string id;

  // The fixed string "urlshortener#url".
  std::string kind;

  // Long URL, e.g. "http://www.google.com/". Might not be present if the status
  // is "REMOVED".
  std::string long_url;

  // Status of the target URL. Possible values: "OK", "MALWARE", "PHISHING", or
  // "REMOVED". A URL might be marked "REMOVED" if it was flagged as spam, for
  // example.
  std::string status;

  // {
  //   "type": "object", 
  //   "id": "Url", 
  //   "properties": {
  //     "status": {
  //       "type": "string", 
  //       "description": "Status of the target URL. Possible values: \"OK\",
  //           \"MALWARE\", \"PHISHING\", or \"REMOVED\". A URL might be marked
  //           \"REMOVED\" if it was flagged as spam, for example."
  //     }, 
  //     "kind": {
  //       "default": "urlshortener#url", 
  //       "type": "string", 
  //       "description": "The fixed string \"urlshortener#url\"."
  //     }, 
  //     "created": {
  //       "type": "string", 
  //       "description": "Time the short URL was created; ISO 8601
  //           representation using the yyyy-MM-dd'T'HH:mm:ss.SSSZZ format, e.g.
  //           \"2010-10-14T19:01:24.944+00:00\"."
  //     }, 
  //     "analytics": {
  //       "description": "A summary of the click analytics for the short and
  //           long URL. Might not be present if not requested or currently
  //           unavailable.",
  //       "$ref": "AnalyticsSummary"
  //     }, 
  //     "longUrl": {
  //       "type": "string", 
  //       "description": "Long URL, e.g. \"http://www.google.com/\". Might not
  //           be present if the status is \"REMOVED\"."
  //     }, 
  //     "id": {
  //       "type": "string", 
  //       "description": "Short URL, e.g. \"http://goo.gl/l6MS\"."
  //     }
  //   }
  // }
};

struct UrlHistory {
  // A list of URL resources.
  std::vector<std::tr1::shared_ptr<Url> > items;

  // Number of items returned with each full "page" of results. Note that the
  // last page could have fewer items than the "itemsPerPage" value.
  int32_t items_per_page;

  // The fixed string "urlshortener#urlHistory".
  std::string kind;

  // A token to provide to get the next page of results.
  std::string next_page_token;

  // Total number of short URLs associated with this user (may be approximate).
  int32_t total_items;

  // {
  //   "type": "object", 
  //   "id": "UrlHistory", 
  //   "properties": {
  //     "nextPageToken": {
  //       "type": "string", 
  //       "description": "A token to provide to get the next page of results."
  //     }, 
  //     "items": {
  //       "items": {
  //         "$ref": "Url"
  //       }, 
  //       "type": "array", 
  //       "description": "A list of URL resources."
  //     }, 
  //     "kind": {
  //       "default": "urlshortener#urlHistory", 
  //       "type": "string", 
  //       "description": "The fixed string \"urlshortener#urlHistory\"."
  //     }, 
  //     "itemsPerPage": {
  //       "type": "integer", 
  //       "description": "Number of items returned with each full \"page\" of
  //           results. Note that the last page could have fewer items than the
  //           \"itemsPerPage\" value.",
  //       "format": "int32"
  //     }, 
  //     "totalItems": {
  //       "type": "integer", 
  //       "description": "Total number of short URLs associated with this user
  //           (may be approximate).",
  //       "format": "int32"
  //     }
  //   }
  // }
};

#endif  // URLSHORTENER_V1_H_
