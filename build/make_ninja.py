#!/usr/bin/env python
# Copyright 2013 Ben Smith. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import cStringIO
import ninja_syntax
import optparse
import os
import sys

WINDOWS = sys.platform in ('cygwin', 'win32')
SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(SCRIPT_DIR)


def Prefix(prefix, items):
  if items is None:
    return ''
  if type(items) is str:
    items = items.split()
  return ' '.join(prefix + x for x in items)

def SourceToObj(source, arch):
  return os.path.join('out', '%s.%s.o' % (os.path.splitext(source)[0], arch))

def SplitPath(path):
  result = []
  while True:
    head, tail = os.path.split(path)
    if not head:
      return [tail] + result
    result[:0] = [tail]
    path = head

def NoRepath(seq):
  result = []
  for path in seq:
    result.append(path.replace('<', '').replace('>', ''))
  return result

def Repath(prefix, seq):
  result = []
  for path in seq:
    if '<' in path:
      strip_start = path.find('<')
      strip_end = path.find('>')
      path = path[:strip_start] + path[strip_end+1:]
    else:
      path = os.path.join(*SplitPath(path)[1:])

    if type(prefix) is list:
      args = prefix + [path]
      result.append(os.path.join(*args))
    else:
      result.append(os.path.join(prefix, path))
  return result

def Python(cmd):
  if WINDOWS:
    return 'python %s' % (cmd,)
  return cmd


def Path(p):
  return os.path.normpath(p)


def PathToLibname(p):
  basename = os.path.splitext(os.path.basename(p))[0]
  assert(basename.startswith('lib'))
  return basename[3:]


MAKE_NINJA = os.path.relpath(__file__, ROOT_DIR)
SOURCE_FILES = [
  'src/gapi.cc',
]

DATA_FILES = [
  'data/index.html',
  'data/main.css',
]
SRC_DATA_FILES = NoRepath(DATA_FILES)
DST_DATA_FILES = Repath('out', DATA_FILES)


BUILT_FILES = [
  'out/gapi_test.nmf',
  'out/gapi_test_x86_32.nexe',
  'out/gapi_test_x86_64.nexe',
  'out/gapi_test_arm.nexe',
]


PACKAGE_FILES = DATA_FILES + BUILT_FILES + [
  'data/background.js',
  'data/manifest.json',
]
SRC_PACKAGE_FILES = NoRepath(PACKAGE_FILES)
DST_PACKAGE_FILES = Repath(['out', 'package'], PACKAGE_FILES)


class Writer(ninja_syntax.Writer):
  def __init__(self, s):
    ninja_syntax.Writer.__init__(self, s)

  def build(self, outputs, rule, inputs=None, implicit=None, order_only=None,
            variables=None):
    outputs = map(Path, self._as_list(outputs))
    inputs = map(Path, self._as_list(inputs))
    implicit = map(Path, self._as_list(implicit))
    order_only = map(Path, self._as_list(order_only))
    ninja_syntax.Writer.build(self, outputs, rule, inputs, implicit, order_only,
                              variables)

def main():
  parser = optparse.OptionParser()
  options, args = parser.parse_args()

  out_filename = os.path.join(os.path.dirname(__file__), '../build.ninja')
  s = cStringIO.StringIO()
  w = Writer(s)

  w.rule('configure', command = Python(MAKE_NINJA), generator=1)
  w.build('build.ninja', 'configure', implicit=[MAKE_NINJA])

  platform_dict = {
    'linux2': 'linux',
    'cygwin': 'win',
    'win32': 'win',
    'darwin': 'mac'
  }

  w.variable('nacl_sdk_root', Path('nacl_sdk/pepper_canary'))
  w.variable('toolchain_dir', Path('$nacl_sdk_root/toolchain'))
  w.variable('toolchain_dir_x86', Path('$toolchain_dir/%s_x86_newlib' % (
      platform_dict[sys.platform])))
  w.variable('toolchain_dir_arm', Path('$toolchain_dir/%s_arm_newlib' % (
      platform_dict[sys.platform])))
  w.variable('cc-x86_32', Path('$toolchain_dir_x86/bin/i686-nacl-gcc'))
  w.variable('cxx-x86_32', Path('$toolchain_dir_x86/bin/i686-nacl-g++'))
  w.variable('ar-x86_32', Path('$toolchain_dir_x86/bin/i686-nacl-ar'))
  w.variable('cc-x86_64', Path('$toolchain_dir_x86/bin/x86_64-nacl-gcc'))
  w.variable('cxx-x86_64', Path('$toolchain_dir_x86/bin/x86_64-nacl-g++'))
  w.variable('ar-x86_64', Path('$toolchain_dir_x86/bin/x86_64-nacl-ar'))
  w.variable('cc-arm', Path('$toolchain_dir_arm/bin/arm-nacl-gcc'))
  w.variable('cxx-arm', Path('$toolchain_dir_arm/bin/arm-nacl-g++'))
  w.variable('ar-arm', Path('$toolchain_dir_arm/bin/arm-nacl-ar'))

  Code(w)
  Data(w)
  Package(w)
  w.default(' '.join(map(Path, ['out/gapi_test.nmf'] + DST_DATA_FILES)))

  # Don't write build.ninja until everything succeeds
  with open(out_filename, 'w') as f:
    f.write(s.getvalue())


