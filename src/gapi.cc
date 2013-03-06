#include "ppapi/cpp/instance.h"
#include "ppapi/cpp/module.h"
#include "ppapi/cpp/var.h"
#include <stdio.h>
#include <string.h>

#if 0
#include "json_parser.h"
#include "urlshortener_v1.h"
#endif

class Instance : public pp::Instance {
 public:
  explicit Instance(PP_Instance instance)
      : pp::Instance(instance) {
#if 0
    Url data;
    char buffer[] = "{\n \"kind\": \"urlshortener#url\",\n \"id\": \"http://goo.gl/Lv6ph\",\n \"longUrl\": \"http://googlecode.blogspot.com/2011/01/google-url-shortener-gets-api.html\",\n \"status\": \"OK\",\n \"analytics\": {\n  \"allTime\": {\n   \"shortUrlClicks\": \"10072\",\n   \"longUrlClicks\": \"10747\"\n  },\n  \"month\": {\n   \"shortUrlClicks\": \"113\",\n   \"longUrlClicks\": \"113\"\n  },\n  \"week\": {\n   \"shortUrlClicks\": \"4\",\n   \"longUrlClicks\": \"4\"\n  },\n  \"day\": {\n   \"shortUrlClicks\": \"0\",\n   \"longUrlClicks\": \"0\"\n  },\n  \"twoHours\": {\n   \"shortUrlClicks\": \"0\",\n   \"longUrlClicks\": \"0\"\n  }\n }\n}\n";
    MemoryReader src(&buffer[0], strlen(buffer));
    ErrorPtr error;
    Decode(&src, &data, &error);
    if (error) {
      printf("%s\n", error->ToString().c_str());
    }
#endif
  }
};

class Module : public pp::Module {
 public:
  virtual pp::Instance* CreateInstance(PP_Instance instance) {
    return new Instance(instance);
  }
};

namespace pp {
Module* CreateModule() {
  return new ::Module();
}
}  // namespace pp
