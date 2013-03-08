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
    { "{\"myInt32\": 3.5}", "Unexpected characters at end of integer" },
    { "{\"myInt32\": 123456789012}", "Integer value out of range" },
    { "{\"myUint32\": -1}", "Integer value out of range" },
    { "{\"myInt64\": foo}", "invalid string in json text" },
    { "{\"myInt64\": 1234}", "Unexpected number" },
    { "{\"myInt64\": \"1234a\"}", "Unexpected characters at end of integer" },
    { "{\"myInt64\": \"1234.5\"}", "Unexpected characters at end of integer" },
    { "{\"myInt64\": \"10000000000000000000\"}", "Integer value out of range" },
    // strtoull parses -1 as a valid uint64 (ULLONG_MAX). :-/
//    { "{\"myUint64\": \"-1\"}", "Integer value out of range" },
    { "{\"myFloat\": \"1.5\"}", "Unexpected string" },
    { "{\"myFloat\": 1e40}", "Float value out of range" },
    { "{\"myDouble\": 1e400}", "Float value out of range" },
    { "{\"myString\": true}", "Unexpected bool" },
    { "{\"myBool\": 1}", "Unexpected number" },
    { "{\"myBool\": \"true\"}", "Unexpected string" },
    { "{\"myRef\": null}", "Unexpected null" },
    { "{\"myObject\": null}", "Unexpected null" },
    { "{\"myObject\": {\"badProperty\": 123}}", "Unknown map key" },
  };

  for (int i = 0; i < sizeof(test_cases)/sizeof(test_cases[0]); ++i) {
    const char* json = test_cases[i].json;
    test_types_schema::Types data;
    MemoryReader reader(&json[0], strlen(json));
    ErrorPtr error;
    test_types_schema::Decode(&reader, &data, &error);
    const char* error_message = error ? error->ToString().c_str() : "None";
    EXPECT_TRUE(strstr(error_message, test_cases[i].error) != NULL)
        << "For testcase: " << json << "\n"
        << "Expected error to be: " << test_cases[i].error << "\n"
        << "Actual error: " << error_message;
  }
}

TEST(ArrayTypesTest, TestParse) {
  test_types_schema::ArrayTypes data;
  FileReader reader("test_array_types_data.json");
  ErrorPtr error;
  test_types_schema::Decode(&reader, &data, &error);
  ASSERT_EQ(NULL, error.get()) << "Decode error: " << error->ToString();

  ASSERT_EQ(2, data.my_int32_array.size());
  ASSERT_EQ(3, data.my_uint32_array.size());
  ASSERT_EQ(1, data.my_int64_array.size());
  ASSERT_EQ(0, data.my_uint64_array.size());
  ASSERT_EQ(3, data.my_float_array.size());
  ASSERT_EQ(3, data.my_double_array.size());
  ASSERT_EQ(3, data.my_string_array.size());
  ASSERT_EQ(3, data.my_bool_array.size());
  ASSERT_EQ(2, data.my_ref_array.size());
  ASSERT_EQ(3, data.my_object_array.size());

  EXPECT_EQ(-1234, data.my_int32_array[0]);
  EXPECT_EQ(456, data.my_int32_array[1]);
  EXPECT_EQ(1234, data.my_uint32_array[0]);
  EXPECT_EQ(45100, data.my_uint32_array[1]);
  EXPECT_EQ(23, data.my_uint32_array[2]);
  EXPECT_EQ(-3123456789, data.my_int64_array[0]);
  EXPECT_FLOAT_EQ(1.0, data.my_float_array[0]);
  EXPECT_FLOAT_EQ(2.0, data.my_float_array[1]);
  EXPECT_FLOAT_EQ(3.0, data.my_float_array[2]);
  EXPECT_DOUBLE_EQ(-5.6, data.my_double_array[0]);
  EXPECT_DOUBLE_EQ(4.5, data.my_double_array[1]);
  EXPECT_DOUBLE_EQ(100.3, data.my_double_array[2]);
  EXPECT_FALSE(data.my_bool_array[0]);
  EXPECT_FALSE(data.my_bool_array[1]);
  EXPECT_TRUE(data.my_bool_array[2]);
  ASSERT_TRUE(data.my_ref_array[0].get() != NULL);
  ASSERT_TRUE(data.my_ref_array[1].get() != NULL);
  EXPECT_STREQ("First", data.my_ref_array[0]->value1.c_str());
  EXPECT_EQ(1, data.my_ref_array[0]->value2);
  EXPECT_STREQ("Second", data.my_ref_array[1]->value1.c_str());
  EXPECT_EQ(2, data.my_ref_array[1]->value2);
  EXPECT_STREQ("1234", data.my_object_array[0].my_object_string.c_str());
  EXPECT_FLOAT_EQ(1234, data.my_object_array[0].my_object_float);
  EXPECT_STREQ("45.3", data.my_object_array[1].my_object_string.c_str());
  EXPECT_FLOAT_EQ(45.3, data.my_object_array[1].my_object_float);
  EXPECT_STREQ("1e9", data.my_object_array[2].my_object_string.c_str());
  EXPECT_FLOAT_EQ(1e9, data.my_object_array[2].my_object_float);
}

