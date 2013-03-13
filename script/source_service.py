import collections
import cStringIO
import itertools

from easy_template import RunTemplateString
import gapi_utils
import service


SOURCE_SCHEMA_DECL = """\
class {{self.schema.cbtype}} : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
[[for state in sorted(self.schema.states):]]
    {{state}},
[[]]
  };

  explicit {{self.schema.cbtype}}({{self.schema.ctype}}* data);
  virtual int OnNull(JsonParser* p, ErrorPtr* error);
  virtual int OnBool(JsonParser* p, bool value, ErrorPtr* error);
  virtual int OnNumber(JsonParser* p, const char* s, size_t length, ErrorPtr* error);
  virtual int OnString(JsonParser* p, const unsigned char* s, size_t length, ErrorPtr* error);
  virtual int OnStartMap(JsonParser* p, ErrorPtr* error);
  virtual int OnMapKey(JsonParser* p, const unsigned char* s, size_t length, ErrorPtr* error);
  virtual int OnEndMap(JsonParser* p, ErrorPtr* error);
  virtual int OnStartArray(JsonParser* p, ErrorPtr* error);
  virtual int OnEndArray(JsonParser* p, ErrorPtr* error);

 private:
  {{self.schema.ctype}}* data_;
  int state_;
};

"""

SOURCE_SCHEMA_DEF = """\

void Decode(Reader* src, {{self.schema.ctype}}* out_data, ErrorPtr* error) {
  JsonParser p;
  p.PushCallbacks(new {{self.schema.cbtype}}(out_data));
  p.Decode(src, error);
}

{{self.schema.cbtype}}::{{self.schema.cbtype}}({{self.schema.ctype}}* data)
    : data_(data),
      state_(STATE_NONE) {
}

int {{self.schema.cbtype}}::OnNull(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnNull()\\n");
[[]]
  error->reset(new MessageError("Unexpected null"));
  return 0;
}

int {{self.schema.cbtype}}::OnBool(JsonParser* p, bool value, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnBool(%d) %d\\n", value, state_);
[[]]
[[if self.schema.bool_states:]]
  switch (state_) {
[[  for state, info in sorted(self.schema.bool_states.iteritems()):]]
    case {{state}}:
[[    if info.is_array:]]
      APPEND_BOOL_AND_RETURN({{info.cident}});
[[    else:]]
      SET_BOOL_AND_RETURN({{info.cident}}, {{info.prev_state}});
[[  ]]
    default:
      error->reset(new MessageError("Unexpected bool"));
      return 0;
  }
[[else:]]
  error->reset(new MessageError("Unexpected bool"));
  return 0;
[[]]
}

int {{self.schema.cbtype}}::OnNumber(JsonParser* p, const char* s, size_t length, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnNumber(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
[[if self.schema.number_states:]]
  char* endptr;
  char buffer[kMaxNumberBufferSize];
  size_t nbytes = std::min(kMaxNumberBufferSize - 1, length);
  strncpy(&buffer[0], s, nbytes);
  buffer[nbytes] = 0;
  switch (state_) {
[[  for state, info in sorted(self.schema.number_states.iteritems()):]]
[[    prefix = 'APPEND' if info.is_array else 'SET']]
[[    optional_state = '' if info.is_array else ', ' + info.prev_state]]
    case {{state}}:
[[    if info.ctype == "int32_t":]]
      {{prefix}}_INT32_AND_RETURN({{info.cident}}{{optional_state}});
[[    elif info.ctype == "uint32_t":]]
      {{prefix}}_UINT32_AND_RETURN({{info.cident}}{{optional_state}});
[[    elif info.ctype == "float":]]
      {{prefix}}_FLOAT_AND_RETURN({{info.cident}}{{optional_state}});
[[    elif info.ctype == "double":]]
      {{prefix}}_DOUBLE_AND_RETURN({{info.cident}}{{optional_state}});
[[  ]]
    default:
      error->reset(new MessageError("Unexpected number"));
      return 0;
  }
[[else:]]
  error->reset(new MessageError("Unexpected number"));
  return 0;
[[]]
}

int {{self.schema.cbtype}}::OnString(JsonParser* p, const unsigned char* s, size_t length, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnString(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
[[if self.schema.string_states:]]
[[  if any(info.ctype in ("int64_t", "uint64_t") for info in self.schema.string_states.values()):]]
  char* endptr;
  char buffer[kMaxNumberBufferSize];
  size_t nbytes = std::min(kMaxNumberBufferSize - 1, length);
  strncpy(&buffer[0], reinterpret_cast<const char*>(s), nbytes);
  buffer[nbytes] = 0;
[[  ]]
  switch (state_) {
[[  for state, info in sorted(self.schema.string_states.iteritems()):]]
[[    prefix = 'APPEND' if info.is_array else 'SET']]
[[    optional_state = '' if info.is_array else ', ' + info.prev_state]]
    case {{state}}:
[[    if info.ctype == "int64_t":]]
      {{prefix}}_INT64_AND_RETURN({{info.cident}}{{optional_state}});
[[    elif info.ctype == "uint64_t":]]
      {{prefix}}_UINT64_AND_RETURN({{info.cident}}{{optional_state}});
[[    else:]]
      {{prefix}}_STRING_AND_RETURN({{info.cident}}{{optional_state}});
[[  ]]
    default:
      error->reset(new MessageError("Unexpected string"));
      return 0;
  }
[[else:]]
  error->reset(new MessageError("Unexpected string"));
  return 0;
[[]]
}

int {{self.schema.cbtype}}::OnMapKey(JsonParser* p, const unsigned char* s, size_t length, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnMapKey(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
  if (length == 0) return 0;
  switch (state_) {
[[for state, info in sorted(self.schema.props_states.iteritems()):]]
    case {{state}}:
      switch (s[0]) {
[[  for first_char, group in groupby(sorted(info), lambda i:i.name[0]):]]
        case '{{first_char}}':
[[  # Sort group in reverse order of name length.]]
[[    group = sorted(group, lambda x,y: cmp(len(y.name), len(x.name)))]]
[[    for group_info in group:]]
          CHECK_MAP_KEY("{{group_info.name}}", {{len(group_info.name)}}, {{group_info.next_state}});
[[    ]]
          break;
[[  ]]
        default: break;
      }
[[]]
    default: break;
  }
  error->reset(new MessageError("Unknown map key"));
  return 0;
}

int {{self.schema.cbtype}}::OnStartMap(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnStartMap() %d\\n", state_);
[[]]
  switch (state_) {
    case STATE_NONE:
      state_ = STATE_TOP;
      return 1;
[[if self.schema.map_states:]]
[[  for state, info in sorted(self.schema.map_states.iteritems()):]]
    case {{state}}:
[[    if info.map_type == 'ref':]]
[[      if info.is_array:]]
      PUSH_CALLBACK_REF_ARRAY_AND_RETURN({{info.ctype}}, {{info.cbtype}}, {{info.cident}});
[[      else:]]
      PUSH_CALLBACK_REF_AND_RETURN({{info.ctype}}, {{info.cbtype}}, {{info.cident}});
[[    elif info.map_type == 'object':]]
[[      if info.is_array:]]
      data_->{{info.cident}}.push_back({{info.ctype}}());
[[      ]]
      state_ = {{info.next_state}};
      return 1;
[[]]
    default:
      error->reset(new MessageError("Unexpected state"));
      return 0;
  }
}

int {{self.schema.cbtype}}::OnEndMap(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnEndMap() %d\\n", state_);
[[]]
  switch (state_) {
    case STATE_TOP:
      if (p->PopCallbacks())
        return p->HasCallbacks() ? p->OnEndMap() : 1;
      error->reset(new MessageError("Unexpected end of map"));
      return 0;
[[if self.schema.map_states:]]
[[  for state, info in sorted(self.schema.map_states.iteritems()):]]
[[    if info.map_type == 'ref':]]
    case {{state}}:
      state_ = {{info.prev_state}};
      return 1;
[[    elif info.map_type == 'object':]]
    case {{info.next_state}}:
      state_ = {{info.prev_state}};
      return 1;
[[]]
    default:
      error->reset(new MessageError("Unexpected state"));
      return 0;
  }
}

int {{self.schema.cbtype}}::OnStartArray(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnStartArray() %d\\n", state_);
[[]]
[[if self.schema.array_states:]]
  switch (state_) {
[[  for state, info in self.schema.array_states.iteritems():]]
    case {{state}}:
[[    if info.is_array:]]
      data_->{{info.cident}}.push_back({{info.elem_type}}());
[[    ]]
      state_ = {{info.next_state}};
      return 1;
[[  ]]
    default:
      error->reset(new MessageError("Unexpected array"));
      return 0;
  }
[[else:]]
  error->reset(new MessageError("Unexpected array"));
  return 0;
[[]]
}

int {{self.schema.cbtype}}::OnEndArray(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{self.schema.cbtype}}::OnEndArray() %d\\n", state_);
[[]]
[[if self.schema.array_states:]]
  switch (state_) {
[[  for state, info in self.schema.array_states.iteritems():]]
    case {{info.next_state}}:
      state_ = {{info.prev_state}};
      return 1;
[[  ]]
    default:
      error->reset(new MessageError("Unexpected end of array"));
      return 0;
  }
[[else:]]
  error->reset(new MessageError("Unexpected end of array"));
  return 0;
[[]]
}

"""

