import cpp_json_constructor_generator
import cpp_json_decoder_generator
import cpp_json_encoder_generator
from easy_template import RunTemplateString


def Generate(outf, s, **kwargs):
  outf.write(RunTemplateString(SOURCE_HEAD, kwargs))
  cpp_json_constructor_generator.Generate(outf, s)
  cpp_json_decoder_generator.Generate(outf, s)
  cpp_json_encoder_generator.Generate(outf, s)
  outf.write(RunTemplateString(SOURCE_FOOT, kwargs))


SOURCE_HEAD = """\
#include "{{header_name}}"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits>
#include <vector>
#include "json_generator.h"
#include "json_parser.h"
#include "json_parser_macros.h"


[[if namespace:]]
namespace {{namespace}} {

static const size_t kMaxNumberBufferSize = 32;

[[]]
"""

SOURCE_FOOT = """\
[[if namespace:]]
}  // namespace {{namespace}}
[[]]
"""