TEST(ArrayTypesTest, TestFailures) {
  struct TestCase {
    const char* json;
    const char* error;
  };
  TestCase test_cases[] = {
    { "{\"myInt32Array\": [32, \"\"]}", "Unexpected string" },
    { "{\"myInt32Array\": [3.5]}", "Unexpected characters at end of integer" },
    { "{\"myInt32Array\": null}", "Unexpected null" },
    // TODO(binji): better error for this: "int64 expects numbers in strings..."
    { "{\"myInt64Array\": [\"1234\", 1234]}", "Unexpected number" },
    { "{\"myBoolArray\": [true, false, 1]}", "Unexpected number" },
  };

  for (int i = 0; i < sizeof(test_cases)/sizeof(test_cases[0]); ++i) {
    const char* json = test_cases[i].json;
    test_types_schema::ArrayTypes data;
    MemoryReader reader(&json[0], strlen(json));
    ErrorPtr error;
    test_types_schema::Decode(&reader, &data, &error);
    const char* error_message = error ? error->ToString().c_str() : "None";
    EXPECT_TRUE(strstr(error_message, test_cases[i].error) != NULL)
        << "For testcase: " << json << "\n"
        << "Expected error to be: " << test_cases[i].error << "\n"
        << "Actual error: " << error_message;
  }
}

TEST(ComplexTypesTest, TestParse) {
  const char* test_cases[] = {
    "{\"twoply\": []}",
    "{\"twoply\": [[]]}",
    "{\"twoply\": [[], [], [], [], []]}",
    "{\"twoply\": [[1, 2]]}",
    "{\"twoply\": [[1, 2], []]}",
    "{\"twoply\": [[1, 2], [3, 4]]}",
    "{\"twoply\": [[1], [3], [5], [7]]}",
    "{\"threeply\": []}",
    "{\"threeply\": [[]]}",
    "{\"threeply\": [[[]]]}",
    "{\"threeply\": [[],[]]}",
    "{\"threeply\": [[],[],[[]]]}",
    "{\"threeply\": [[[1],[2],[3]],[[4],[5],[6]],[[7],[8],[9]]]}",
    "{\"twoplyObjects\": [[{\"x\": 1}]]}",
    "{\"twoplyObjects\": [[{\"x\": 1}, {\"x\": 2}]]}",
    "{\"twoplyObjects\": [[{\"x\": 1}, {\"x\": 2}], [{\"x\": 3}]]}",
    "{\"twoplyRefs\": [[{\"value1\": \"foo\"}]]}",
    "{\"twoplyRefs\": [[{\"value2\": 1}, {\"value1\": \"2\"}]]}",
    "{\"twoplyRefs\": [[{\"value1\": \"1\", \"value2\": 2}], [{\"value2\": 2}]]}",
    "{\"arrayOfNested\": []}",
    "{\"arrayOfNested\": [{\"x\": {\"y\": 1}}]}",
    "{\"arrayOfNested\": [{\"x\": {\"y\": 1}}, {\"x\": {\"y\": 2}}]}",
  };

  for (int i = 0; i < sizeof(test_cases)/sizeof(test_cases[0]); ++i) {
    const char* json = test_cases[i];
    test_types_schema::ComplexTypes data;
    MemoryReader reader(&json[0], strlen(json));
    ErrorPtr error;
    test_types_schema::Decode(&reader, &data, &error);
    EXPECT_TRUE(error.get() == NULL)
        << "For testcase: " << json << "\n"
        << "Got error: " << error->ToString();
  }
}

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
