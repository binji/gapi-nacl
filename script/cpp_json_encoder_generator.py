from easy_template import RunTemplateString
import gapi_utils
import service


def Generate(outf, service):
  for schema in service.schemas.itervalues():
    _GenerateSchemaDeclaration(outf, schema)
  for schema in service.schemas.itervalues():
    _GenerateSchemaThunkDefinition(outf, schema)
  for schema in service.schemas.itervalues():
    _GenerateSchemaDefinition(outf, schema)


def _GenerateSchemaDeclaration(outf, schema):
  outf.write(RunTemplateString(TEMPLATE_DECLARE_SCHEMA, vars()))

def _GenerateSchemaThunkDefinition(outf, schema):
  outf.write(RunTemplateString(TEMPLATE_DEFINE_SCHEMA_THUNK, vars()))

def _GenerateSchemaDefinition(outf, schema):
  service.Iterate(schema, GenerateSchemaCallbacks(outf))


def _IncrementIndexVar(index_var):
  if index_var:
    return chr(ord(index_var) + 1)
  else:
    return 'i'


class GenerateSchemaCallbacks(service.ServiceCallbacks):
  def __init__(self, outf):
    self.outf = outf

  def CIdentFromContext(self, context):
    cident = 'data->'
    index_var = None
    iter_var = None
    prev_item = None
    for item in context:
      if isinstance(prev_item, service.Property):
        if prev_item.is_additional_properties:
          index_var = _IncrementIndexVar(index_var)
          cident = '%s->second' % index_var
      if isinstance(item, service.Property):
        cident += item.base_cident
      elif isinstance(item, service.ArrayPropertyType):
        index_var = _IncrementIndexVar(index_var)
        cident += '[%s]' % index_var
      elif isinstance(item, service.ObjectPropertyType):
        cident += '.'
      prev_item = item
    return cident

  def IndexVarFromContext(self, context):
    index_var = None
    for item in context:
      if (isinstance(item, service.ArrayPropertyType) or
          (isinstance(item, service.Property) and
           item.is_additional_properties)):
        index_var = _IncrementIndexVar(index_var)
    return index_var

  def IndentFromContext(self, context):
    indent = ''
    for item in context:
      if isinstance(item, service.ArrayPropertyType):
        indent += '  '
      elif isinstance(item, service.Property) and item.is_additional_properties:
        indent += '  '
    return indent

  def GetPropKeyAndLen(self, prop):
    if prop.is_additional_properties:
      index_var = self.IndexVarFromContext(prop.GetContext())
      return ('%s->first.c_str()' % index_var,
              '%s->first.length()' % index_var)
    return '"%s"' % prop.name, str(len(prop.name))

  def BeginSchema(self, schema):
    if not schema.parent_schema:
      self.outf.write(RunTemplateString(TEMPLATE_BEGIN_SCHEMA, vars()))

  def EndSchema(self, schema):
    if not schema.parent_schema:
      self.outf.write(RunTemplateString(TEMPLATE_END_SCHEMA, vars()))

  def BeginProperty(self, prop):
    if prop.is_additional_properties:
      cident = self.CIdentFromContext(prop.GetContext())
      indent = self.IndentFromContext(prop.schema.GetContext())
      index_var = self.IndexVarFromContext(prop.GetContext())
      self.outf.write(RunTemplateString(TEMPLATE_BEGIN_ADDL_PROPS, vars(),
                                        output_indent=indent))

  def EndProperty(self, prop):
    if prop.is_additional_properties:
      indent = self.IndentFromContext(prop.schema.GetContext())
      self.outf.write(RunTemplateString(TEMPLATE_END_ADDL_PROPS, vars(),
                                        output_indent=indent))

  def PrimitivePropertyType(self, prop_type):
    context = prop_type.GetContext()
    indent = self.IndentFromContext(context)
    cident = self.CIdentFromContext(prop_type.GetContext())
    prop_key, prop_key_len = self.GetPropKeyAndLen(prop_type.prop)
    self.outf.write(RunTemplateString(TEMPLATE_PRIMITIVE_HEADER, vars(),
                                      output_indent=indent))
    type_macro = TYPE_MACRO_DICT[prop_type.type_format]
    if type_macro == 'String':
      self.outf.write(RunTemplateString(TEMPLATE_PRIMITIVE_STRING, vars(),
                                        output_indent=indent))
    else:
      self.outf.write(RunTemplateString(TEMPLATE_PRIMITIVE_NON_STRING, vars(),
                                        output_indent=indent))

  def BeginArrayPropertyType(self, prop_type):
    context = prop_type.GetPrevContext()
    indent = self.IndentFromContext(context)
    cident = self.CIdentFromContext(context)
    prop_key, prop_key_len = self.GetPropKeyAndLen(prop_type.prop)
    index_var = self.IndexVarFromContext(prop_type.GetContext())
    self.outf.write(RunTemplateString(TEMPLATE_BEGIN_ARRAY, vars(),
                                      output_indent=indent))

  def EndArrayPropertyType(self, prop_type):
    indent = self.IndentFromContext(prop_type.GetPrevContext())
    self.outf.write(RunTemplateString(TEMPLATE_END_ARRAY, vars(),
                                      output_indent=indent))

  def BeginObjectPropertyType(self, prop_type):
    indent = self.IndentFromContext(prop_type.GetContext())
    prop_key, prop_key_len = self.GetPropKeyAndLen(prop_type.prop)
    self.outf.write(RunTemplateString(TEMPLATE_BEGIN_OBJECT, vars(),
                                      output_indent=indent))

  def EndObjectPropertyType(self, prop_type):
    indent = self.IndentFromContext(prop_type.GetContext())
    self.outf.write(RunTemplateString(TEMPLATE_END_OBJECT, vars(),
                                      output_indent=indent))

  def ReferencePropertyType(self, prop_type):
    context = prop_type.GetContext()
    indent = self.IndentFromContext(context)
    cident = self.CIdentFromContext(context)
    prop_key, prop_key_len = self.GetPropKeyAndLen(prop_type.prop)
    self.outf.write(RunTemplateString(TEMPLATE_REFERENCE, vars(),
                                      output_indent=indent))


