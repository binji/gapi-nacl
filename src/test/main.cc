#include "gtest/gtest.h"
#include "io.h"
#include "json_parser.h"
#include "out/gen/src/test/data/schema1.h"
#include "out/gen/src/test/data/schema2.h"
#include "out/gen/src/test/data/schema3.h"

TEST(GenTest1, TestParse) {
  schema1::StringCount data;
  char buffer[] = "{\"id\": \"foobar\", \"count\": \"123456\"}";
  MemoryReader reader(&buffer[0], strlen(buffer));
  ErrorPtr error;
  schema1::Decode(&reader, &data, &error);
  ASSERT_EQ(NULL, error.get()) << "Decode error: " << error->ToString();
  EXPECT_STREQ("foobar", data.id.c_str());
  EXPECT_EQ(123456, data.count);
}

TEST(GenTest2, TestParse) {
  schema2::Url data;
  FileReader reader("test2_response.json");
  ErrorPtr error;
  schema2::Decode(&reader, &data, &error);
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

TEST(GenTest3, TestTypes) {
  schema3::Types data;
  FileReader reader("test3_types1.json");
  ErrorPtr error;
  schema3::Decode(&reader, &data, &error);
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

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
