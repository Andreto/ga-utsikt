import sys
import json
sys.path.append('./py')
from main import *

p = []
l = []

demInfo = json.load(open("./serverParameters/demfiles.json", "r"))

for tile in demInfo["tiles"]:
    tileCh = list(map(int, tile.split("_")))
    tileCh = [45,42]
    borders = getTileArea(*tileCh)
    p.append(borders)
    l.append({"txt": tile, "ch": [(borders[2][0] + borders[0][0])/2, (borders[2][1] + borders[0][1])/2]})
    break

print(json.dumps({"p": p, "l": l}))