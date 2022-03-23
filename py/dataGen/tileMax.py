# Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

import math
import json
import sys
import os
import numpy as np
import rasterio

demPath = "D:/EUDEM_1-1/demtiles/"
demList = os.listdir(demPath)
#demList = ["dem_42_38.tif", "dem_42_39.tif"]


maxData = {}
globalMax = 0

for demFile in demList:
    tile = rasterio.open(demPath + demFile).read()[0]
    maxElev = np.amax(tile)
    maxData[demFile.strip(".tif").strip("dem_")] = maxElev
    print(demFile.strip(".tif").strip("dem_"), maxElev)
    if maxElev > globalMax:
        globalMax = maxElev

maxData["global"] = globalMax

print(maxData)

with open("maxElevations.json", "w+") as f:
    f.write(str(maxData).replace("'", '"'))