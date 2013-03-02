#!/usr/bin/env python
import collections
import copy
import cStringIO
import itertools
import json
import os
import re
import sys
import urllib2

from easy_template import RunTemplateString
import gapi_utils

DISCOVERY_API = 'https://www.googleapis.com/discovery/v1/apis'
API_JSON = 'out/api.json'

TYPE_DICT = {
  ('any', ''): 'std::string',
  ('boolean', ''): 'bool',
  ('integer', 'int32'): 'int32_t',
  ('integer', 'uint32'): 'uint32_t',
  ('number', 'double'): 'double',
  ('number', 'float'): 'float',
  ('string', 'byte'): 'std::vector<uint8_t>',  # byte array
  ('string', 'date'): 'std::string',
  ('string', 'date-time'): 'std::string',
  ('string', 'int64'): 'int64_t',
  ('string', ''): 'std::string',
  ('string', 'uint64'): 'uint64_t',
}


def WriteWrappedComment(f, s, indent, length):
  lines = gapi_utils.WrapLine(s, length - (len(indent) + len('// ')))
  for line in lines:
    f.write('%s// %s\n' % (indent, line))


def WriteJsonComment(f, d, indent, length):
  for line in json.dumps(d, indent=2).splitlines():
    lines = gapi_utils.WrapLine(line, length - (len(indent) + len('// ')), True)
    for wrapped_line in lines:
      f.write('%s// %s\n' % (indent, wrapped_line))


class Service(object):
  def __init__(self, data):
    self.data = data
    self._Run()

  @property
  def name(self):
    return self.data['name']

  @property
  def version(self):
    return self.data['version']

  def _Run(self):
    self.BeginService(self.name, self.version)
    if 'schemas' in self.data:
      for schema_name, schema in sorted(self.data['schemas'].iteritems()):
        self.OnSchema(schema_name, schema)
    self.EndService(self.name, self.version)

  def BeginService(self, name, version): pass
  def EndService(self, name, version): pass

  def OnSchema(self, schema_name, schema):
    self.BeginSchema(schema_name, schema)
    if 'properties' in schema:
      for prop_name, prop in sorted(schema['properties'].iteritems()):
        self.OnProperty(prop_name, prop)
    if 'additionalProperties' in schema:
      prop_name = '_additionalProperties'
      prop = schema['additionalProperties']
      self.OnProperty(prop_name, prop)
    self.EndSchema(schema_name, schema)

  def BeginSchema(self, schema_name, schema): pass
  def EndSchema(self, schema_name, schema): pass

  def OnProperty(self, prop_name, prop):
    self.BeginProperty(prop_name, prop)
    self.OnPropertyType(prop_name, prop)
    if 'description' in prop:
      desc = prop['description'].encode('ascii', 'replace')
      self.OnPropertyComment(prop_name, prop, desc)
    self.EndProperty(prop_name, prop)

  def BeginProperty(self, prop_name, prop): pass
  def EndProperty(self, prop_name, prop): pass
  def OnPropertyComment(self, prop_name, prop, comment): pass

  def OnPropertyType(self, prop_name, prop):
    self.BeginPropertyType(prop_name, prop)
    if 'type' in prop or 'format' in prop:
      prop_type = prop.get('type', '')
      if prop_type == 'array':
        self.OnPropertyTypeArray(prop_name, prop, prop['items'])
      elif prop_type == 'object':
        self.OnPropertyTypeObject(prop_name, prop)
      else:
        prop_format = prop.get('format', '')
        self.OnPropertyTypeFormat(prop_name, prop, prop_type, prop_format)
    elif '$ref' in prop:
      self.OnPropertyTypeRef(prop_name, prop, prop['$ref'])
    self.EndPropertyType(prop_name, prop)

  def BeginPropertyType(self, prop_name, prop): pass
  def EndPropertyType(self, prop_name, prop): pass
  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format): pass
  def OnPropertyTypeRef(self, prop_name, prop, ref): pass

  def OnPropertyTypeArray(self, prop_name, prop, prop_items):
    self.BeginPropertyTypeArray(prop_name, prop, prop_items)
    self.OnPropertyType(prop_name, prop_items)
    self.EndPropertyTypeArray(prop_name, prop, prop_items)

  def BeginPropertyTypeArray(self, prop_name, prop, prop_items): pass
  def EndPropertyTypeArray(self, prop_name, prop, prop_items): pass

  def OnPropertyTypeObject(self, prop_name, prop):
    schema_name = self.BeginPropertyTypeObject(prop_name, prop)
    if not schema_name:
      schema_name = prop_name
    self.OnSchema(schema_name, prop)
    self.EndPropertyTypeObject(prop_name, prop, schema_name)

  def BeginPropertyTypeObject(self, prop_name, prop): pass
  def EndPropertyTypeObject(self, prop_name, prop, schema_name): pass


HEADER_HEAD = """\
#ifndef {{include_guard}}
#define {{include_guard}}

#include <map>
#include <tr1/memory>
#include <vector>
#include <string>

[[for schema in self.toplevel_schemas:]]
struct {{schema}};
[[]]

[[for schema in self.toplevel_schemas:]]
bool Decode(JsonParser* p, {{schema}}* out_data);
[[]]

"""

