#!/usr/bin/env python
import cStringIO
import json
import optparse
import os
import sys
import urllib2

import cpp_header_generator
import cpp_source_generator
import service


DISCOVERY_API = 'https://www.googleapis.com/discovery/v1/apis'
API_JSON = 'out/api.json'


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
  parser = optparse.OptionParser()
  parser.add_option('-o', dest='outbasename')
  parser.add_option('-n', '--namespace')
  parser.add_option('-d', '--debug', action='store_true')
  options, args = parser.parse_args(args)

  inputs = []
  if args:
    if len(args) > 1:
      print 'Ignoring additional args: %s' % ', '.join(args[1:])
    if not options.outbasename:
      parser.error('no output file given.')
    with open(args[0]) as inf:
      service_json = json.load(inf)
    inputs.append((options.outbasename, service_json))
  else:
    # Read and generate for all descovery APIs.
    d = ReadCachedJson(DISCOVERY_API, API_JSON)
    for item in d['items']:
      basename = 'out/%s_%s' % (item['name'], item['version'])
      service_json = ReadCachedJson(item['discoveryRestUrl'], basename + '.json')
      inputs.append((basename, service_json))

  for basename, service_json in inputs:
    header_name = basename + '.h'
    source_name = basename + '.cc'
    s = service.Service(service_json)
#    Generate(cpp_header_generator, header_name, s,
#             header_name=header_name,
#             namespace=options.namespace)
#    Generate(cpp_source_generator, source_name, s,
#             header_name=header_name,
#             namespace=options.namespace)


def Generate(generator, outfname, service, **kwargs):
  outf = cStringIO.StringIO()
  generator.Generate(outf, service, **kwargs)
  with open(outfname, 'w') as real_outf:
    real_outf.write(outf.getvalue())


if __name__ == '__main__':
  main(sys.argv[1:])
