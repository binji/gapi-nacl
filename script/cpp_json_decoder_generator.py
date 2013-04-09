import collections
import itertools

from easy_template import RunTemplateString
import gapi_utils
import service


def Generate(outf, service):
  for schema in service.schemas.itervalues():
    _GenerateSchemaDeclaration(outf, schema)
  for schema in service.schemas.itervalues():
    _GenerateSchemaDefinition(outf, schema)


def _GenerateSchemaDeclaration(outf, schema):
  # TODO(binji): only create this once
  state_info = StateInfo(schema)
  outf.write(RunTemplateString(TEMPLATE_DECLARE_SCHEMA, vars()))

def _GenerateSchemaDefinition(outf, schema):
  state_info = StateInfo(schema)
  debug = False
  groupby = itertools.groupby
  ReferencePropertyType = service.ReferencePropertyType
  ObjectPropertyType = service.ObjectPropertyType
  outf.write(RunTemplateString(TEMPLATE_DEFINE_SCHEMA, vars()))


class StateInfo(object):
  def __init__(self, schema):
    self.states = set()
    self.array_states = {}
    self.bool_states = {}
    self.number_states = {}
    self.object_states = {}
    self.prop_key_states = collections.defaultdict(list)
    self.string_states = {}
    self.additional_properties_schemas = {}
    self._Load(schema)

  def _Load(self, schema):
    service.Iterate(schema, StateInfoCallbacks(self))


def _GetStateFromContext(context, non_key):
  # X K -> {X}{NAME}_K
  # X K A... -> {X}{NAME}_A
  # X K A... O -> {X}{NAME}_A...O
  state = ''
  is_first = True
  for item in reversed(context):
    if isinstance(item, service.Property):
      if is_first and not non_key:
        state = 'K'
      if not (is_first and non_key):
        state = '_%s_' % gapi_utils.Upper(item.name) + state
    elif isinstance(item, service.ArrayPropertyType):
      state = 'A' + state
    elif isinstance(item, service.ObjectPropertyType):
      state = 'O' + state
    else:
      continue
    is_first = False
  if not state:
    return 'STATE_TOP'
  return 'STATE' + state


def _GetAddlPropIteratorCIdent(schema):
  return gapi_utils.SnakeCase(schema.name) + '_iterator_'


def _GetCIdentFromContext(context):
  cident = ''
  is_first = True
  for item in reversed(context):
    if isinstance(item, service.Property):
      cident = item.base_cident + cident
      is_first = False
    elif isinstance(item, service.ArrayPropertyType):
      if not is_first:
        cident = '.back()' + cident
      is_first = False
    elif isinstance(item, service.ObjectPropertyType):
      cident = '.' + cident
      is_first = False
    if isinstance(item, service.PropertyType):
      if item.prop.is_additional_properties:
        iter_name = _GetAddlPropIteratorCIdent(item.prop.schema)
        return '%s->second%s' % (iter_name, cident)
  return 'data_->' + cident


class StateInfoCallbacks(service.ServiceCallbacks):
  def __init__(self, state_info):
    self.state_info = state_info

  def GetState(self, obj):
    return self._GetState(obj.GetContext(), non_key=False)

  def GetNonKeyState(self, obj):
    return self._GetState(obj.GetContext(), non_key=True)

  def _GetState(self, context, non_key):
    state = _GetStateFromContext(context, non_key)
    self.state_info.states.add(state)
    return state

  def GetCIdent(self, obj):
    return _GetCIdentFromContext(obj.GetContext())

  def BeginSchema(self, schema):
    if schema.additional_properties:
      info = AddlPropInfo(schema, _GetAddlPropIteratorCIdent(schema))
      self.state_info.additional_properties_schemas[schema.name] = info

  def BeginProperty(self, prop):
    # ... X K -> {state: X, next: K}
    state = self.GetState(prop.schema)
    next_state = self.GetState(prop)
    cident = self.GetCIdent(prop)
    iter_ident = _GetAddlPropIteratorCIdent(prop.schema)
    info = PropInfo(prop, next_state, cident, iter_ident)
    self.state_info.prop_key_states[state].append(info)

  def PrimitivePropertyType(self, prop_type):
    # ... X K -> {state: K, prev: X}
    # ... X A -> {state: A, prev: A}
    prev_state = self.GetNonKeyState(prop_type)
    state = self.GetState(prop_type)
    cident = self.GetCIdent(prop_type)
    typ, fmt = prop_type.type_format
    info = Info(prop_type, cident, None, prev_state)
    if typ in ('number', 'integer'):
      self.state_info.number_states[state] = info
    elif typ == 'boolean':
      self.state_info.bool_states[state] = info
    elif typ == 'string':
      self.state_info.string_states[state] = info

  def BeginArrayPropertyType(self, prop_type):
    # ... X K A -> {state: K, next: A, prev: X}
    # ... A1 A2 -> {state: A1, next: A2, prev: A1}
    state = self.GetState(prop_type.parent)
    next_state = self.GetState(prop_type)
    prev_state = self.GetNonKeyState(prop_type.parent)
    cident = self.GetCIdent(prop_type.parent)
    self.state_info.array_states[state] = \
        Info(prop_type, cident, next_state, prev_state)

  def BeginObjectPropertyType(self, prop_type):
    # ... X K O -> {state: K, next: O, prev: X}
    # ... A O -> {state: A, next: O, prev: A}
    state = self.GetState(prop_type.parent)
    next_state = self.GetState(prop_type)
    prev_state = self.GetNonKeyState(prop_type.parent)
    cident = self.GetCIdent(prop_type.parent)
    self.state_info.object_states[state] = \
        Info(prop_type, cident, next_state, prev_state)

  def ReferencePropertyType(self, prop_type):
    # ... X K -> {state: K, prev: X}
    # ... X A -> {state: A, prev: A}
    prev_state = self.GetNonKeyState(prop_type)
    state = self.GetState(prop_type)
    cident = self.GetCIdent(prop_type)
    self.state_info.object_states[state] = \
        Info(prop_type, cident, None, prev_state)

