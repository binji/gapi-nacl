#!/usr/bin/env python
import json
import os
import re
import sys
import urllib2

import gapi_utils

DISCOVERY_API = 'https://www.googleapis.com/discovery/v1/apis'
API_JSON = 'api.json'

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


class CHeaderService(Service):
  def __init__(self, service):
    self.f = None
    self.indent = ''
    self.prop_stack = []
    super(CHeaderService, self).__init__(service)
  def BeginService(self, name, version):
    self.f = open('out/%s_%s.h' % (name, version), 'w')
  def EndService(self, name, version):
    self.f.close()
  def BeginSchema(self, schema_name, schema):
    self.f.write('%sstruct %s {\n' % (self.indent, schema_name))
    self.indent += '  '
  def EndSchema(self, schema_name, schema):
    WriteJsonComment(self.f, schema, self.indent, 80)
    self.indent = self.indent[:-2]
    self.f.write('%s};\n\n' % (self.indent,))
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
    self.prop_stack[-1] = gapi_utils.WrapType('std::shared_ptr<%s>', ref)
  def BeginPropertyType(self, prop_name, prop):
    pass
  def EndPropertyType(self, prop_name, prop):
    pass
  def OnPropertyTypeFormat(self, prop_name, prop, prop_type, prop_format):
    self.prop_stack[-1] = TYPE_DICT[(prop_type, prop_format)]
  def BeginPropertyTypeArray(self, prop_name, prop, prop_items):
    pass
  def EndPropertyTypeArray(self, prop_name, prop, prop_items):
    item_type = self.prop_stack[-1]
    self.prop_stack[-1] = gapi_utils.WrapType('std::vector<%s>', item_type)
  def BeginPropertyTypeObject(self, prop_name, prop):
    return gapi_utils.CapWords(prop_name + 'Object')
  def EndPropertyTypeObject(self, prop_name, prop, schema_name):
    self.prop_stack[-1] = schema_name


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
    json_name = '%s_%s.json' % (item['name'], item['version'])
    service = ReadCachedJson(item['discoveryRestUrl'], json_name)
    CHeaderService(service)


if __name__ == '__main__':
  main(sys.argv[1:])