class SchemaInfo(object):
  def __init__(self, schema_name=None, parent=None):
    cap = gapi_utils.CapWords(schema_name)
    if parent:
      self.base_ctype = cap + 'Object'
      self.ctype = '%s::%sObject' % (parent.ctype, cap)
    else:
      self.base_ctype = self.ctype = cap
    self.cbtype = '%sCallbacks' % cap
    self.states = set()
    self.context_stack = []
    self.null_states = {}
    self.bool_states = {}
    self.number_states = {}
    self.string_states = {}
    self.map_states = {}
    self.array_states = {}
    self.props_states = collections.defaultdict(list)
    self.outf = cStringIO.StringIO()


PrimitiveStateInfo = collections.namedtuple(
    'PrimitiveStateInfo', ['cident', 'prev_state', 'ctype', 'is_array'])
ArrayStateInfo = collections.namedtuple(
    'ArrayStateInfo', ['cident', 'next_state', 'prev_state', 'elem_type', 'is_array'])
RefStateInfo = collections.namedtuple(
    'RefStateInfo', ['cident', 'prev_state', 'ctype', 'cbtype', 'is_array', 'map_type'])
ObjectStateInfo = collections.namedtuple(
    'ObjectStateInfo', ['cident', 'next_state', 'prev_state', 'ctype', 'is_array', 'map_type'])
