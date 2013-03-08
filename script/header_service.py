import cStringIO
import json

from easy_template import RunTemplateString
import gapi_utils
import service


HEADER_HEAD = """\
#ifndef {{include_guard}}
#define {{include_guard}}

#include <stdint.h>
#include <map>
#include <tr1/memory>
#include <vector>
#include <string>

#include "error.h"
#include "io.h"

[[if self.options.namespace:]]
namespace {{self.options.namespace}} {
[[]]

[[for schema in self.toplevel_schemas:]]
struct {{schema}};
[[]]

[[for schema in self.toplevel_schemas:]]
void Decode(Reader* src, {{schema}}* out_data, ErrorPtr* error);
void Encode(Writer* src, {{schema}}* data, ErrorPtr* error);
[[]]

"""

HEADER_FOOT = """\
[[if self.options.namespace:]]
}  // namespace {{self.options.namespace}}

[[]]
#endif  // {{include_guard}}
"""

HEADER_SCHEMA_HEAD = """\
struct {{schema_name}} {
"""

HEADER_SCHEMA_FOOT = """\
};

"""


def WriteWrappedComment(f, s, indent, length):
  lines = gapi_utils.WrapLine(s, length - (len(indent) + len('// ')))
  for line in lines:
    f.write('%s// %s\n' % (indent, line))


def WriteJsonComment(f, d, indent, length):
  for line in json.dumps(d, indent=2).splitlines():
    lines = gapi_utils.WrapLine(line, length - (len(indent) + len('// ')), True)
    for wrapped_line in lines:
      f.write('%s// %s\n' % (indent, wrapped_line))


class Service(service.Service):
  def __init__(self, service, outfname, options):
    self.f = cStringIO.StringIO()
    self.outfname = outfname
    self.options = options
    self.indent = ''
    self.prop_type = []
    self.schema_stack = []
    self.toplevel_schemas = []
    super(Service, self).__init__(service)

  def EndService(self, name, version):
    with open(self.outfname, 'w') as outf:
      include_guard = gapi_utils.MakeIncludeGuard(self.outfname)
      outf.write(RunTemplateString(HEADER_HEAD, vars()))
      outf.write(self.f.getvalue())
      outf.write(RunTemplateString(HEADER_FOOT, vars()))

  def BeginSchema(self, schema_name, schema):
    if not self.schema_stack:
      self.toplevel_schemas.append(schema_name)
    self.schema_stack.append(schema_name)
    self.f.write(RunTemplateString(HEADER_SCHEMA_HEAD, vars(),
                                   output_indent=self.indent))
    self.indent += '  '

  def EndSchema(self, schema_name, schema):
    WriteJsonComment(self.f, schema, self.indent, 80)
    self.indent = self.indent[:-2]
    self.f.write(RunTemplateString(HEADER_SCHEMA_FOOT, vars(),
                                   output_indent=self.indent))
    self.schema_stack.pop()

  def BeginProperty(self, prop_name, prop):
    self.prop_type = ''

  def EndProperty(self, prop_name, prop):
    self.f.write('%s%s %s;\n\n' % (
        self.indent,
        self.prop_type,
        gapi_utils.SnakeCase(prop_name)))

  def OnPropertyComment(self, prop_name, prop, comment):
    for line in comment.splitlines():
      WriteWrappedComment(self.f, line, self.indent, 80)

  def OnPropertyTypeRef(self, prop_name, prop, ref):
    self.prop_type = gapi_utils.WrapType('std::tr1::shared_ptr<%s>', ref)

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    self.prop_type = service.TYPE_DICT[(prop_type, prop_format)]

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    self.prop_type = gapi_utils.WrapType('std::vector<%s>', self.prop_type)

  def BeginPropertyTypeObject(self, prop_name, prop):
    return gapi_utils.CapWords(prop_name + 'Object')

  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    self.prop_type = schema_name
