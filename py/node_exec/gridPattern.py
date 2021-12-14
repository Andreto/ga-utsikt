import sys
import json
sys.path.append('./py')
from main import *

out = []

demInfo = json.load(open("./serverParameters/demfiles.json", "r"))

for tile in demInfo["tiles"]:
    tile = list(map(int, tile.split("_")))
    out.append(getTileArea(*tile))
print(out)