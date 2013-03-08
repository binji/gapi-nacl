import collections
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
      data_->{{info.cident}}.push_back({{self.schema.ctype}}::{{info.ctype}}());
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


def StateFromContextStack(context_stack):
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


def CIdentFromContextStack(context_stack):
  if not context_stack:
    return ''
  result = ''
  last_name_ix = 0
  ix = 0
  for ix, (name, _) in enumerate(context_stack):
    if name:
      # Build up identifier from last name.
      for _, typ in context_stack[last_name_ix+1:ix]:
        if typ == 'array':
          result += '.back()'
        if typ == 'object':
          result += '.'
      result += gapi_utils.SnakeCase(name)
      last_name_ix = ix
  return result
  """
  prev_typ = None
  for name, typ in context_stack:
    if name: result += gapi_utils.SnakeCase(name)
    elif typ == 'array': result += '.back()'
    elif typ == 'object': result += '.'
    prev_typ = typ
  return result
  """


class SchemaInfo(object):
  def __init__(self, schema_name=None, parent=None):
    cap = gapi_utils.CapWords(schema_name)
    self.cbtype = '%sCallbacks' % cap
    self.ctype = cap
    self.states = set()
    self.context_stack = []
    self.null_states = {}
    self.bool_states = {}
    self.number_states = {}
    self.string_states = {}
    self.map_states = {}
    self.array_states = {}
    self.props_states = collections.defaultdict(list)


PrimitiveStateInfo = collections.namedtuple(
    'PrimitiveStateInfo', ['cident', 'prev_state', 'ctype', 'is_array'])
ArrayStateInfo = collections.namedtuple(
    'ArrayStateInfo', ['cident', 'next_state', 'prev_state'])
RefStateInfo = collections.namedtuple(
    'RefStateInfo', ['cident', 'prev_state', 'ctype', 'cbtype', 'is_array', 'map_type'])
ObjectStateInfo = collections.namedtuple(
    'ObjectStateInfo', ['cident', 'next_state', 'prev_state', 'ctype', 'is_array', 'map_type'])
PropStateInfo = collections.namedtuple(
    'PropStateInfo', ['name', 'next_state'])


class Service(service.Service):
  def __init__(self, service, outfname, headerfname, options):
    self.outfname = outfname
    self.options = options
    self.headerfname = headerfname
    self.schema = None
    self.schema_level = 0
    self.decf = cStringIO.StringIO()
    self.deff = cStringIO.StringIO()
    super(Service, self).__init__(service)

  @property
  def state(self):
    return StateFromContextStack(self.schema.context_stack)

  @property
  def prev_state(self):
    return StateFromContextStack(self.schema.context_stack[:-1])

  @property
  def non_key_state(self):
    stack_copy = self.schema.context_stack[:]
    while stack_copy and not stack_copy[-1][1]:
      stack_copy.pop()
    return StateFromContextStack(stack_copy)

  @property
  def cident(self):
    return CIdentFromContextStack(self.schema.context_stack)

  @property
  def is_array_state(self):
    return self.schema.context_stack[-1][1] == 'array'

  def PushContext(self, name, typ):
    self.schema.context_stack.append((name, typ))
    self.schema.states.add(self.state)

  def PopContext(self):
    self.schema.context_stack.pop()

  def BeginService(self, name, version):
    pass

  def EndService(self, name, version):
    with open(self.outfname, 'w') as outf:
      header = self.headerfname
      outf.write(RunTemplateString(SOURCE_HEAD, vars()))
      outf.write(self.decf.getvalue())
      outf.write(self.deff.getvalue())
      outf.write(RunTemplateString(SOURCE_FOOT, vars()))

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

  def EndProperty(self, prop_name, prop):
    self.PopContext()

  def OnPropertyTypeRef(self, prop_name, prop, ref):
    cident = self.cident
    is_array = self.is_array_state
    assert self.state not in self.schema.map_states
    self.schema.map_states[self.state] = \
        RefStateInfo(cident, self.non_key_state, ref, ref + 'Callbacks', is_array, 'ref')

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    # TODO(binji): handle any
    ctype = service.TYPE_DICT[(prop_type, prop_format)]
    data = PrimitiveStateInfo(self.cident, self.non_key_state, ctype, self.is_array_state)
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
    current_state = self.state
    prev_state = self.non_key_state
    cident = self.cident
    self.PushContext(None, 'array')
    next_state = self.state
    assert current_state not in self.schema.array_states
    self.schema.array_states[current_state] = \
        ArrayStateInfo(cident, next_state, prev_state)

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    self.PopContext()

  def BeginPropertyTypeObject(self, prop_name, prop):
    cident = self.cident
    prev_state = self.non_key_state
    basename = gapi_utils.CapWords(prop_name)
    ctype = basename + 'Object'
    current_state = self.state
    is_array = self.is_array_state
    self.PushContext(None, 'object')
    next_state = self.state
    assert self.state not in self.schema.map_states
    self.schema.map_states[current_state] = \
        ObjectStateInfo(cident, next_state, prev_state, ctype, is_array, 'object')

  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    self.PopContext()
