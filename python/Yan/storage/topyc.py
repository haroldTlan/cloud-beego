#!/usr/bin/env python
import glob
import sys
import os

os.chdir(sys.argv[1])
os.system('rm *.pyc -rf')
pyfiles = [f for f in glob.glob('*.py')]
imports = []
for pyname in pyfiles:
    m = os.path.splitext(pyname)[0]
    if m <> 'topyc':
        imports.append('import %s' % m)

with open('topyc_.py', 'w') as f:
    f.write('\n'.join(imports))

import topyc_
try:
    os.remove('topyc_.py')
except:
    pass
try:
    os.remove('topyc_.pyc')
except:
    pass
