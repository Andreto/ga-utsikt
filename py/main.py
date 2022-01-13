# Utsiktsberäkning # Andreas Törnkvist, Moltas Lindell # 2021

import json
import math
import sys
from posixpath import lexists

import numpy as np
import plotly.express as px
import pyproj as proj
import rasterio
from numpy.lib.function_base import i0

import worldfiles as wf

sys.path.append('./py/__pymodules__')


# Longitude = X ; Latitude = Y


# Define ellipsoid properties
earthRadius = 6371000  # meters
equatorRadius = 6378137
poleRadius = 6356752
maxCurveRadius = (equatorRadius**2)/poleRadius # used for efficiently estemating the curveshift on far away tiles

# Define projection-conversions
wmTOeu = proj.Transformer.from_crs("epsg:4326", "epsg:3035", always_xy=True)
euTOwm = proj.Transformer.from_crs("epsg:3035", "epsg:4326", always_xy=True)

exportData = [] # :TEMP:


def tileIndexToCoord(tLon, tLat, x, y):
    return(tLon*100000 + x*25, (tLat+1)*100000 - (y+1)*25)  # Longitude, Latitude


def coordToTileIndex(lon, lat):
    # lon, lat = lon-12.5, lat+12.5 # Adjust for tif-grid coordinates being referenced top-right instead of center # :TODO:
    tLon, tLat = math.floor(lon/100000), math.floor(lat/100000)
    x, y = round((lon-(tLon*100000))/25), round(3999-((lat-(tLat*100000))/25))
    return(tLon, tLat, x, y)


def tileId(tLon, tLat): #Convert tile-index (array [x, y]) to tile-id (string "x_y")
    return(str(tLon) + "_" + str(tLat))


def tileIndex(tilename): #Convert tile-id (string "x_y") to tile-index (array [x, y])
    return(list(map(int, tilename.split("_"))))


def getTileArea(tLon, tLat):
    # Returns a leaflet polyline representing the edge of a tile
    latlngs = []
    latlngs.append([*euTOwm.transform(tLon*100000, tLat*100000)])
    latlngs.append([*euTOwm.transform((tLon+1)*100000, tLat*100000)])
    latlngs.append([*euTOwm.transform((tLon+1)*100000, (tLat+1)*100000)])
    latlngs.append([*euTOwm.transform(tLon*100000, (tLat+1)*100000)])
    latlngs.append([*euTOwm.transform(tLon*100000, tLat*100000)])
    for itt in range(len(latlngs)):
        latlngs[itt].reverse()
    return(latlngs)


def radiusCalculation(lat):  # Calculates the earths radius at a given latitude
    lat = lat*(math.pi/180)  # Convert to radians
    R = (
        (equatorRadius*poleRadius)
        /
        math.sqrt((poleRadius*math.cos(lat))**2 + ((equatorRadius*math.sin(lat))**2))
    )
    # R_old = math.sqrt( # :TEMP:
    #     (((equatorRadius**2)*(math.cos(lat))) **2 + ((poleRadius**2)*(math.sin(lat)))**2)
    #     /
    #     (((equatorRadius)*(math.cos(lat)))**2 + ((poleRadius)*(math.sin(lat)))**2)
    # )
    return(R)


def getLinePoints(tile, startX, startY, endX, endY):
    points = []
    if (startX-endX != 0):
        v = math.atan((startY-endY)/(startX-endX))
    else:
        v = math.pi
    l = math.sqrt((startY-endY)**2 + (startX-endX)**2)
    for i in range(math.floor(l)):
        x = startX + round(math.cos(v)*i)
        y = startY + round(math.sin(v)*i)
        points.append(tile[y][x])
    return(points)


def getLinePointsAndCoords(tile, tLon, tLat, startX, startY, v):
    points = []
    coords = []

    v = -v

    i = 0
    x = startX
    y = startY
    while(x >= 0 and x <= 3999 and y >= 0 and y <= 3999):
        points.append(tile[y][x])
        lat, lon = euTOwm.transform(*tileIndexToCoord(tLon, tLat, x, y))
        coords.append([lon, lat])
        i += 1
        x = startX + round(math.cos(v)*i)
        y = startY + round(math.sin(v)*i)

    return(points, coords)


