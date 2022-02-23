import queue
import sys
import json
sys.path.append('./py')
from main import *

from datetime import datetime
from contextlib import redirect_stdout
with open('temp/py_log.txt', 'w+') as f:
    f.write("-- Log -- \n")
    f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    with redirect_stdout(f):
        print()
        print(float(sys.argv[3]))
        print("---------------------")

        


import time
start = time.time()
lon, lat, res, wh = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])

#queue = createResQueue(lon, lat, res)
queue = createDiQueue(4477700, 4254400, [5.654866776])

# 4477625 4254375 5.672320069
# 111586.0367
# 4477700 4254400 5.654866776

lines, hzPoly, exInfo = calcViewPolys(queue, wh)

print(json.dumps({
    "pl": lines,
    "hz": hzPoly,
    "info": exInfo
}))

end = time.time()
with open('temp/py_exectime.txt', 'a') as f:
    with redirect_stdout(f):
        print(end-start)


