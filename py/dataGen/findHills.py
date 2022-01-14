import csv
import string
import rasterio
from contextlib import redirect_stdout
import json

#Returns tallest adjacent point
def tallestAdjacentPoint(tile, x, y):
    hPoint = {"n": 0, "h": 0, "x": 0, "y": 0}
    
    #Iterates through adjacent points
    for y2 in range(-1, 2):
        if (y + y2 < 0 or y + y2 >= 4000):   #Skips if the tile edge is reached
            continue
        for x2 in range(-1, 2):
            if (x + x2 < 0 or x + x2 >= 4000):   #Skips if the tile edge is reached
                continue
                
            if (y2 == 0 and x2 == 0):   #Origin is skipped
                continue
            
            p = tile[x + x2][y + y2]

            if (p > hPoint["h"]):
                hPoint["h"] = p
                hPoint["x"] = x + x2
                hPoint["y"] = y + y2

    return hPoint

def xyId(x, y):
    return(str(x) + "_" + str(y))

def exportHills():
    tileX = 46
    tileY = 39

    tile = rasterio.open("../../demtiles" + "/dem_" + str(tileX) + "_" + str(tileY) + ".tif").read()[0]

    hillExport = {}

    #Iterates through points within the tile.
    for y in range(4000):
        if (y % 100 == 0): print(round(y/40,2), "%")
        for x in range(4000):
            
            p = tile[x][y]
            pNext = tallestAdjacentPoint(tile, x, y)

            while(pNext["h"] > p):
                x2 = pNext["x"]
                y2 = pNext["y"]

                p = pNext["h"]
                pNext = tallestAdjacentPoint(tile, x2, y2)
            
            if xyId(pNext["x"], pNext["y"]) in hillExport:
                hillExport[xyId(pNext["x"], pNext["y"])]["n"] += 1
            else:
                
                pNext["n"] = 1
                hillExport[xyId(pNext["x"], pNext["y"])] = (pNext)

    print("Exporting " + str(len(hillExport)) + " hills...", )
    with open("../../temp/hillExport.json", 'w+') as f:
        with redirect_stdout(f):
            print(json.dumps(str(hillExport)))

    with open("../../temp/hillExport.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(hillExport)

exportHills()

# tileX = 46
# tileY = 39

# tile = rasterio.open("../../demtiles" + "/dem_" + str(tileX) + "_" + str(tileY) + ".tif").read()[0]

# print(tallestAdjacentPoint(tile, 300, 300))