def exportPointsToCSV(data):
    # [row][col]
    with open("temp/plotPoints.csv", "a+") as f:
        f.write("sep=;\n")
        for i in range(len(data)):
            for j in range(len(data[i])):
                f.write(str(data[i][j]).replace(".", ","))
                if j != len(data[i]) - 1:
                    f.write(";")
            f.write("\n")


def plotlyShow(data):
    xPl = []
    yPl = []
    cPl = []
    for i in range(len(data)):
        xPl.append(data[i][0])
        yPl.append(data[i][1])
        cPl.append(data[i][2])
    fig = px.scatter(x=xPl, y=yPl, color=cPl)
    fig.show()


def inBounds(x, y, top, left, bottom, right):
    return(x >= left and x <= right and y >= top and y <= bottom)


def pointSteps(di):
    # The change between calculationpoints should be at least 1 full pixel in x or y direction
    if abs(math.cos(di)) > abs(math.sin(di)):
        xChange = (math.cos(di)/abs(math.cos(di)))
        yChange = abs(math.tan(di)) * ((math.sin(di) / abs(math.sin(di))) if math.sin(di) else 0)
    else:
        yChange = (math.sin(di)/abs(math.sin(di)))
        xChange = abs(1/(math.tan(di) if math.tan(di) else 1)) * ((math.cos(di) / abs(math.cos(di))) if math.cos(di) else 0)
    lChange = math.sqrt(xChange**2 + yChange**2)
    return(xChange, yChange, lChange)


def nextTileBorder(tilename, x, y, di):
    xLen = (4000-x) if math.cos(di) > 0 else -1-x
    yLen = -1-y if math.sin(di) > 0 else (4000-y)

    xCost = abs(xLen / math.cos(di)) if math.cos(di) else 10000
    yCost = abs(yLen / math.sin(di)) if math.sin(di) else 10000

    if xCost < yCost:
        nX = x + xLen
        nY = y + abs(xLen * math.tan(di))*(1 if math.sin(di) > 0 else -1)
    else:
        nX = x + abs(yLen / math.tan(di))*(1 if math.cos(di) > 0 else -1)
        nY = y + yLen

    return(coordToTileIndex(*tileIndexToCoord(*tileIndex(tilename), nX, nY)))

def checkNextTile(tilename, x, y, di, vMax, hOffset, lSurf, demTiles, maxElev): # :TODO:
    tLonNext, tLatNext, xNext, yNext = nextTileBorder(tilename, x, y, di)
    tilenameNext = tileId(tLonNext, tLatNext)
    lSurf += math.sqrt((xNext-x)**2 + (yNext-y)**2)

    if tilenameNext in demTiles:
        curveShift = maxCurveRadius - math.cos((lSurf*25)/maxCurveRadius)*maxCurveRadius
        requiredElev = math.sin((lSurf*25)/maxCurveRadius)*math.tan(vMax) + curveShift + hOffset
        if maxElev[tilenameNext] < requiredElev:
            if maxElev["global"] < requiredElev:
                return(0, "")
            else:
                return(checkNextTile(tilenameNext, xNext, yNext, di, vMax, hOffset, lSurf, demTiles, maxElev))
        else:
            return(1, [tilenameNext, {"x": xNext, "y": xNext}])
    else:
        return(2, "")

