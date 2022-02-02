
import csv
import string
import rasterio
import time
from contextlib import redirect_stdout
import json
import sys
import pandas
sys.path.append('./py')
from main import *

demFileData = json.load(open("./serverParameters/demfiles.json", "r"))
demPath = demFileData["path"]

tileX = 45
tileY = 42

maxElevs = [{"elev": 0, "lon": 0, "lat": 0}]*400


tile = rasterio.open(demPath + "/dem_" + str(tileX) + "_" + str(tileY) + ".tif").read()[0]

with open("./temp/tempSave.csv", "w+") as f:
    f.write("lon,lat,h\n")
    for y in range(4000):
        for x in range(4000):
            lon, lat = tileIndexToCoord(tileX, tileY, x, y)
            f.write(str(lon) + "," + str(lat) + "," + str(tile[x][y]) + "\n")


print("Sorting by h...")
csvData = pandas.read_csv("./temp/tempSave.csv")
csvData.sort_values(["h"], axis=0, ascending=[False], inplace=True)
csvData.to_csv("./calcData/calcPoints/calcPoints_h.csv", mode="w+", index=False, header=False)

