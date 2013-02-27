#!/usr/bin/env python
import collections
import cStringIO
import easy_template
import json
import os
import re
import sys
import urllib2

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

"""

HEADER_FOOT = """\
#endif  // {{include_guard}}
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
      outf.write(easy_template.RunTemplateString(HEADER_HEAD, vars()))
      outf.write(self.f.getvalue())
      outf.write(easy_template.RunTemplateString(HEADER_FOOT, vars()))

  def BeginSchema(self, schema_name, schema):
    if not self.schema_stack:
      self.toplevel_schemas.append(schema_name)
    self.schema_stack.append(schema_name)
    self.f.write('%sstruct %s {\n' % (self.indent, schema_name))
    self.indent += '  '

  def EndSchema(self, schema_name, schema):
    WriteJsonComment(self.f, schema, self.indent, 80)
    self.indent = self.indent[:-2]
    self.f.write('%s};\n\n' % (self.indent,))
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
#include <stdlib.h>
#include <string.h>
#include <vector>
#include "json_parser.h"

"""

SOURCE_FOOT = """\
"""

SOURCE_SCHEMA = """\
class {{schema_name}}Callbacks : public JsonCallbacks {
 public:
  enum {
    STATE_NONE,
    STATE_TOP,
[[for state in sorted(self.schema.states):]]
    {{state}},
[[]]
  };

  explicit {{schema_name}}Callbacks({{schema_name}}* data);
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
  {{schema_name}}* data_;
};

{{schema_name}}Callbacks::{{schema_name}}Callbacks({{schema_name}}* data)
    : data_(data) {
}

int {{schema_name}}Callbacks::OnNull(JsonParser* p) {
  return 0;  // fail
}

int {{schema_name}}Callbacks::OnBool(JsonParser* p, bool value) {
  return 0;  // fail
}

int {{schema_name}}Callbacks::OnNumber(JsonParser* p, const char* s, size_t length) {
  char* endptr;
  char buffer[32];
  strncpy(&buffer[0], s, length);
  switch (top()) {
[[for state, props in self.schema.number_states.iteritems():]]
    case {{state}}:
[[  for prop_name, ctype in props:]]
      {{prop_name}} {{ctype}}
[[]]
    default:
      return 0;
  }
}

int {{schema_name}}Callbacks::OnString(JsonParser* p, const unsigned char* s, size_t length) {
  return 0;  // fail
}

int {{schema_name}}Callbacks::OnStartMap(JsonParser* p) {
  return 0;  // fail
}

int {{schema_name}}Callbacks::OnMapKey(JsonParser* p, const unsigned char* s, size_t length) {
  if (length == 0) return 0;
  switch (top()) {
[[for state, props in self.schema.state_props.iteritems():]]
    case {{state}}:
      switch (s[0]) {
[[  for prop_name, next_state in props:]]
        case '{{prop_name[0]}}':
          if (length != {{len(prop_name)}} ||
              strncmp(reinterpret_cast<const char*>(s), "{{prop_name}}", {{len(prop_name)}}) != 0)
            return 0;
          Push({{next_state}});
          return 1;
[[  ]]
        default:
          return 0;
      }
[[]]
    default:
      return 0;
  }
}

int {{schema_name}}Callbacks::OnEndMap(JsonParser* p) {
  return 0;  // fail
}

int {{schema_name}}Callbacks::OnStartArray(JsonParser* p) {
  return 0;  // fail
}

int {{schema_name}}Callbacks::OnEndArray(JsonParser* p) {
  return 0;  // fail
}

"""


class SchemaInfo(object):
  def __init__(self):
    self.states = set()
    self.null_states = collections.defaultdict(list)
    self.bool_states = collections.defaultdict(list)
    self.number_states = collections.defaultdict(list)
    self.string_states = collections.defaultdict(list)
    self.map_states = collections.defaultdict(list)
    self.array_states = collections.defaultdict(list)
    self.state_props = collections.defaultdict(list)


class CSourceService(Service):
  def __init__(self, service):
    self.f = cStringIO.StringIO()
    self.state_stack = []
    self.schema = SchemaInfo()

    self.schema_level = 0
    super(CSourceService, self).__init__(service)

  @property
  def state(self):
    if self.state_stack:
      return self.state_stack[-1]
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
    self.state_stack.append(new_state)

  def PopState(self):
    self.state_stack.pop()

  def BeginService(self, name, version):
    pass

  def EndService(self, name, version):
    with open('out/%s_%s.cc' % (name, version), 'w') as outf:
      header = '%s_%s.h' % (name, version)
      outf.write(easy_template.RunTemplateString(SOURCE_HEAD, vars()))
      outf.write(self.f.getvalue())
      outf.write(easy_template.RunTemplateString(SOURCE_FOOT, vars()))

  def BeginSchema(self, schema_name, schema):
    self.schema_level += 1

  def EndSchema(self, schema_name, schema):
    self.schema_level -= 1
    if not self.schema_level:
      # Process top-level schema
      self.f.write(easy_template.RunTemplateString(SOURCE_SCHEMA, vars()))
      # Reset schema info
      self.schema = SchemaInfo()

  def BeginProperty(self, prop_name, prop):
    current_state = self.state
    self.PushState(gapi_utils.Upper(prop_name))
    next_state = self.state
    self.schema.state_props[current_state].append((prop_name, next_state))

  def EndProperty(self, prop_name, prop):
    self.PopState()

  def OnPropertyTypeRef(self, prop_name, prop, ref):
    pass

  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    # TODO(binji): handle any
    ctype = TYPE_DICT[(prop_type, prop_format)]
    if prop_type in ['number', 'integer'] or \
        (prop_type == 'string' and 'int' in prop_format):
      # Number
      self.schema.number_states[self.state].append((prop_name, ctype))
    elif prop_type == 'boolean':
      self.schema.bool_states[self.state].append((prop_name, ctype))
    elif prop_type == 'string':
      self.schema.string_states[self.state].append((prop_name, ctype))

  def BeginPropertyTypeArray(self, prop_name, prop, prop_items):
    self.PushState('array')

  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    self.PopState()

  def BeginPropertyTypeObject(self, prop_name, prop):
    self.PushState('object')

  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    self.PopState()


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
