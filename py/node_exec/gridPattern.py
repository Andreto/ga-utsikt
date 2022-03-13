# Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

import sys
import json
sys.path.append('./py')
from main import *

p = []
l = []

demInfo = json.load(open("./serverParameters/demfiles.json", "r"))

for tile in demInfo["tiles"]["elev"]:
    tileCh = list(map(int, tile.split("_")))
    borders = getTileArea(*tileCh)
    p.append(borders)
    l.append({"txt": tile, "ch": [(borders[2][0] + borders[0][0])/2, (borders[2][1] + borders[0][1])/2]})

print(json.dumps({"p": p, "l": l}))