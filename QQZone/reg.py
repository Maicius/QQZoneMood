import sys
import re
import json
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

# s = "abc(hello)casdf"
s = open('data0.json').read()
# s = "\"" + s + "\""
print s
dictData = json.dumps(s)
print dictData
decode = json.loads(dictData)

print decode[1]