# Returns a leaflet polyline object representing visible areas
def calcViewLine(tile, point, tilename, viewHeight, demTiles, maxElev):

    pX = point["p"]["x"]
    pY = point["p"]["y"]
    di = point["di"]
    vMax = point["start"]["v"]
    lSurf = point["start"]["lSurf"]

    tileMaxElev = maxElev[tilename]

    latlngs = []  # List of lines to visualize the view

    lladd = []  # Stores consecutive points to be added to the latlngs list
    llon = False  # Keeps track of whether the last point was added to the latlngs list

    h0 = tile[pY, pX] if tile[pY, pX] > 1000 else 0  # Elevation of the first point
    hBreak = False  # Keeps track of whether the calculation stopped due to max elevation being reached

    # Longitude, Latitude of the first point (in degrees)
    lon, lat = euTOwm.transform(*tileIndexToCoord(*tileIndex(tilename), pX, pY))

    startRadius = point["start"]["radius"] if point["start"]["radius"] else radiusCalculation(lat)  # Earths radius in the first point (in meters)

    xChange, yChange, lChange = pointSteps(di)

    while inBounds(pX, pY, 0, 0, 3999, 3999):
        # h # the surface-height perpendicular to the ellipsoid.
        # x # absolute x-position
        h = tile[round(pY), round(pX)]
        if h < -1000: 
            h = 0

        lon, lat = euTOwm.transform(*tileIndexToCoord(*tileIndex(tilename), pX, pY))
        pRadius = radiusCalculation(lat) # Earths radius in the current point (in meters)
        
        # :TODO: Rethink and check the maths
        x = math.sin((lSurf*25)/(pRadius))*pRadius # Account for the earths curvature droping of
        curveShift = math.sqrt(pRadius**2 - x**2) - startRadius # Shift in absolute y-position due to earths curvature
        x -= math.sin((lSurf*25)/(pRadius))*h # Account for the hight data being perpendicular to the earths surface
        y = math.cos((lSurf*25)/(pRadius))*h + curveShift - h0 - viewHeight

        # Detect visibility
        v = math.atan(x and y / x or 0)
        
        global exportData
        exportData.append([x, y, ("a" if v > vMax else "b")]) # :TEMP:

        if v > vMax and x > 0:
            # Point is visible, add it to the current line (lladd)
            if llon:
                if len(lladd) > 1:
                    lladd[1] = [lat, lon]
                else:
                    lladd.append([lat, lon])
            else:
                lladd.append([lat, lon])
                llon = True

            vMax = v
        elif llon:
            # Point is not visible, break and append the current line (lladd) to the latlngs list
            latlngs.append(lladd)
            llon = False
            lladd = []

        # Elevation required to see a point with the current angle
        requiredElev = (math.tan(vMax)*x) - curveShift + h0 + viewHeight
        if requiredElev > tileMaxElev: # :HERE:
            hBreak = True
            break

        lSurf += lChange
        #pY += math.sin(di) ; pX += math.cos(di) # :TEMP:
        pY -= yChange; pX += xChange

    
    #exportPointsToCSV(data=exportData) # :TEMP:

    if llon: # Add the current line (lladd) to the latlngs list before returning
        latlngs.append(lladd)
    
    tLon, tLat, stX, stY = coordToTileIndex(*tileIndexToCoord(*tileIndex(tilename), round(pX), round(pY)))
    if hBreak:
        cnCode, cnObj =  checkNextTile(tilename, pX, pY, di, vMax, (h0 + viewHeight), lSurf, demTiles, maxElev)
        if cnCode == 0:
            return(latlngs, 0, "")
        elif cnCode == 1:
            # print("Next tile:", cnObj[0], "at", cnObj[1], "with dir", di) # :TEMP:
            return(latlngs, 1, [cnObj[0],
            {
            "p": {"x": cnObj[1]["x"], "y": cnObj[1]["y"]},
            "di": di,
            "start": {"v": vMax, "lSurf": lSurf, "radius": startRadius}
            }
        ])
        elif cnCode == 2:
            return(latlngs, 2, ["warn", "Some of the view is not visible due to the lack of DEM data"])
            

    elif tileId(tLon, tLat) in demTiles:
        return(latlngs, 1, [tileId(tLon, tLat),
                            {
            "p": {"x": stX, "y": stY},
            "di": di,
            "start": {"v": vMax, "lSurf": lSurf, "radius": startRadius}
        }
        ])
    else:
        return(latlngs, 2, ["warn", "Some of the view is not visible due to the lack of DEM data"])


