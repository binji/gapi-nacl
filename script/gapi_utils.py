import re

def MixedCaseToSnakeCase(s):
  "fooBar -> foo_bar"
  result = ''
  for c in s:
    if c.isupper():
      if result:
        result += '_'
      result += c.lower()
    else:
      result += c
  return result


def MixedCaseToCapWords(s):
  "fooBar -> FooBar"
  return s[0].upper() + s[1:]


def MakeCIdentifier(s):
  "make sure |s| is a valid c identifier (i.e. no keywords, no symbols)"
  CPP_KEYWORDS = set([
    "asm", "auto", "bool", "break", "case", "catch", "char", "class", "const",
    "const_cast", "continue", "default", "delete", "do", "double",
    "dynamic_cast", "else", "enum", "explicit", "extern", "false", "float",
    "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
    "namespace", "new", "operator", "private", "protected", "public",
    "register", "reinterpret_cast", "return", "short", "signed", "sizeof",
    "static", "static_cast", "struct", "switch", "template", "this", "throw",
    "true", "try", "typedef", "typeid", "typename", "union", "unsigned",
    "using", "virtual", "void", "volatile", "wchar_t", "while",
  ])
  if s in CPP_KEYWORDS:
    return '_' + s
  return re.sub(r'\W', '_', s)


def MakeIncludeGuard(filename):
  "name_version -> NAME_VERSION_H_"
  return re.sub(r'\W', '_', filename.upper() + '_')


def SnakeCase(s):
  return MakeCIdentifier(MixedCaseToSnakeCase(s))


def CapWords(s):
  return MakeCIdentifier(MixedCaseToCapWords(s))


def Upper(s):
  return MakeCIdentifier(s.upper())


def WrapType(outer, inner):
  """Put |inner| inside |outer|, a format string, e.g. "std::vector<%s>"."""
  if inner and inner[-1] == '>':
    inner += ' '
  return outer % inner


def WrapLine(s, length, wrap_indent=False):
  if len(s) <= length:
    return [s]
  lines = []
  line = ''
  indent = re.match(r'(\s*)', s).group(1)
  for word in re.split('(\s+)', s):
    if len(line + word) > length:
      new_line = ''
      if wrap_indent:
        # Previous indent + 4 spaces
        new_line = indent + ' ' * 4
      if len(word) > length:
        # Word is really long, may as well add it now.
        line += word
      elif word.isspace():
        # If word is all spaces at the end of the line, just ignore it.
        pass
      else:
        new_line += word

      lines.append(line.rstrip())
      line = new_line
    else:
      line += word
  if line:
    lines.append(line.rstrip())
  return lines