PropStateInfo = collections.namedtuple(
    'PropStateInfo', ['name', 'next_state'])


class DecodeService(service.Service):
  def __init__(self, service, outf, options):
    self.outf = outf
    self.options = options
    self.schema = None
    self.schema_level = 0
    self.prop_type = ''
    self.decf = cStringIO.StringIO()
    self.deff = cStringIO.StringIO()
    super(DecodeService, self).__init__(service)

  @property
  def state(self):
    return self.StateFromContextStack(self.schema.context_stack)

  @property
  def prev_state(self):
    return self.StateFromContextStack(self.schema.context_stack[:-1])

  @property
  def non_key_state(self):
    stack_copy = self.schema.context_stack[:]
    while stack_copy and not stack_copy[-1][1]:
      stack_copy.pop()
    return self.StateFromContextStack(stack_copy)

  @property
  def cident(self):
    return self.CIdentFromContextStack(self.schema.context_stack)

  @property
  def is_array_state(self):
    return self.schema.context_stack[-1][1] == 'array'

  def StateFromContextStack(self, context_stack):
    if not context_stack:
      return 'STATE_TOP'
    result = 'STATE'
    prev_typ = None
    for name, typ in context_stack:
      if name or not prev_typ:
        result += '_'
      if name: result += gapi_utils.Upper(name)
      elif typ == 'array': result += 'A'
      elif typ == 'object': result += 'O'
      prev_typ = typ
    if not prev_typ:
      result += '_K'
    return result

  def CIdentFromContextStack(self, context_stack):
    if not context_stack:
      return ''
    result = ''
    prev_typ = None
    for name, typ in context_stack:
      if prev_typ == 'array': result += '.back()'
      if name: result += gapi_utils.SnakeCase(name)
      elif typ == 'object': result += '.'
      prev_typ = typ
    return result

  def PushContext(self, name, typ):
    self.schema.context_stack.append((name, typ))
    self.schema.states.add(self.state)

  def PopContext(self):
    self.schema.context_stack.pop()

  def EndService(self, name, version):
    self.outf.write(self.decf.getvalue())
    self.outf.write(self.deff.getvalue())

  def BeginSchema(self, schema_name, schema):
    if self.schema_level == 0:
      self.schema = SchemaInfo(schema_name, self.schema)
    self.schema_level += 1

  def EndSchema(self, schema_name, schema):
    self.schema_level -= 1
    if self.schema_level == 0:
      groupby = itertools.groupby
      self.decf.write(RunTemplateString(SOURCE_SCHEMA_DECL, vars()))
      self.deff.write(RunTemplateString(SOURCE_SCHEMA_DEF, vars()))
      self.schema = None

  def BeginProperty(self, prop_name, prop):
    current_state = self.state
    self.PushContext(prop_name, None)
    next_state = self.state
    self.schema.props_states[current_state].append(PropStateInfo(prop_name, next_state))
    self.prop_type = ''

  def EndProperty(self, prop_name, prop):
    self.PopContext()

  def OnPropertyTypeRef(self, prop_name, prop, ref):
    cident = self.cident
    is_array = self.is_array_state
    assert self.state not in self.schema.map_states
    self.schema.map_states[self.state] = \
        RefStateInfo(cident, self.non_key_state, ref, ref + 'Callbacks', is_array, 'ref')
    self.prop_type = gapi_utils.WrapType('std::tr1::shared_ptr<%s>', ref)

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    # TODO(binji): handle any
    cident = self.cident
    ctype = service.TYPE_DICT[(prop_type, prop_format)]
    is_array = self.is_array_state
    data = PrimitiveStateInfo(cident, self.non_key_state, ctype, is_array)
    if prop_type in ['number', 'integer']:
      assert self.state not in self.schema.number_states
      self.schema.number_states[self.state] = data
    elif prop_type == 'boolean':
      assert self.state not in self.schema.bool_states
      self.schema.bool_states[self.state] = data
    elif prop_type == 'string':
      assert self.state not in self.schema.string_states
      self.schema.string_states[self.state] = data
    self.prop_type = ctype

  def BeginPropertyTypeArray(self, prop_name, prop, prop_items):
    cident = self.cident
    prev_state = self.non_key_state
    cident = self.cident
    current_state = self.state
    is_array = self.is_array_state
    self.PushContext(None, 'array')
    next_state = self.state
    assert current_state not in self.schema.array_states
    self.schema.array_states[current_state] = \
        ArrayStateInfo(cident, next_state, prev_state, None, is_array)

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    self.prop_type = gapi_utils.WrapType('std::vector<%s>', self.prop_type)
    self.PopContext()
    self.schema.array_states[self.state] = \
        self.schema.array_states[self.state]._replace(elem_type=self.prop_type)

  def BeginPropertyTypeObject(self, prop_name, prop):
    if not self.prop_type:
      self.prop_type = self.schema.ctype
    self.prop_type += '::%sObject' % gapi_utils.CapWords(prop_name)
    cident = self.cident
    prev_state = self.non_key_state
    basename = gapi_utils.CapWords(prop_name)
    current_state = self.state
    is_array = self.is_array_state
    self.PushContext(None, 'object')
    next_state = self.state
    assert self.state not in self.schema.map_states
    self.schema.map_states[current_state] = \
        ObjectStateInfo(cident, next_state, prev_state, self.prop_type, is_array, 'object')

  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    self.PopContext()
    self.prop_type = self.schema.map_states[self.state].ctype