def BuildProject(w, name, rule, sources,
                 includedirs=None, libs=None, order_only=None, defines=None):
  includedirs = includedirs or []
  libs = libs or []
  defines = defines or []
  libfiles = [l for l in libs if os.path.dirname(l)]
  libnames = [l for l in libs if not os.path.dirname(l)]
  libdirs = sorted(set([os.path.dirname(l) for l in libfiles]))
  libs = [PathToLibname(l) for l in libfiles] + libnames

  for arch in ('x86_32', 'x86_64', 'arm'):
    arch_incdirs = Prefix('-I', [x.format(**vars()) for x in includedirs])
    arch_libdirs = Prefix('-L', [x.format(**vars()) for x in libdirs])
    arch_libs = Prefix('-l', [x.format(**vars()) for x in libs])
    arch_libfiles = [x.format(**vars()) for x in libfiles]
    arch_defines = Prefix('-D', [x.format(**vars()) for x in defines])

    ccflags_name = 'ccflags{arch}_{name}'.format(**vars())
    cxxflags_name = 'cxxflags{arch}_{name}'.format(**vars())
    ldflags_name = 'ldflags{arch}_{name}'.format(**vars())
    w.variable(ccflags_name,
               '$base_ccflags {arch_incdirs} {arch_defines}'.format(**vars()))
    w.variable(cxxflags_name,
               '$base_cxxflags {arch_incdirs} {arch_defines}'.format(**vars()))
    w.variable(ldflags_name, '{arch_libdirs} {arch_libs}'.format(**vars()))

    objs = [SourceToObj(x, arch) for x in sources]
    for source, obj in zip(sources, objs):
      ext = os.path.splitext(source)[1]
      if ext in ('.cc', '.cpp'):
        cc = '$cxx-' + arch
        ccflags = '$' + cxxflags_name
      elif ext == '.c':
        cc = '$cc-' + arch
        ccflags = '$' + ccflags_name

      w.build(obj, 'cc', source,
              order_only=order_only,
              variables={'ccflags': ccflags, 'cc': cc})

    if rule == 'link':
      out_name = 'out/{name}_{arch}.nexe'.format(**vars())
      variables= {'ldflags': '$' + ldflags_name, 'cc': '$cxx-' + arch}
    elif rule == 'ar':
      out_name = 'out/{name}_{arch}.a'.format(**vars())
      variables= {'ar': '$ar-' + arch}

    w.build(out_name, rule, objs + arch_libfiles, variables=variables)


def Code(w):
  w.newline()
  w.rule('cc',
      command='$cc $ccflags -MMD -MF $out.d -c $in -o $out',
      depfile='$out.d',
      description='CC $out')
  w.rule('ar',
      command='$ar rc $out $in',
      description='AR $out')
  w.rule('link',
      command='$cc $in $ldflags -o $out',
      description='LINK $out')

#  w.variable('base_ccflags', '-g')
#  w.variable('base_cxxflags', '-g -std=c++0x')
  w.variable('base_ccflags', '-g -O3')
  w.variable('base_cxxflags', '-g -std=c++0x -O3')

  BuildProject(
    w, 'gapi_test', 'link',
    SOURCE_FILES,
    includedirs=[
      'src',
      'out',
      '$nacl_sdk_root/include'],
    libs=[
      'ppapi_cpp',
      'ppapi'])

  w.newline()
  w.rule('nmf',
      command='$nmf $in -o $out',
      description='NMF $out')
  w.variable('nmf', Python('$nacl_sdk_root/tools/create_nmf.py'))
  w.build('out/gapi_test.nmf', 'nmf', [
    'out/gapi_test_x86_32.nexe',
    'out/gapi_test_x86_64.nexe',
    'out/gapi_test_arm.nexe'])


def Data(w):
  w.newline()

  if WINDOWS:
    cmd = Python('script/cp.py $in $out')
  else:
    cmd = 'cp $in $out'
  w.rule('cp', command=cmd, description='CP $out')
  for outf, inf in zip(DST_DATA_FILES, SRC_DATA_FILES):
    w.build(outf, 'cp', inf)


def Package(w):
  w.newline()
  w.rule('zip', command='$zip -C out/package $out $in', description='ZIP $out')
  w.variable('zip', Python('script/zip.py'))
  for outf, inf in zip(DST_PACKAGE_FILES, SRC_PACKAGE_FILES):
    w.build(outf, 'cp', inf)
  w.build(os.path.join('out', 'gapi_test.zip'), 'zip', DST_PACKAGE_FILES)
  w.build('package', 'phony', 'out/gapi_test.zip')


if __name__ == '__main__':
  sys.exit(main())
