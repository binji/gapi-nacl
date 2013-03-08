import cStringIO
import itertools

from easy_template import RunTemplateString
import gapi_utils
import service


SOURCE_HEAD = """\
#include "{{header}}"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits>
#include <vector>
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

SOURCE_SCHEMA_DECL = """\
class {{sub_schema.cbtype}} : public JsonCallbacks {
 public:
[[if sub_schema.sub_schemas:]]
[[  for sub_schema_name in sorted(sub_schema.sub_schemas):]]
  class {{sub_schema_name}};
[[  ]]

[[]]
  enum {
    STATE_NONE,
    STATE_TOP,
[[for state in sorted(sub_schema.states):]]
    {{state}},
[[]]
  };

  explicit {{sub_schema.base_cbtype}}({{sub_schema.ctype}}* data);
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
  {{sub_schema.ctype}}* data_;
  int state_;
};

"""

SOURCE_SCHEMA_DEF = """\

void Decode(Reader* src, {{sub_schema.ctype}}* out_data, ErrorPtr* error) {
  JsonParser p;
  p.PushCallbacks(new {{sub_schema.cbtype}}(out_data));
  p.Decode(src, error);
}

{{sub_schema.cbtype}}::{{sub_schema.base_cbtype}}({{sub_schema.ctype}}* data)
    : data_(data),
      state_(STATE_NONE) {
}

int {{sub_schema.cbtype}}::OnNull(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnNull()\\n");
[[]]
  if (error) error->reset(new MessageError("Unexpected null"));
  return 0;
}

