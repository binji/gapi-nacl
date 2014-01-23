import collections

import gapi_utils


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


def ParseNamedItems(data, key, out_dict, out_factory):
  for item_name, item_data in sorted(data.get(key, {}).iteritems()):
    assert item_name not in out_dict
    out_dict[item_name] = out_factory(item_name, item_data)


class Service(object):
  def __init__(self, data):
    self.schemas = {}
    self.resources = {}
    self._Parse(data)
    self._FixReferences()

  def Generator(self):
    for _, schema in sorted(self.schemas.iteritems()):
      for result in schema.Generator():
        yield result

  def _Parse(self, data):
    schema_factory = lambda n, d: Schema(None, n, d)
    ParseNamedItems(data, 'schemas', self.schemas, schema_factory)
    ParseNamedItems(data, 'resources', self.resources, Resource)

  def _FixReferences(self):
    for typ, data in self.Generator():
      if typ == 'ReferencePropertyType':
        # References always point to top-level schemas, so we can always find
        # them in the self.schemas dict.
        data.referent = self.schemas[data.referent_name]


class Schema(object):
  def __init__(self, parent_prop_type, name, data):
    self.name = name
    self.parent_prop_type = parent_prop_type
    self.properties = {}
    self.additional_properties = None
    self._Parse(data)

  def GetContext(self):
    if self.parent_prop_type:
      return self.parent_prop_type.GetContext() + [self]
    return [self]

  def Generator(self):
    yield 'BeginSchema', self
    for _, prop in sorted(self.properties.iteritems()):
      for result in prop.Generator():
        yield result
    if self.additional_properties:
      for result in self.additional_properties.Generator():
        yield result
    yield 'EndSchema', self

  def _Parse(self, data):
    property_factory = lambda n, d: Property(self, n, d)
    ParseNamedItems(data, 'properties', self.properties, property_factory)
    if 'additionalProperties' in data:
      self.additional_properties = Property(self, None,
                                            data['additionalProperties'])

  def __str__(self):
    return '<Schema %s>' % self.name

  @property
  def parent_schema(self):
    if self.parent_prop_type:
      return self.parent_prop_type.prop.schema
    return None

  @property
  def ctype(self):
    if self.parent_schema:
      return '%s::%s' % (self.parent_schema.ctype, self.base_ctype)
    return self.base_ctype

  @property
  def base_ctype(self):
    if self.parent_schema:
      return gapi_utils.CapWords(self.name) + 'Object'
    return gapi_utils.CapWords(self.name)

  @property
  def cbtype(self):
    return self.ctype + 'Callbacks'


class Property(object):
  def __init__(self, schema, name, data):
    self.is_additional_properties = name is None
    if name is None:
      self.name = '_additionalProperties'
    else:
      self.name = name
    self.schema = schema
    self.description = data.get('description', '').encode('ascii', 'replace')
    self.prop_type = MakePropertyType(self, None, data)

  def GetContext(self):
    return self.schema.GetContext() + [self]

  def Generator(self):
    yield 'BeginProperty', self
    for result in self.prop_type.Generator():
      yield result
    yield 'EndProperty', self

  def __str__(self):
    return '<Property %s>' % self.name

  @property
  def base_cident(self):
    if self.is_additional_properties:
      return '_additional_properties'
    else:
      return gapi_utils.SnakeCase(self.name)

  @property
  def ctype(self):
    if self.is_additional_properties:
      return gapi_utils.WrapType('std::map<std::string, %s>',
                                 self.prop_type.ctype)
    else:
      return self.prop_type.ctype

  @property
  def ctypedef(self):
    assert self.is_additional_properties
    return '%s::%s' % (self.schema.ctype, self.base_ctypedef)

  @property
  def base_ctypedef(self):
    assert self.is_additional_properties
    return 'AddlPropsType'


def MakePropertyType(prop, parent_prop_type, data):
  if 'type' in data or 'format' in data:
    prop_type = data.get('type', '')
    if prop_type == 'array':
      return ArrayPropertyType(prop, parent_prop_type, data['items'])
    elif prop_type == 'object':
      return ObjectPropertyType(prop, parent_prop_type, data)
    else:
      prop_format = data.get('format', '')
      return PrimitivePropertyType(prop, parent_prop_type,
                                   (prop_type, prop_format))
  elif '$ref' in data:
    return ReferencePropertyType(prop, parent_prop_type, data['$ref'])


class PropertyType(object):
  def __init__(self, prop, parent_prop_type):
    self.prop = prop
    self.parent_prop_type = parent_prop_type
    if self.parent_prop_type:
      self.parent = self.parent_prop_type
    else:
      self.parent = self.prop

  def GetContext(self):
    return self.parent.GetContext() + [self]

  def GetPrevContext(self):
    return self.GetContext()[:-1]

  @property
  def is_parent_array(self):
    if self.parent_prop_type:
      return isinstance(self.parent_prop_type, ArrayPropertyType)
    return False