# ENCODING #####################################################################
SOURCE_ENC_DECL_SCHEMA = """\
bool Encode(JsonGenerator* g, {{self.schema.ctype}}* data, ErrorPtr* error);
"""

SOURCE_ENC_BEGIN_SCHEMA = """\

void Encode(Writer* src, {{self.schema.ctype}}* data, const JsonGeneratorOptions& options, ErrorPtr* error) {
  JsonGenerator g(src, options);
  Encode(&g, data, error);
}

bool Encode(JsonGenerator* g, {{self.schema.ctype}}* data, ErrorPtr* error) {
  CHECK_GEN(StartMap);
"""

SOURCE_ENC_END_SCHEMA = """\
  CHECK_GEN(EndMap);
  return true;
}
"""

SOURCE_ENC_PROP_TYPE_FORMAT = """\
  CHECK_GEN_KEY(\"{{prop_name}}\", {{len(prop_name)}});
[[if ctype == 'bool':]]
  CHECK_GEN1(Bool, data->{{cident}});
[[elif ctype == 'int32_t':]]
  CHECK_GEN1(Int32, data->{{cident}});
[[elif ctype == 'uint32_t':]]
  CHECK_GEN1(Uint32, data->{{cident}});
[[elif ctype == 'int64_t':]]
  CHECK_GEN1(Int64, data->{{cident}});
[[elif ctype == 'uint64_t':]]
  CHECK_GEN1(Uint64, data->{{cident}});
[[elif ctype == 'float':]]
  CHECK_GEN1(Float, data->{{cident}});
[[elif ctype == 'double':]]
  CHECK_GEN1(Double, data->{{cident}});
[[elif ctype == 'std::string':]]
  CHECK_GEN_STRING(data->{{cident}});
[[]]
"""

