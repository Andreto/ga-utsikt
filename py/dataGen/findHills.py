import string
import rasterio
from contextlib import redirect_stdout
import json

tileSize = 1000

#Returns highest adjacent point
def highestAdjacentPoint(tile, x, y):
    hPoint = {"h": tile[x][y], "x": 0, "y": 0}
    
    #Iterates through adjacent points
    for y2 in range(-1, 2):
        if (y + y2 < 0 or y + y2 >= tileSize):   #Skips if the tile edge is reached
            continue
        for x2 in range(-1, 2):
            if (x + x2 < 0 or x + x2 >= tileSize):   #Skips if the tile edge is reached
                continue
                
            if (y2 == 0 and x2 == 0):   #Origin is skipped
                continue
            
            p = tile[x + x2][y + y2]    #Examined point

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
    for y in range(tileSize):
        if (y % 100 == 0): print(y, "/", tileSize)  #Prints progress
        for x in range(tileSize):
            
            p = {"n": 0, "h": tile[x][y], "x": x, "y": y}

            if (p["h"] < -1000): continue

            pNext = highestAdjacentPoint(tile, x, y)

            while(pNext["h"] > p["h"]):
                p["h"] = pNext["h"]
                p["x"] = pNext["x"]
                p["y"] = pNext["y"]

                pNext = highestAdjacentPoint(tile, p["x"], p["y"])

            if xyId(p["x"], p["y"]) in hillExport:
                hillExport[xyId(p["x"], p["y"])]["n"] += 1
            else:
                p["n"] = 1
                hillExport[xyId(p["x"], p["y"])] = p

    #Remove hills with "n" < 83..?         

    print("Exported " + str(len(hillExport)) + " hills.")

    with open("../../temp/hillExport.json", 'w+') as f:
        with redirect_stdout(f):
            print(json.dumps(str(hillExport)))

exportHills()