class PrimitivePropertyType(PropertyType):
  def __init__(self, prop, parent_prop_type, type_format):
    super(PrimitivePropertyType, self).__init__(prop, parent_prop_type)
    self.type_format = type_format

  def Generator(self):
    yield 'PrimitivePropertyType', self

  def __str__(self):
    return '<PrimitivePropertyType %s>' % (self.type_format,)

  @property
  def ctype(self):
    return TYPE_DICT[self.type_format]


class ArrayPropertyType(PropertyType):
  def __init__(self, prop, parent_prop_type, items):
    super(ArrayPropertyType, self).__init__(prop, parent_prop_type)
    self.element_type = MakePropertyType(prop, self, items)

  def Generator(self):
    yield 'BeginArrayPropertyType', self
    for result in self.element_type.Generator():
      yield result
    yield 'EndArrayPropertyType', self

  def __str__(self):
    return '<ArrayPropertyType %s>' % self.element_type

  @property
  def ctype(self):
    return gapi_utils.WrapType('std::vector<%s>', self.element_type.ctype)


class ObjectPropertyType(PropertyType):
  def __init__(self, prop, parent_prop_type, data):
    super(ObjectPropertyType, self).__init__(prop, parent_prop_type)
    self.schema = Schema(self, self.prop.name, data)

  def Generator(self):
    yield 'BeginObjectPropertyType', self
    for result in self.schema.Generator():
      yield result
    yield 'EndObjectPropertyType', self

  def __str__(self):
    return '<ObjectPropertyType %s>' % self.schema

  @property
  def ctype(self):
    return self.schema.ctype


class ReferencePropertyType(PropertyType):
  def __init__(self, prop, parent_prop_type, referent_name):
    super(ReferencePropertyType, self).__init__(prop, parent_prop_type)
    self.referent_name = referent_name
    self.referent = None

  def Generator(self):
    yield 'ReferencePropertyType', self

  def __str__(self):
    return '<ReferencePropertyType %s>' % self.referent

  @property
  def ctype(self):
    return gapi_utils.WrapType('std::tr1::shared_ptr<%s>', self.referent.ctype)


def Iterate(obj, callbacks):
  for typ, data in obj.Generator():
    getattr(callbacks, typ)(data)


class ServiceCallbacks(object):
  def BeginSchema(self, schema): pass
  def EndSchema(self, schema): pass
  def BeginProperty(self, prop): pass
  def EndProperty(self, prop): pass
  def PrimitivePropertyType(self, prop_type): pass
  def BeginArrayPropertyType(self, prop_type): pass
  def EndArrayPropertyType(self, prop_type): pass
  def BeginObjectPropertyType(self, prop_type): pass
  def EndObjectPropertyType(self, prop_type): pass
  def ReferencePropertyType(self, prop_type): pass


class Resource(object):
  def __init__(self, name, data):
    self.name = name
    self.methods = {}
    self._Parse(data)

  def _Parse(self, data):
    method_factory = lambda n, d: Method(self, n, d)
    ParseNamedItems(data, 'methods', self.methods, method_factory)


class Method(object):
  def __init__(self, resource, name, data):
    self.resource = resource
    self.name = name
    self.path = data['path']
    self.http_method = data['httpMethod']
    self.description = data.get('description', '')
    self.request_name = data.get('request', {}).get('$ref')
    self.request = None
    self.response_name = data.get('response', {}).get('$ref')
    self.response = None

    self.parameters = {}
    parameter_factory = lambda n, d: MethodParameter(self, n, d)
    ParseNamedItems(data, 'parameters', self.parameters, parameter_factory)

    self.parameter_order = []
    for p in data.get('parameterOrder', []):
      self.parameter_order.append(self.parameters[p])

    self.scopes = data.get('scopes')
    self.supports_media_upload = data.get('supportsMediaUpload', False)
    self.supports_media_download = data.get('supportsMediaDownload', False)
    self.supports_subscription = data.get('supportsSubscription', False)

    skip = [
      'id',
      'description',
      'path',
      'httpMethod',
      'request',
      'response',
      'parameters',
      'parameterOrder',
      'scopes',
      'supportsMediaUpload',
      'supportsMediaDownload',
      'supportsSubscription',
    ]

    for key, value in data.iteritems():
      if key not in skip:
        print resource.name, name, '>>', key, value


class MethodParameter(object):
  def __init__(self, method, name, data):
    self.method = method
    self.name = name
    self.description = data.get('description', '')
    self.location = data['location']
    self.required = data.get('required', False)
    self.type_format = (data.get('type', ''), data.get('format', ''))
    self.pattern = data.get('pattern')
    self.minimum = data.get('minimum')
    self.maximum = data.get('maximum')
    self.default = data.get('default')
    self.repeated = data.get('repeated', False)
    enums = data.get('enum')
    enum_descs = data.get('enumDescriptions')
    if enums and enum_descs:
      self.enums = zip(enums, enum_descs)
