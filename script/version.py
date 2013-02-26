#!/usr/bin/env python
import optparse
import sys

YAJL_MAJOR=2
YAJL_MINOR=1
YAJL_MICRO=0

def main(args):
  parser = optparse.OptionParser(usage='%prog in -o out')
  parser.add_option('-o', dest='outfname', help='output file')
  options, args = parser.parse_args(args)
  if not args:
    parser.error('No input file')
  infname = args[0]
  outfname = options.outfname
  with open(infname) as inf:
    text = inf.read()
    text = text.replace('${YAJL_MAJOR}', str(YAJL_MAJOR))
    text = text.replace('${YAJL_MINOR}', str(YAJL_MINOR))
    text = text.replace('${YAJL_MICRO}', str(YAJL_MICRO))

  if outfname:
    with open(outfname, 'w') as outf:
      outf.write(text)
  else:
    print text

  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