TYPE_MACRO_DICT = {
  ('any', ''): 'String',
  ('boolean', ''): 'Bool',
  ('integer', 'int32'): 'Int32',
  ('integer', 'uint32'): 'Uint32',
  ('number', 'double'): 'Double',
  ('number', 'float'): 'Float',
  ('string', ''): 'String',
  ('string', 'int64'): 'Int64',
  ('string', 'uint64'): 'Uint64',
}


TEMPLATE_DECLARE_SCHEMA = """\
bool Encode(JsonGenerator* g, {{schema.ctype}}* data, ErrorPtr* error);
"""

TEMPLATE_DEFINE_SCHEMA_THUNK = """\

void Encode(Writer* src, {{schema.ctype}}* data, const JsonGeneratorOptions& options, ErrorPtr* error) {
  JsonGenerator g(src, options);
  Encode(&g, data, error);
}
"""

TEMPLATE_BEGIN_SCHEMA = """\

bool Encode(JsonGenerator* g, {{schema.ctype}}* data, ErrorPtr* error) {
  CHECK_GEN(StartMap);
"""

TEMPLATE_END_SCHEMA = """\
  CHECK_GEN(EndMap);
  return true;
}
"""

TEMPLATE_BEGIN_ADDL_PROPS = """\
  GEN_FOREACH_ITER({{index_var}}, {{cident}}, {{prop.ctypedef}}) {
"""

TEMPLATE_END_ADDL_PROPS = """\
  }
"""

TEMPLATE_PRIMITIVE_HEADER = """\
[[if not prop_type.is_parent_array:]]
  CHECK_GEN_KEY({{prop_key}}, {{prop_key_len}});
"""

TEMPLATE_PRIMITIVE_NON_STRING = """\
  CHECK_GEN1({{type_macro}}, {{cident}});
"""

TEMPLATE_PRIMITIVE_STRING = """\
  CHECK_GEN_STRING({{cident}});
"""

TEMPLATE_BEGIN_ARRAY = """\
[[if not prop_type.is_parent_array:]]
  CHECK_GEN_KEY({{prop_key}}, {{prop_key_len}});
[[]]
  CHECK_GEN(StartArray);
  GEN_FOREACH({{index_var}}, {{cident}}) {
"""

TEMPLATE_END_ARRAY = """\
  }
  CHECK_GEN(EndArray);
"""

TEMPLATE_BEGIN_OBJECT = """\
[[if not prop_type.is_parent_array:]]
  CHECK_GEN_KEY({{prop_key}}, {{prop_key_len}});
[[]]
  CHECK_GEN(StartMap);
"""

TEMPLATE_END_OBJECT = """\
  CHECK_GEN(EndMap);
"""

TEMPLATE_REFERENCE = """\
  if ({{cident}}.get()) {
[[if not prop_type.is_parent_array:]]
    CHECK_GEN_KEY({{prop_key}}, {{prop_key_len}});
[[]]
    CHECK_ENCODE({{cident}}.get());
  }
"""
