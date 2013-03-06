#include "gtest/gtest.h"
#include "io.h"
#include "json_parser.h"
#include "out/gen/src/test/data/simple_schema.h"
#include "out/gen/src/test/data/urlshortener_schema.h"
#include "out/gen/src/test/data/test_types_schema.h"

TEST(SimpleSchemaTest, TestParse) {
  simple_schema::StringCount data;
  char buffer[] = "{\"id\": \"foobar\", \"count\": \"123456\"}";
  MemoryReader reader(&buffer[0], strlen(buffer));
  ErrorPtr error;
  simple_schema::Decode(&reader, &data, &error);
  ASSERT_EQ(NULL, error.get()) << "Decode error: " << error->ToString();
  EXPECT_STREQ("foobar", data.id.c_str());
  EXPECT_EQ(123456, data.count);
}

TEST(UrlshortenerSchemaTest, TestParse) {
  urlshortener_schema::Url data;
  FileReader reader("urlshortener_response.json");
  ErrorPtr error;
  urlshortener_schema::Decode(&reader, &data, &error);
  ASSERT_EQ(NULL, error.get()) << "Decode error: " << error->ToString();

  // Test a few values...
  ASSERT_TRUE(data.analytics.get() != NULL);
  ASSERT_TRUE(data.analytics->all_time.get() != NULL);
  ASSERT_EQ(10073, data.analytics->all_time->short_url_clicks);
  ASSERT_EQ(10, data.analytics->all_time->referrers.size());
  EXPECT_STREQ("www.google.com",
               data.analytics->all_time->referrers[6]->id.c_str());
  ASSERT_EQ(10, data.analytics->all_time->browsers.size());
  EXPECT_STREQ("Chrome", data.analytics->all_time->browsers[0]->id.c_str());
}

TEST(TypesTest, TestParse) {
  test_types_schema::Types data;
  FileReader reader("test_types_data.json");
  ErrorPtr error;
  test_types_schema::Decode(&reader, &data, &error);
  ASSERT_EQ(NULL, error.get()) << "Decode error: " << error->ToString();

  EXPECT_EQ(-1234, data.my_int32);
  EXPECT_EQ(1234, data.my_uint32);
  EXPECT_EQ(-3123456789, data.my_int64);
  EXPECT_EQ(13123456789, data.my_uint64);
  EXPECT_FLOAT_EQ(14.5, data.my_float);
  EXPECT_DOUBLE_EQ(1e24, data.my_double);
  EXPECT_STREQ("Hello, World!", data.my_string.c_str());
  EXPECT_EQ(true, data.my_bool);
  ASSERT_TRUE(data.my_ref.get() != NULL);
  EXPECT_STREQ("Goodbye, moon.", data.my_ref->value1.c_str());
  EXPECT_EQ(8675309, data.my_ref->value2);
  EXPECT_STREQ("Hi, rock?", data.my_object.my_object_string.c_str());
  EXPECT_FLOAT_EQ(3.14159, data.my_object.my_object_float);
}

TEST(TypesTest, TestFailures) {
  struct TestCase {
    const char* json;
    const char* error;
  };
  TestCase test_cases[] = {
    { "{\"myInt32\": \"\"}", "Unexpected string" },
    { "{\"myInt32\": 3.5}", "Error parsing integer" },
    { "{\"myInt32\": 123456789012}", "Error parsing integer" },
  };

  for (int i = 0; i < sizeof(test_cases)/sizeof(test_cases[0]); ++i) {
    const char* json = test_cases[i].json;
    test_types_schema::Types data;
    MemoryReader reader(&json[0], strlen(json));
    ErrorPtr error;
    test_types_schema::Decode(&reader, &data, &error);
    ASSERT_TRUE(error.get() != NULL) << "Expected error for testcase: " << json;
    EXPECT_STREQ(test_cases[i].error, error->ToString().c_str())
        << "Testcase: " << json;
  }
}

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