Info = collections.namedtuple(
    'Info', ['prop_type', 'cident', 'next_state', 'prev_state'])
PropInfo = collections.namedtuple(
    'PropInfo', ['prop', 'next_state', 'cident', 'iter_ident'])
AddlPropInfo = collections.namedtuple('AddlPropInfo', ['schema', 'cident'])


TEMPLATE_DECLARE_SCHEMA = """\
class {{schema.cbtype}} : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
[[for state in sorted(state_info.states):]]
    {{state}},
[[]]
  };

  explicit {{schema.cbtype}}({{schema.ctype}}* data);
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
  {{schema.ctype}}* data_;
[[for schema_name, info in state_info.additional_properties_schemas.iteritems():]]
  {{info.schema.additional_properties.ctypedef}}::iterator {{info.cident}};
[[]]
  int state_;
};

"""


TEMPLATE_DEFINE_SCHEMA = """\

void Decode(Reader* src, {{schema.ctype}}* out_data, ErrorPtr* error) {
  JsonParser p;
  p.PushCallbacks(new {{schema.cbtype}}(out_data));
  p.Decode(src, error);
}

{{schema.cbtype}}::{{schema.cbtype}}({{schema.ctype}}* data)
    : data_(data),
      state_(STATE_NONE) {
}

int {{schema.cbtype}}::OnNull(JsonParser* p, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnNull()\\n");
[[]]
  error->reset(new MessageError("Unexpected null"));
  return 0;
}

int {{schema.cbtype}}::OnBool(JsonParser* p, bool value, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnBool(%d) %d\\n", value, state_);
[[]]
[[if state_info.bool_states:]]
  switch (state_) {
[[  for state, info in sorted(state_info.bool_states.iteritems()):]]
    case {{state}}:
[[    if info.prop_type.is_parent_array:]]
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

int {{schema.cbtype}}::OnNumber(JsonParser* p, const char* s, size_t length, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnNumber(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
[[if state_info.number_states:]]
  char* endptr;
  char buffer[kMaxNumberBufferSize];
  size_t nbytes = std::min(kMaxNumberBufferSize - 1, length);
  strncpy(&buffer[0], s, nbytes);
  buffer[nbytes] = 0;
  switch (state_) {
[[  for state, info in sorted(state_info.number_states.iteritems()):]]
[[    prefix = 'APPEND' if info.prop_type.is_parent_array else 'SET']]
[[    optional_state = '' if info.prop_type.is_parent_array else ', ' + info.prev_state]]
    case {{state}}:
[[    if info.prop_type.ctype == "int32_t":]]
      {{prefix}}_INT32_AND_RETURN({{info.cident}}{{optional_state}});
[[    elif info.prop_type.ctype == "uint32_t":]]
      {{prefix}}_UINT32_AND_RETURN({{info.cident}}{{optional_state}});
[[    elif info.prop_type.ctype == "float":]]
      {{prefix}}_FLOAT_AND_RETURN({{info.cident}}{{optional_state}});
[[    elif info.prop_type.ctype == "double":]]
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

int {{schema.cbtype}}::OnString(JsonParser* p, const unsigned char* s, size_t length, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnString(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
[[if state_info.string_states:]]
[[  if any(info.prop_type.ctype in ("int64_t", "uint64_t") for info in state_info.string_states.values()):]]
  char* endptr;
  char buffer[kMaxNumberBufferSize];
  size_t nbytes = std::min(kMaxNumberBufferSize - 1, length);
  strncpy(&buffer[0], reinterpret_cast<const char*>(s), nbytes);
  buffer[nbytes] = 0;
[[  ]]
  switch (state_) {
[[  for state, info in sorted(state_info.string_states.iteritems()):]]
[[    prefix = 'APPEND' if info.prop_type.is_parent_array else 'SET']]
[[    optional_state = '' if info.prop_type.is_parent_array else ', ' + info.prev_state]]
    case {{state}}:
[[    if info.prop_type.ctype == "int64_t":]]
      {{prefix}}_INT64_AND_RETURN({{info.cident}}{{optional_state}});
[[    elif info.prop_type.ctype == "uint64_t":]]
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

int {{schema.cbtype}}::OnMapKey(JsonParser* p, const unsigned char* s, size_t length, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnMapKey(%.*s) %d\\n", static_cast<int>(length), s, state_);
[[]]
  if (length == 0) return 0;
  switch (state_) {
[[for state, info in sorted(state_info.prop_key_states.iteritems()):]]
    case {{state}}:
[[  for prop, next_state, _, _ in sorted(info):]]
[[    if not prop.is_additional_properties:]]
      CHECK_MAP_KEY("{{prop.name}}", {{len(prop.name)}}, {{next_state}});
[[  for prop, next_state, cident, iter_ident in info:]]
[[    if prop.is_additional_properties:]]
      MAP_KEY_ADDL_PROPS({{cident}}, {{prop.ctypedef}}, {{iter_ident}}, {{next_state}});
[[  ]]
      break;
[[  ]]
[[]]
    default: break;
  }
  error->reset(new MessageError("Unknown map key"));
  return 0;
}

int {{schema.cbtype}}::OnStartMap(JsonParser* p, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnStartMap() %d\\n", state_);
[[]]
  switch (state_) {
    case STATE_NONE:
      state_ = STATE_TOP;
      return 1;
[[if state_info.object_states:]]
[[  for state, info in sorted(state_info.object_states.iteritems()):]]
    case {{state}}:
[[    if isinstance(info.prop_type, ReferencePropertyType):]]
[[      if info.prop_type.is_parent_array:]]
      PUSH_CALLBACK_REF_ARRAY_AND_RETURN({{info.prop_type.referent.ctype}}, {{info.prop_type.referent.cbtype}}, {{info.cident}});
[[      else:]]
      PUSH_CALLBACK_REF_AND_RETURN({{info.prop_type.referent.ctype}}, {{info.prop_type.referent.cbtype}}, {{info.cident}});
[[    elif isinstance(info.prop_type, ObjectPropertyType):]]
[[      if info.prop_type.is_parent_array:]]
      {{info.cident}}.push_back({{info.prop_type.ctype}}());
[[      ]]
      state_ = {{info.next_state}};
      return 1;
[[]]
    default:
      error->reset(new MessageError("Unexpected state"));
      return 0;
  }
}

int {{schema.cbtype}}::OnEndMap(JsonParser* p, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnEndMap() %d\\n", state_);
[[]]
  switch (state_) {
    case STATE_TOP:
      if (p->PopCallbacks())
        return p->HasCallbacks() ? p->OnEndMap() : 1;
      error->reset(new MessageError("Unexpected end of map"));
      return 0;
[[if state_info.object_states:]]
[[  for state, info in sorted(state_info.object_states.iteritems()):]]
[[    if isinstance(info.prop_type, ReferencePropertyType):]]
    case {{state}}:
      state_ = {{info.prev_state}};
      return 1;
[[    elif isinstance(info.prop_type, ObjectPropertyType):]]
    case {{info.next_state}}:
      state_ = {{info.prev_state}};
      return 1;
[[]]
    default:
      error->reset(new MessageError("Unexpected state"));
      return 0;
  }
}

int {{schema.cbtype}}::OnStartArray(JsonParser* p, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnStartArray() %d\\n", state_);
[[]]
[[if state_info.array_states:]]
  switch (state_) {
[[  for state, info in state_info.array_states.iteritems():]]
    case {{state}}:
[[    if info.prop_type.is_parent_array:]]
      {{info.cident}}.push_back({{info.prop_type.ctype}}());
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

int {{schema.cbtype}}::OnEndArray(JsonParser* p, ErrorPtr* error) {
[[if debug:]]
  printf("{{schema.cbtype}}::OnEndArray() %d\\n", state_);
[[]]
[[if state_info.array_states:]]
  switch (state_) {
[[  for state, info in state_info.array_states.iteritems():]]
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