SOURCE_ENC_PROP_TYPE_REF = """\
  if (data->{{cident}}.get()) {
    CHECK_GEN_KEY(\"{{prop_name}}\", {{len(prop_name)}});
    CHECK_ENCODE(data->{{cident}}.get());
  }
"""

SOURCE_ENC_BEGIN_PROP_TYPE_ARRAY = """\
  CHECK_GEN_KEY(\"{{prop_name}}\", {{len(prop_name)}});
  CHECK_GEN(StartArray);
  GEN_FOREACH({{ix}}, data->{{cident}}) {
"""

SOURCE_ENC_END_PROP_TYPE_ARRAY = """\
  }
  CHECK_GEN(EndArray);
"""

SOURCE_ENC_BEGIN_PROP_TYPE_OBJECT = """\
  CHECK_GEN_KEY(\"{{prop_name}}\", {{len(prop_name)}});
  CHECK_GEN(StartMap);
"""

SOURCE_ENC_END_PROP_TYPE_OBJECT = """\
  CHECK_GEN(EndMap);
"""


class EncodeService(service.Service):
  def __init__(self, service, outf, options):
    self.outf = outf
    self.options = options
    self.context_stack = []
    self.schema = None
    self.schema_level = 0
    self.decf = cStringIO.StringIO()
    self.deff = cStringIO.StringIO()
    super(EncodeService, self).__init__(service)

  @property
  def cident(self):
    return self.CIdentFromContextStack(self.context_stack)

  @property
  def is_array_state(self):
    return self.context_stack[-1][1] == 'array'

  @property
  def ix_char(self):
    return self.context_stack[-1][2]

  @property
  def indent(self):
    result = ''
    for _, typ, _ in self.context_stack:
      if typ == 'array':
        result += '  '
    return result

  def CIdentFromContextStack(self, context_stack):
    if not context_stack:
      return ''
    result = ''
    prev_typ, prev_ix = None, None
    for name, typ, ix in context_stack:
      if name: result += gapi_utils.SnakeCase(name)
      if typ == 'array': result += '[%s]' % ix
      elif typ == 'object': result += '.'
      prev_typ, prev_ix = typ, ix
    return result

  def PushContext(self, name, typ):
    next_ix = None
    if self.context_stack:
      next_ix = prev_ix = self.context_stack[-1][2]
      if typ == 'array':
        if prev_ix:
          next_ix = chr(ord(prev_ix) + 1)
        else:
          next_ix = 'i'
    self.context_stack.append((name, typ, next_ix))

  def PopContext(self):
    self.context_stack.pop()

  def EndService(self, name, version):
    self.outf.write(self.decf.getvalue())
    self.outf.write(self.deff.getvalue())

  def BeginSchema(self, schema_name, schema):
    if self.schema_level == 0:
      self.schema = SchemaInfo(schema_name, self.schema)
      self.decf.write(RunTemplateString(SOURCE_ENC_DECL_SCHEMA, vars()))
      self.deff.write(RunTemplateString(SOURCE_ENC_BEGIN_SCHEMA, vars()))
    self.schema_level += 1

  def EndSchema(self, schema_name, schema):
    self.schema_level -= 1
    if self.schema_level == 0:
      self.deff.write(RunTemplateString(SOURCE_ENC_END_SCHEMA, vars()))
      self.schema = None

  def BeginProperty(self, prop_name, prop):
    self.PushContext(prop_name, None)

  def EndProperty(self, prop_name, prop):
    self.PopContext()

  def OnPropertyTypeRef(self, prop_name, prop, ref):
    cident = self.cident
    is_array = self.is_array_state
    self.deff.write(RunTemplateString(SOURCE_ENC_PROP_TYPE_REF, vars(),
        output_indent=self.indent))

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    cident = self.cident
    is_array = self.is_array_state
    ctype = service.TYPE_DICT[(prop_type, prop_format)]
    self.deff.write(RunTemplateString(SOURCE_ENC_PROP_TYPE_FORMAT, vars(),
        output_indent=self.indent))

  def BeginPropertyTypeArray(self, prop_name, prop, prop_items):
    cident = self.cident
    indent = self.indent
    is_array = self.is_array_state
    self.PushContext(None, 'array')
    ix = self.ix_char
    self.deff.write(RunTemplateString(SOURCE_ENC_BEGIN_PROP_TYPE_ARRAY, vars(),
        output_indent=indent))

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    self.PopContext()
    self.deff.write(RunTemplateString(SOURCE_ENC_END_PROP_TYPE_ARRAY, vars(),
        output_indent=self.indent))

  def BeginPropertyTypeObject(self, prop_name, prop):
    cident = self.cident
    is_array = self.is_array_state
    self.PushContext(None, 'object')
    self.deff.write(RunTemplateString(SOURCE_ENC_BEGIN_PROP_TYPE_OBJECT, vars(),
        output_indent=self.indent))

  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    self.deff.write(RunTemplateString(SOURCE_ENC_END_PROP_TYPE_OBJECT, vars(),
        output_indent=self.indent))
    self.PopContext()