HEADER_FOOT = """\
#endif  // {{include_guard}}
"""

HEADER_SCHEMA_HEAD = """\
struct {{schema_name}} {
"""

HEADER_SCHEMA_FOOT = """\
};

"""

class CHeaderService(Service):
  def __init__(self, service):
    self.f = cStringIO.StringIO()
    self.indent = ''
    self.prop_stack = []
    self.schema_stack = []
    self.toplevel_schemas = []
    super(CHeaderService, self).__init__(service)

  def EndService(self, name, version):
    with open('out/%s_%s.h' % (name, version), 'w') as outf:
      include_guard = gapi_utils.MakeIncludeGuard(name, version)
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
    self.prop_stack.append('')

  def EndProperty(self, prop_name, prop):
    self.f.write('%s%s %s;\n\n' % (
        self.indent,
        self.prop_stack[-1],
        gapi_utils.SnakeCase(prop_name)))
    self.prop_stack.pop()

  def OnPropertyComment(self, prop_name, prop, comment):
    for line in comment.splitlines():
      WriteWrappedComment(self.f, line, self.indent, 80)

  def OnPropertyTypeRef(self, prop_name, prop, ref):
    self.prop_stack[-1] = gapi_utils.WrapType('std::tr1::shared_ptr<%s>', ref)

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    self.prop_stack[-1] = TYPE_DICT[(prop_type, prop_format)]

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    item_type = self.prop_stack[-1]
    self.prop_stack[-1] = gapi_utils.WrapType('std::vector<%s>', item_type)

  def BeginPropertyTypeObject(self, prop_name, prop):
    return gapi_utils.CapWords(prop_name + 'Object')

  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    self.prop_stack[-1] = schema_name


SOURCE_HEAD = """\
#include "{{header}}"
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <vector>
#include "json_parser.h"
#include "json_parser_macros.h"

"""

SOURCE_FOOT = """\
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
  virtual int OnNull(JsonParser* p);
  virtual int OnBool(JsonParser* p, bool value);
  virtual int OnNumber(JsonParser* p, const char* s, size_t length);
  virtual int OnString(JsonParser* p, const unsigned char* s, size_t length);
  virtual int OnStartMap(JsonParser* p);
  virtual int OnMapKey(JsonParser* p, const unsigned char* s, size_t length);
  virtual int OnEndMap(JsonParser* p);
  virtual int OnStartArray(JsonParser* p);
  virtual int OnEndArray(JsonParser* p);

 private:
  {{sub_schema.ctype}}* data_;
  int state_;
};

"""

SOURCE_SCHEMA_DEF = """\

bool Decode(JsonParser* p, {{sub_schema.ctype}}* out_data) {
  p->PushCallbacks(new {{sub_schema.cbtype}}(out_data));
  p->Decode();
}

{{sub_schema.cbtype}}::{{sub_schema.base_cbtype}}({{sub_schema.ctype}}* data)
    : data_(data) {
}

int {{sub_schema.cbtype}}::OnNull(JsonParser* p) {
  return 0;
}

int {{sub_schema.cbtype}}::OnBool(JsonParser* p, bool value) {
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
      return 0;
  }
[[else:]]
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnNumber(JsonParser* p, const char* s, size_t length) {
[[if sub_schema.number_states:]]
  char* endptr;
  char buffer[32];
  strncpy(&buffer[0], s, length);
  switch (state_) {
[[  for state, (cident, ctype, is_array) in sorted(sub_schema.number_states.iteritems()):]]
[[    prefix = 'APPEND' if is_array else 'SET']]
[[    if ctype == "int32_t":]]
    case {{state}}:
      {{prefix}}_INT32_AND_RETURN({{cident}});
[[    elif ctype == "uint32_t":]]
    case {{state}}:
      {{prefix}}_UINT32_AND_RETURN({{cident}});
[[    elif ctype == "int64_t":]]
    case {{state}}:
      {{prefix}}_INT64_AND_RETURN({{cident}});
[[    elif ctype == "uint64_t":]]
    case {{state}}:
      {{prefix}}_UINT64_AND_RETURN({{cident}});
[[    elif ctype == "float":]]
    case {{state}}:
      {{prefix}}_FLOAT_AND_RETURN({{cident}});
[[    elif ctype == "double":]]
    case {{state}}:
      {{prefix}}_DOUBLE_AND_RETURN({{cident}});
[[  ]]
    default:
      return 0;
  }
[[else:]]
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnString(JsonParser* p, const unsigned char* s, size_t length) {
[[if sub_schema.string_states:]]
  switch (state_) {
[[  for state, (cident, ctype, is_array) in sorted(sub_schema.string_states.iteritems()):]]
    case {{state}}:
[[    if is_array:]]
      APPEND_STRING_AND_RETURN({{cident}});
[[    else:]]
      SET_STRING_AND_RETURN({{cident}});
[[  ]]
    default:
      return 0;
  }
[[else:]]
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnStartMap(JsonParser* p) {
[[if sub_schema.map_states:]]
  switch (state_) {
[[  for state, (cident, ctype, is_array, map_type) in sorted(sub_schema.map_states.iteritems()):]]
    case {{state}}: {
[[    if map_type == 'ref':]]
[[      if is_array:]]
      PUSH_CALLBACK_REF_ARRAY({{ctype}}, {{cident}});
[[      else:]]
      PUSH_CALLBACK_REF({{ctype}}, {{cident}});
[[    elif map_type == 'object':]]
[[      if is_array:]]
      PUSH_CALLBACK_OBJECT_ARRAY({{ctype}}, {{cident}});
[[      else:]]
      PUSH_CALLBACK_OBJECT({{ctype}}, {{cident}});
[[    ]]
      return 1;
    }
[[  ]]
    default:
      return 0;
  }
[[else:]]
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnMapKey(JsonParser* p, const unsigned char* s, size_t length) {
  if (length == 0) return 0;
  switch (s[0]) {
[[for first_char, group in groupby(sorted(sub_schema.props), lambda p:p[0][0]):]]
    case '{{first_char}}':
[[  # Sort group in reverse order of name length.]]
[[  group = sorted(group, lambda x,y: cmp(len(y[0]), len(x[0])))]]
[[  for prop_name, next_state in group:]]
      CHECK_MAP_KEY("{{prop_name}}", {{len(prop_name)}}, {{next_state}});
[[  ]]
      return 0;
[[]]
    default:
      return 0;
  }
}

int {{sub_schema.cbtype}}::OnEndMap(JsonParser* p) {
  if (state_ != STATE_TOP)
    return 0;
  return p->PopCallbacks() ? 1 : 0;
}

int {{sub_schema.cbtype}}::OnStartArray(JsonParser* p) {
[[if sub_schema.array_states:]]
  switch (state_) {
[[  for state, (next_state, prev_state) in sub_schema.array_states.iteritems():]]
    case {{state}}:
      state_ = {{next_state}};
      return 1;
[[  ]]
    default:
      return 0;
  }
[[else:]]
  return 0;
[[]]
}

int {{sub_schema.cbtype}}::OnEndArray(JsonParser* p) {
[[if sub_schema.array_states:]]
  switch (state_) {
[[  for state, (next_state, prev_state) in sub_schema.array_states.iteritems():]]
    case {{next_state}}:
      state_ = {{prev_state}};
      return 1;
[[  ]]
    default:
      return 0;
  }
[[else:]]
  return 0;
[[]]
}

"""


