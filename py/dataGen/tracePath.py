import csv
import string
import rasterio
import time
from contextlib import redirect_stdout
import json
import sys
sys.path.append('./py')
from main import *

#Returns highest adjacent point
def highestAdjacentPoint(tile, x, y):
    hPoint = {"h": tile[x][y], "x": 0, "y": 0}
    
    #Iterates through adjacent points
    for y2 in range(-1, 2):
        if (y + y2 < 0 or y + y2 >= 4000):   #Skips if the tile edge is reached
            continue
        for x2 in range(-1, 2):
            if (x + x2 < 0 or x + x2 >= 4000):   #Skips if the tile edge is reached
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

def exportPath(lon, lat):

    lon, lat = wmTOeu.transform(lon, lat)

    tileX, tileY, y, x = coordToTileIndex(lon, lat)

    tile = rasterio.open("./demtiles" + "/dem_" + str(tileX) + "_" + str(tileY) + ".tif").read()[0]

    path = []
            
    p = {"n": 0, "h": tile[x][y], "x": x, "y": y}

    pNext = highestAdjacentPoint(tile, x, y)

    #Iterates until a hill is found.
    while(pNext["h"] > p["h"]):
        p["h"] = pNext["h"]
        p["x"] = pNext["x"]
        p["y"] = pNext["y"]
        
        path.append([p["y"], p["x"]])

        pNext = highestAdjacentPoint(tile, p["x"], p["y"])
    
    #Exports path.
    with open("./temp/hillpoints.csv", "w+") as f:
        for key in range(0, len(path), 3):
            item = path[key]

            lon, lat = tileIndexToCoord(tileX, tileY, item[0], item[1])
            f.write(str(lon) + "," + str(lat) + "\n")

    print("Exported a path with a length of " + str(len(path)) + " points")  #Prints export info

exportPath(17.367008, 67.643823)