# CONSTRUCTOR/DESTRUCTOR #######################################################

SOURCE_CONS_BEGIN_SCHEMA = """\
{{self.schema.ctype}}::{{self.schema.base_ctype}}() {
"""

SOURCE_CONS_END_SCHEMA = """\
}

{{self.schema.ctype}}::~{{self.schema.base_ctype}}() {
}

"""

SOURCE_CONS_PROP_TYPE_FORMAT = """\
[[if not has_array:]]
[[  if ctype == 'bool':]]
  {{cident}} = false;
[[  elif ctype in ('int32_t', 'uint32_t', 'int64_t', 'uint64_t'):]]
  {{cident}} = 0;
[[  elif ctype in ('float', 'double'):]]
  {{cident}} = 0;
[[]]
"""


class ConstructorService(service.Service):
  def __init__(self, service, outf, options):
    self.outf = outf
    self.array_count = 0
    self.schema_stack = []
    super(ConstructorService, self).__init__(service)

  @property
  def schema(self):
    if self.schema_stack:
      return self.schema_stack[-1]
    return None

  @property
  def has_array(self):
    return self.array_count != 0

  def BeginSchema(self, schema_name, schema):
    self.schema_stack.append(SchemaInfo(schema_name, self.schema))
    self.schema.outf.write(RunTemplateString(SOURCE_CONS_BEGIN_SCHEMA, vars()))

  def EndSchema(self, schema_name, schema):
    schema = self.schema
    self.schema.outf.write(RunTemplateString(SOURCE_CONS_END_SCHEMA, vars()))
    self.schema_stack.pop()
    self.outf.write(schema.outf.getvalue())

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    cident = gapi_utils.SnakeCase(prop_name)
    has_array = self.has_array
    ctype = service.TYPE_DICT[(prop_type, prop_format)]
    self.schema.outf.write(RunTemplateString(SOURCE_CONS_PROP_TYPE_FORMAT, vars()))

  def BeginPropertyTypeArray(self, prop_name, prop, prop_items):
    self.array_count += 1

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    self.array_count -= 1


# SERVICE ######################################################################

SOURCE_HEAD = """\
#include "{{self.headerfname}}"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits>
#include <vector>
#include "json_generator.h"
#include "json_parser.h"
#include "json_parser_macros.h"


[[if self.options.namespace:]]
namespace {{self.options.namespace}} {

static const size_t kMaxNumberBufferSize = 32;

[[]]
"""

SOURCE_FOOT = """\
[[if self.options.namespace:]]
}  // namespace {{self.options.namespace}}
[[]]
"""


