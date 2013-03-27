from easy_template import RunTemplateString
import gapi_utils
import service


def Generate(outf, service, **kwargs):
  namespace = kwargs['namespace']
  header_name = kwargs['header_name']
  include_guard = gapi_utils.MakeIncludeGuard(header_name)
  outf.write(RunTemplateString(HEADER_HEAD, vars()))
  for schema in service.schemas.itervalues():
    _GenerateSchema(outf, schema)
    outf.write('\n')
  outf.write(RunTemplateString(HEADER_FOOT, vars()))


def _GenerateSchema(outf, schema):
  service.Iterate(schema, GenerateSchemaCallbacks(outf))


def WriteWrappedComment(f, s, indent, length):
  lines = gapi_utils.WrapLine(s, length - (len(indent) + len('// ')))
  for line in lines:
    f.write('%s// %s\n' % (indent, line))


def WriteJsonComment(f, d, indent, length):
  for line in json.dumps(d, indent=2).splitlines():
    lines = gapi_utils.WrapLine(line, length - (len(indent) + len('// ')), True)
    for wrapped_line in lines:
      f.write('%s// %s\n' % (indent, wrapped_line))


class GenerateSchemaCallbacks(service.ServiceCallbacks):
  def __init__(self, outf):
    self.outf = outf

  def GetIndentFromContext(self, context):
    indent = ''
    for item in context:
      if isinstance(item, service.Schema):
        indent += '  '
    return indent

  def GetIndent(self, obj):
    return self.GetIndentFromContext(obj.GetContext())

  def GetPrevIndent(self, obj):
    return self.GetIndentFromContext(obj.GetContext()[:-1])

  def BeginSchema(self, schema):
    self.outf.write(RunTemplateString(HEADER_SCHEMA_HEAD, vars(),
                                      output_indent=self.GetPrevIndent(schema)))

  def EndSchema(self, schema):
    self.outf.write(RunTemplateString(HEADER_SCHEMA_FOOT, vars(),
                                      output_indent=self.GetPrevIndent(schema)))

  def EndProperty(self, prop):
    indent = self.GetIndent(prop)
    self.outf.write('\n')
    for line in prop.description.splitlines():
      WriteWrappedComment(self.outf, line, indent, 80)

    ctype = prop.ctype
    if prop.is_additional_properties:
      self.outf.write('%stypedef %s %s;\n' % (
          indent,
          prop.ctype,
          prop.base_ctypedef))
      ctype = prop.base_ctypedef

    self.outf.write('%s%s %s;\n' % (
        indent,
        ctype,
        prop.base_cident))


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

class JsonGeneratorOptions;

[[if namespace:]]
namespace {{namespace}} {
[[]]

[[for _, schema in sorted(service.schemas.iteritems()):]]
struct {{schema.ctype}};
[[]]

[[for _, schema in sorted(service.schemas.iteritems()):]]
void Decode(Reader* src, {{schema.ctype}}* out_data, ErrorPtr* error);
void Encode(Writer* src, {{schema.ctype}}* data, const JsonGeneratorOptions& options, ErrorPtr* error);
[[]]

"""

HEADER_FOOT = """\
[[if namespace:]]
}  // namespace {{namespace}}

[[]]
#endif  // {{include_guard}}
"""

HEADER_SCHEMA_HEAD = """\
struct {{schema.base_ctype}} {
  {{schema.base_ctype}}();
  ~{{schema.base_ctype}}();
"""

HEADER_SCHEMA_FOOT = """\
};
"""
