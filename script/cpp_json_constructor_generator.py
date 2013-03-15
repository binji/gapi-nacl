from easy_template import RunTemplateString
import gapi_utils
import service


def Generate(outf, service):
  for typ, data in service.Generator():
    if typ == 'BeginSchema':
      _GenerateSchema(outf, data)


def _GenerateSchema(outf, schema):
  outf.write(RunTemplateString(TEMPLATE_BEGIN_SCHEMA, vars()))
  for prop in schema.properties.itervalues():
    prop_type = prop.prop_type
    cident = gapi_utils.SnakeCase(prop.name)
    outf.write(RunTemplateString(TEMPLATE_PRIMITIVE, vars()))
  outf.write(RunTemplateString(TEMPLATE_END_SCHEMA, vars()))


def CIdentFromContext(context):
  cident = ''
  index_var = None
  for item in context:
    if isinstance(item, service.Property):
      cident += item.base_cident
    elif isinstance(item, service.ObjectPropertyType):
      cident += '.'
  return cident


TEMPLATE_BEGIN_SCHEMA = """\
{{schema.ctype}}::{{schema.base_ctype}}() {
"""

TEMPLATE_END_SCHEMA = """\
}

{{schema.ctype}}::~{{schema.base_ctype}}() {
}

"""

TEMPLATE_PRIMITIVE = """\
[[if not prop_type.is_parent_array:]]
[[  if prop_type.ctype == 'bool':]]
  {{cident}} = false;
[[  elif prop_type.ctype in ('int32_t', 'uint32_t', 'int64_t', 'uint64_t'):]]
  {{cident}} = 0;
[[  elif prop_type.ctype in ('float', 'double'):]]
  {{cident}} = 0;
[[]]
"""