class Service(service.Service):
  def __init__(self, service, outfname, headerfname, options):
    self.outfname = outfname
    self.options = options
    self.headerfname = headerfname
    self.consf = cStringIO.StringIO()
    self.conss = ConstructorService(service, self.consf, options)
    self.decf = cStringIO.StringIO()
    self.decs = DecodeService(service, self.decf, options)
    self.encf = cStringIO.StringIO()
    self.encs = EncodeService(service, self.encf, options)
    super(Service, self).__init__(service)

  def BeginService(self, name, version):
    self.conss.BeginService(name, version)
    self.encs.BeginService(name, version)
    self.decs.BeginService(name, version)

  def EndService(self, name, version):
    self.conss.EndService(name, version)
    self.encs.EndService(name, version)
    self.decs.EndService(name, version)
    with open(self.outfname, 'w') as outf:
      outf.write(RunTemplateString(SOURCE_HEAD, vars()))
      outf.write(self.consf.getvalue())
      outf.write(self.decf.getvalue())
      outf.write(self.encf.getvalue())
      outf.write(RunTemplateString(SOURCE_FOOT, vars()))

  def BeginSchema(self, schema_name, schema):
    self.conss.BeginSchema(schema_name, schema)
    self.encs.BeginSchema(schema_name, schema)
    self.decs.BeginSchema(schema_name, schema)

  def EndSchema(self, schema_name, schema):
    self.conss.EndSchema(schema_name, schema)
    self.encs.EndSchema(schema_name, schema)
    self.decs.EndSchema(schema_name, schema)

  def BeginProperty(self, prop_name, prop):
    self.conss.BeginProperty(prop_name, prop)
    self.encs.BeginProperty(prop_name, prop)
    self.decs.BeginProperty(prop_name, prop)

  def EndProperty(self, prop_name, prop):
    self.conss.EndProperty(prop_name, prop)
    self.encs.EndProperty(prop_name, prop)
    self.decs.EndProperty(prop_name, prop)

  def OnPropertyComment(self, prop_name, prop, comment):
    self.conss.OnPropertyComment(prop_name, prop, comment)
    self.encs.OnPropertyComment(prop_name, prop, comment)
    self.decs.OnPropertyComment(prop_name, prop, comment)

  def BeginPropertyType(self, prop_name, prop):
    self.conss.BeginPropertyType(prop_name, prop)
    self.encs.BeginPropertyType(prop_name, prop)
    self.decs.BeginPropertyType(prop_name, prop)

  def EndPropertyType(self, prop_name, prop):
    self.conss.EndPropertyType(prop_name, prop)
    self.encs.EndPropertyType(prop_name, prop)
    self.decs.EndPropertyType(prop_name, prop)

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    self.conss.OnPropertyTypeFormat(prop_name, prop, prop_type, prop_format)
    self.encs.OnPropertyTypeFormat(prop_name, prop, prop_type, prop_format)
    self.decs.OnPropertyTypeFormat(prop_name, prop, prop_type, prop_format)

  def OnPropertyTypeRef(self, prop_name, prop, ref):
    self.conss.OnPropertyTypeRef(prop_name, prop, ref)
    self.encs.OnPropertyTypeRef(prop_name, prop, ref)
    self.decs.OnPropertyTypeRef(prop_name, prop, ref)

  def BeginPropertyTypeArray(self, prop_name, prop, prop_items):
    self.conss.BeginPropertyTypeArray(prop_name, prop, prop_items)
    self.encs.BeginPropertyTypeArray(prop_name, prop, prop_items)
    self.decs.BeginPropertyTypeArray(prop_name, prop, prop_items)

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    self.conss.EndPropertyTypeArray(prop_name, prop, prop_items)
    self.encs.EndPropertyTypeArray(prop_name, prop, prop_items)
    self.decs.EndPropertyTypeArray(prop_name, prop, prop_items)

  def BeginPropertyTypeObject(self, prop_name, prop):
    self.conss.BeginPropertyTypeObject(prop_name, prop)
    self.encs.BeginPropertyTypeObject(prop_name, prop)
    self.decs.BeginPropertyTypeObject(prop_name, prop)

  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    self.conss.EndPropertyTypeObject(prop_name, prop, schema_name)
    self.encs.EndPropertyTypeObject(prop_name, prop, schema_name)
    self.decs.EndPropertyTypeObject(prop_name, prop, schema_name)