int {{sub_schema.cbtype}}::OnBool(JsonParser* p, bool value, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnBool(%d) %d\\n", value, state_);
[[]]
[[if sub_schema.bool_states:]]
  switch (state_) {
[[  for state, (cident, ctype, is_array) in sorted(sub_schema.bool_states.iteritems()):]]
    case {{state}}:
[[    if is_array:]]
      APPEND_BOOL_AND_RETURN({{cident}});
[[    else:]]
      SET_BOOL_AND_RETURN({{cident}});
[[  ]]
    default:
      if (error) error->reset(new MessageError("Unexpected bool"));
      return 0;
  }
[[else:]]
  if (error) error->reset(new MessageError("Unexpected bool"));
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnNumber(JsonParser* p, const char* s, size_t length, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnNumber(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
[[if sub_schema.number_states:]]
  char* endptr;
  char buffer[kMaxNumberBufferSize];
  size_t nbytes = std::min(kMaxNumberBufferSize - 1, length);
  strncpy(&buffer[0], s, nbytes);
  buffer[nbytes] = 0;
  switch (state_) {
[[  for state, (cident, ctype, is_array) in sorted(sub_schema.number_states.iteritems()):]]
[[    prefix = 'APPEND' if is_array else 'SET']]
    case {{state}}:
[[    if ctype == "int32_t":]]
      {{prefix}}_INT32_AND_RETURN({{cident}});
[[    elif ctype == "uint32_t":]]
      {{prefix}}_UINT32_AND_RETURN({{cident}});
[[    elif ctype == "float":]]
      {{prefix}}_FLOAT_AND_RETURN({{cident}});
[[    elif ctype == "double":]]
      {{prefix}}_DOUBLE_AND_RETURN({{cident}});
[[  ]]
    default:
      if (error) error->reset(new MessageError("Unexpected number"));
      return 0;
  }
[[else:]]
  if (error) error->reset(new MessageError("Unexpected number"));
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnString(JsonParser* p, const unsigned char* s, size_t length, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnString(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
[[if sub_schema.string_states:]]
[[  if any(ctype in ("int64_t", "uint64_t") for _,(_, ctype, _) in sub_schema.string_states.iteritems()):]]
  char* endptr;
  char buffer[kMaxNumberBufferSize];
  size_t nbytes = std::min(kMaxNumberBufferSize - 1, length);
  strncpy(&buffer[0], reinterpret_cast<const char*>(s), nbytes);
  buffer[nbytes] = 0;
[[  ]]
  switch (state_) {
[[  for state, (cident, ctype, is_array) in sorted(sub_schema.string_states.iteritems()):]]
[[    prefix = 'APPEND' if is_array else 'SET']]
    case {{state}}:
[[    if ctype == "int64_t":]]
      {{prefix}}_INT64_AND_RETURN({{cident}});
[[    elif ctype == "uint64_t":]]
      {{prefix}}_UINT64_AND_RETURN({{cident}});
[[    else:]]
      {{prefix}}_STRING_AND_RETURN({{cident}});
[[  ]]
    default:
      if (error) error->reset(new MessageError("Unexpected string"));
      return 0;
  }
[[else:]]
  if (error) error->reset(new MessageError("Unexpected string"));
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnStartMap(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnStartMap() %d\\n", state_);
[[]]
  switch (state_) {
    case STATE_NONE:
      state_ = STATE_TOP;
      return 1;
[[if sub_schema.map_states:]]
[[  for state, (cident, ctype, cbtype, is_array, map_type) in sorted(sub_schema.map_states.iteritems()):]]
    case {{state}}:
[[    if map_type == 'ref':]]
[[      if is_array:]]
      PUSH_CALLBACK_REF_ARRAY_AND_RETURN({{ctype}}, {{cbtype}}, {{cident}});
[[      else:]]
      PUSH_CALLBACK_REF_AND_RETURN({{ctype}}, {{cbtype}}, {{cident}});
[[    elif map_type == 'object':]]
[[      if is_array:]]
      PUSH_CALLBACK_OBJECT_ARRAY_AND_RETURN({{ctype}}, {{cbtype}}, {{cident}});
[[      else:]]
      PUSH_CALLBACK_OBJECT_AND_RETURN({{ctype}}, {{cbtype}}, {{cident}});
[[]]
    default:
      if (error) error->reset(new MessageError("Unexpected state"));
      return 0;
  }
}

int {{sub_schema.cbtype}}::OnMapKey(JsonParser* p, const unsigned char* s, size_t length, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnMapKey(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
  if (length == 0) return 0;
  switch (s[0]) {
[[for first_char, group in groupby(sorted(sub_schema.props), lambda p:p[0][0]):]]
    case '{{first_char}}':
[[  # Sort group in reverse order of name length.]]
[[  group = sorted(group, lambda x,y: cmp(len(y[0]), len(x[0])))]]
[[  for prop_name, next_state in group:]]
      CHECK_MAP_KEY("{{prop_name}}", {{len(prop_name)}}, {{next_state}});
[[  ]]
      if (error) error->reset(new MessageError("Unknown map key"));
      return 0;
[[]]
    default:
      if (error) error->reset(new MessageError("Unknown map key"));
      return 0;
  }
}

int {{sub_schema.cbtype}}::OnEndMap(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnEndMap() %d\\n", state_);
[[]]
  if (!p->PopCallbacks()) {
    if (error) error->reset(new MessageError("Unexpected end of map"));
    return 0;
  }
  return 1;
}

int {{sub_schema.cbtype}}::OnStartArray(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnStartArray() %d\\n", state_);
[[]]
[[if sub_schema.array_states:]]
  switch (state_) {
[[  for state, (next_state, prev_state) in sub_schema.array_states.iteritems():]]
    case {{state}}:
      state_ = {{next_state}};
      return 1;
[[  ]]
    default:
      if (error) error->reset(new MessageError("Unexpected array"));
      return 0;
  }
[[else:]]
  if (error) error->reset(new MessageError("Unexpected array"));
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnEndArray(JsonParser* p, ErrorPtr* error) {
[[if self.options.debug:]]
  printf("{{sub_schema.cbtype}}::OnEndArray() %d\\n", state_);
[[]]
[[if sub_schema.array_states:]]
  switch (state_) {
[[  for state, (next_state, prev_state) in sub_schema.array_states.iteritems():]]
    case {{next_state}}:
      state_ = {{prev_state}};
      return 1;
[[  ]]
    default:
      if (error) error->reset(new MessageError("Unexpected end of array"));
      return 0;
  }
[[else:]]
  if (error) error->reset(new MessageError("Unexpected end of array"));
  return 0;
[[]]
}

"""


class SchemaInfo(object):
  def __init__(self, schema_name=None, parent=None):
    if schema_name:
      cap = gapi_utils.CapWords(schema_name)
      self.base_cbtype = '%sCallbacks' % cap
      if parent.cbtype:
        self.cbtype = '%s::%s' % (parent.cbtype, self.base_cbtype)
        self.ctype = '%s::%sObject' % (parent.ctype, cap)
      else:
        self.cbtype = self.base_cbtype
        self.ctype = cap
    else:
      self.cbtype = ''
      self.base_cbtype = ''
      self.ctype = ''
    self.states = set()
    self.state_stack = []
    self.sub_schemas = set()
    self.null_states = {}
    self.bool_states = {}
    self.number_states = {}
    self.string_states = {}
    self.map_states = {}
    self.array_states = {}
    self.props = []
    self.decf = cStringIO.StringIO()
    self.deff = cStringIO.StringIO()


class Service(service.Service):
  def __init__(self, service, outfname, headerfname, options):
    self.outfname = outfname
    self.options = options
    self.headerfname = headerfname
    self.schema_stack = [SchemaInfo()]
    super(Service, self).__init__(service)

  @property
  def schema(self):
    assert self.schema_stack
    return self.schema_stack[-1]

  @property
  def state(self):
    if self.schema.state_stack:
      return self.schema.state_stack[-1]
    return 'STATE_TOP'

  @property
  def prev_state(self):
    if len(self.schema.state_stack) >= 2:
      return self.schema.state_stack[-2]
    return 'STATE_TOP'

  def PushState(self, state):
    current_state = self.state
    # strip _K if it exists
    if current_state.endswith('_K'):
      current_state = current_state[:-2]
    if current_state == 'STATE_TOP':
      new_state = 'STATE_%s_K' % state
    elif state == 'array':
      new_state = '%s_A' % current_state
    elif state == 'object':
      if current_state.endswith('_A'):
        new_state = '%s_AO' % current_state[:-2]
      else:
        new_state = '%s_O' % current_state
    else:
      new_state = '%s_%s_K' % (current_state, state)
    self.schema.states.add(new_state)
    self.schema.state_stack.append(new_state)

  def PopState(self):
    self.schema.state_stack.pop()

  def BeginService(self, name, version):
    pass

  def EndService(self, name, version):
    with open(self.outfname, 'w') as outf:
      header = self.headerfname
      outf.write(RunTemplateString(SOURCE_HEAD, vars()))
      outf.write(self.schema.decf.getvalue())
      outf.write(self.schema.deff.getvalue())
      outf.write(RunTemplateString(SOURCE_FOOT, vars()))

  def BeginSchema(self, schema_name, schema):
    schema_info = SchemaInfo(schema_name, self.schema)

    cident = gapi_utils.SnakeCase(schema_name)
    is_array = self.state.endswith('_A')
    self.schema.map_states[self.state] = \
        (cident, schema_info.ctype, schema_info.cbtype, is_array, 'object')

    self.schema.sub_schemas.add(schema_info.base_cbtype)
    self.schema_stack.append(schema_info)

  def EndSchema(self, schema_name, schema):
    sub_schema = self.schema
    self.schema_stack.pop()
    groupby = itertools.groupby
    self.schema.decf.write(RunTemplateString(SOURCE_SCHEMA_DECL, vars()))
    self.schema.decf.write(sub_schema.decf.getvalue())
    self.schema.deff.write(RunTemplateString(SOURCE_SCHEMA_DEF, vars()))
    self.schema.deff.write(sub_schema.deff.getvalue())

  def BeginProperty(self, prop_name, prop):
    current_state = self.state
    self.PushState(gapi_utils.Upper(prop_name))
    next_state = self.state
    self.schema.props.append((prop_name, next_state))

  def EndProperty(self, prop_name, prop):
    self.PopState()

  def OnPropertyTypeRef(self, prop_name, prop, ref):
    cident = gapi_utils.SnakeCase(prop_name)
    is_array = self.state.endswith('_A')
    assert self.state not in self.schema.map_states
    self.schema.map_states[self.state] = (cident, ref, ref + 'Callbacks', is_array, 'ref')

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    # TODO(binji): handle any
    cident = gapi_utils.SnakeCase(prop_name)
    ctype = service.TYPE_DICT[(prop_type, prop_format)]
    is_array = self.state.endswith('_A')
    data = (cident, ctype, is_array)
    if prop_type in ['number', 'integer']:
      assert self.state not in self.schema.number_states
      self.schema.number_states[self.state] = data
    elif prop_type == 'boolean':
      assert self.state not in self.schema.bool_states
      self.schema.bool_states[self.state] = data
    elif prop_type == 'string':
      assert self.state not in self.schema.string_states
      self.schema.string_states[self.state] = data

  def BeginPropertyTypeArray(self, prop_name, prop, prop_items):
    prev_state = self.prev_state
    current_state = self.state
    if current_state.endswith('_A'):
      prev_state = current_state
    self.PushState('array')
    next_state = self.state
    assert current_state not in self.schema.array_states
    self.schema.array_states[current_state] = (next_state, prev_state)

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    self.PopState()