def calcViewPolys(startLon, startLat, res, viewHeight):
    lines = []  # Sightlines
    hzPoly = []  # Horizon polygon
    exInfo = []  # Extra info about the execution

    # Open the DEM information files
    demFileData = json.load(open("./serverParameters/demfiles.json", "r"))
    demPath = demFileData["path"]
    demTiles = demFileData["tiles"]
    maxElev = json.load(open("./calcData/maxElevations.json", "r"))

    # Calculate the startingpoints tile, and index within that tile
    tLon, tLat, startX, startY = coordToTileIndex(startLon, startLat)
    startTileId = tileId(tLon, tLat)
    queue = {startTileId: []}  # Prepere the queue

    # Add all directions for the starting point to the queue
    # for i in range(res):
    #     queue[startTileId].append(
    #         {
    #             "p": {"x": startX, "y": startY},
    #             "di": ((2*math.pi)/res) * i,
    #             "start": {"v": -4, "lSurf": 0, "radius": 0}
    #         }
    #     )
    #print("Queue:", queue) # :TEMP:
    #input("Press Enter to continue...") # :TEMP:

    queue[startTileId].append( # :TEMP:
        {
            "p": {"x": startX, "y": startY},
            "di": (((1/8)*math.pi)),
            "start": {"v": -4, "lSurf": 0, "radius": 0}
        }
    )

    


    while (len(queue) > 0):
        # Get the next tile to process
        tilename = list(queue)[0]
        element = queue[tilename]
        tile = rasterio.open(demPath + "/dem_" + tilename + ".tif").read()[0]

        # Process all (starting points and directions) in queue for the current tile
        while len(element) > 0:
            point = element.pop(0)
            line, status, ex = calcViewLine(tile, point, tilename, viewHeight, demTiles, maxElev)
            # Add visible lines to the lines list
            for l in line:
                lines.append(l)

            # Add next starting points to the queue or add execution info to the exInfo list
            if status == 1:
                if ex[0] in queue:
                    queue[ex[0]].append(ex[1])
                else:
                    queue[ex[0]] = [ex[1]]
            elif status == 2 and ex not in exInfo:
                exInfo.append(ex)

        del queue[tilename]

    plotlyShow(exportData)
    return(lines, hzPoly, exInfo)


def findHills():
    t = [46, 39]
    tile = rasterio.open("./demtiles/dem_" +
                         str(t[0]) + "_" + str(t[1]) + ".tif").read()[0]

    hSpots = []

    for i in range(1, 3999):
        if (i % 100 == 0):
            print(i)
        for j in range(1, 3999):
            check = [tile[i][j]]

            h = tile[i][j]
            if h > tile[i+1][j+1] and h > tile[i+1][j-1] and h > tile[i-1][j-1] and h > tile[i-1][j+1]:
                hSpots.append([j, i])

    print(len(hSpots))

    from contextlib import redirect_stdout
    from datetime import datetime
    with open('temp/py_log.txt', 'w+') as f:
        f.write("-- Log -- \n")
        with redirect_stdout(f):
            print()
            print(hSpots)


def main():
    # t = [xmin, ymin] #
    t = [46, 39]
    tile = rasterio.open("./demtiles/dem_" +
                         str(t[0]) + "_" + str(t[1]) + ".tif").read()[0]
    # y, x ; y: upp till ner ; x: höger till vänster

    points = getLinePointsAndCoords(
        tile, *coordToTileIndex(15.99838, 58.60397), math.pi/2)[0]

    # y, x = proj.transform(proj.Proj('epsg:3035'))

    #print(tileIndexToCoord(t[0], t[1], x0, y0), tileIndexToCoord(t[0], t[1], x1, y1))

    #print(wmTOeu.transform(Lon, Lat))

###### MAIN EXC ######

# print(radiusCalculation(58.2))
