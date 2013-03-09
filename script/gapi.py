#!/usr/bin/env python
import json
import optparse
import os
import sys
import urllib2

import service
import header_service
import source_service


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
      service = json.load(inf)
    inputs.append((options.outbasename, service))
  else:
    # Read and generate for all descovery APIs.
    d = ReadCachedJson(DISCOVERY_API, API_JSON)
    for item in d['items']:
      basename = 'out/%s_%s' % (item['name'], item['version'])
      service = ReadCachedJson(item['discoveryRestUrl'], json_name)
      inputs.append((basename, service))

  for basename, service in inputs:
    basename = options.outbasename
    header_name = basename + '.h'
    source_name = basename + '.cc'
    header_service.Service(service, header_name, options).Run()
    source_service.Service(service, source_name, header_name, options).Run()


if __name__ == '__main__':
  main(sys.argv[1:])
