import sys
import json
sys.path.append('./py')
from main import *

from datetime import datetime
from contextlib import redirect_stdout
with open('py_log.txt', 'w') as f:
    f.write("-- Log -- \n")
    f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    with redirect_stdout(f):
        print()
        print(float(sys.argv[3]))



lines, hzPoly = getViewPolygons(float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]))

print(json.dumps({
    "pl": lines,
    "hz": hzPoly
}))