class SchemaInfo(object):
  def __init__(self, schema_name=None, parent_cbtype=None):
    if schema_name:
      cap = gapi_utils.CapWords(schema_name)
      self.base_cbtype = '%sCallbacks' % cap
      if parent_cbtype:
        self.cbtype = '%s::%s' % (parent_cbtype, self.base_cbtype)
        self.ctype = '%sObject' % cap
      else:
        self.cbtype = self.base_cbtype
        self.ctype = cap
    else:
      self.cbtype = ''
      self.base_cbtype = ''
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


class CSourceService(Service):
  def __init__(self, service):
    self.schema_stack = [SchemaInfo()]
    super(CSourceService, self).__init__(service)

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
    with open('out/%s_%s.cc' % (name, version), 'w') as outf:
      header = '%s_%s.h' % (name, version)
      outf.write(RunTemplateString(SOURCE_HEAD, vars()))
      outf.write(self.schema.decf.getvalue())
      outf.write(self.schema.deff.getvalue())
      outf.write(RunTemplateString(SOURCE_FOOT, vars()))

  def BeginSchema(self, schema_name, schema):
    schema_info = SchemaInfo(schema_name, self.schema.cbtype)
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
    self.schema.map_states[self.state] = (cident, ref, is_array, 'ref')

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    # TODO(binji): handle any
    cident = gapi_utils.SnakeCase(prop_name)
    ctype = TYPE_DICT[(prop_type, prop_format)]
    is_array = self.state.endswith('_A')
    data = (cident, ctype, is_array)
    if prop_type in ['number', 'integer'] or \
        (prop_type == 'string' and 'int' in prop_format):
      # Number
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

  def BeginPropertyTypeObject(self, prop_name, prop):
    cident = gapi_utils.SnakeCase(prop_name)
    ctype = gapi_utils.CapWords(prop_name)
    is_array = self.state.endswith('_A')
    assert self.state not in self.schema.map_states
    self.schema.map_states[self.state] = (cident, ctype, is_array, 'object')

  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    pass


def ReadCachedJson(url, filename):
  if os.path.exists(filename):
    return json.loads(open(filename).read())
  with open(filename, 'w') as outf:
    try:
      inf = urllib2.urlopen(url)
      data = inf.read()
      outf.write(data)
    finally:
      inf.close()
  return json.loads(data)


def main(args):
  d = ReadCachedJson(DISCOVERY_API, API_JSON)
  for item in d['items']:
    json_name = 'out/%s_%s.json' % (item['name'], item['version'])
    service = ReadCachedJson(item['discoveryRestUrl'], json_name)
    CHeaderService(service)
    CSourceService(service)


if __name__ == '__main__':
  main(sys.argv[1:])
