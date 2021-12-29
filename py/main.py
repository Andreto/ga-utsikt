# Utsiktsberäkning # Andreas Törnkvist, Moltas Lindell # 2021

import worldfiles as wf
import rasterio
import plotly.express as px
import numpy as np
import pyproj as proj
import json
import math
from posixpath import lexists
import sys

from numpy.lib.function_base import i0
sys.path.append('./py/__pymodules__')


# Longitude = X ; Latitude = Y


# Define ellipsoid properties
earthRadius = 6371000  # meters
equatorRadius = 6378137
poleRadius = 6356752

# Define projection-conversions
wmTOeu = proj.Transformer.from_crs("epsg:4326", "epsg:3035", always_xy=True)
euTOwm = proj.Transformer.from_crs("epsg:3035", "epsg:4326", always_xy=True)


def tileIndexToCoord(tLon, tLat, x, y):
    return(tLon*100000 + x*25, (tLat+1)*100000 - y*25)  # Longitude, Latitude


def tileNameIndexToCoord(tilename, x, y):
    tLon, tLat = list(map(int, tilename.split("_")))
    return(tLon*100000 + x*25, (tLat+1)*100000 - y*25)  # Longitude, Latitude


def coordToTileIndex(lon, lat):
    # lon, lat = lon-12.5, lat+12.5 # Adjust for tif-grid coordinates being referenced top-right instead of center # !!!!Important, To do
    tLon, tLat = math.floor(lon/100000), math.floor(lat/100000)
    x, y = round((lon-(tLon*100000))/25), round(3999-((lat-(tLat*100000))/25))
    return(tLon, tLat, x, y)

# Returns a leaflet polyline representing the edge of a tile


def getTileArea(tLon, tLat):
    latlngs = []
    latlngs.append([*euTOwm.transform(tLon*100000, tLat*100000)])
    latlngs.append([*euTOwm.transform((tLon+1)*100000, tLat*100000)])
    latlngs.append([*euTOwm.transform((tLon+1)*100000, (tLat+1)*100000)])
    latlngs.append([*euTOwm.transform(tLon*100000, (tLat+1)*100000)])
    latlngs.append([*euTOwm.transform(tLon*100000, tLat*100000)])
    for itt in range(len(latlngs)):
        latlngs[itt].reverse()
    return(latlngs)

# Calculates the earths radius at a given latitude


def radiusCalculation(lat):
    lat = lat*(math.pi/180)  # Convert to radians
    R = (
        (equatorRadius*poleRadius)
        /
        (math.sqrt((poleRadius*math.cos(lat))**2 + (equatorRadius*math.sin(lat)**2)))
    )
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


def tileId(tLon, tLat):
    return(str(tLon) + "_" + str(tLat))


def inBounds(x, y, top, left, bottom, right):
    return(x >= left and x <= right and y >= top and y <= bottom)

# Returns a leaflet polyline object representing visible areas


def calcViewLine(tile, point, tilename, viewHeight, demTiles):
    maxElev = json.load(open("./calcData/maxElevations.json", "r"))[tilename]

    pX = point["p"]["x"]
    pY = point["p"]["y"]
    di = point["di"]
    vMax = point["start"]["v"]
    lSurf = point["start"]["lSurf"]

    latlngs = []  # List of lines to visualize the view

    lladd = []  # Stores consecutive points to be added to the latlngs list
    llon = False  # Keeps track of whether the last point was added to the latlngs list

    h0 = tile[pY, pX] if tile[pY, pX] > - \
        1000 else 0  # Elevation of the first point
    hBreak = False  # Keeps track of whether the calculation stopped due to max elevation being reached

    # Longitude, Latitude of the first point (in degrees)
    lon, lat = euTOwm.transform(*tileNameIndexToCoord(tilename, pX, pY))

    startRadius = point["start"]["radius"] if point["start"]["radius"] else radiusCalculation(
        lat)  # Earths radius in the first point (in meters)

    # The change between calculationpoints should be at least 1 full pixel in x or y direction
    if abs(math.cos(di)) > abs(math.sin(di)):
        xChange = (math.cos(di)/abs(math.cos(di)))
        yChange = math.tan(di) * (math.sin(di) /
                                  abs(math.sin(di)) if math.sin(di) else 0)
    else:
        yChange = (math.sin(di)/abs(math.sin(di)))
        xChange = (1/math.tan(di)) * (math.cos(di) /
                                      abs(math.cos(di)) if math.cos(di) else 0)

    while inBounds(pX, pY, 0, 0, 3999, 3999):
        # h # the surface-height perpendicular to the ellipsoid.
        # x # absolute x-position
        h = tile[round(pY), round(pX)]
        if h < -1000:
            h = 0

        lon, lat = euTOwm.transform(*tileNameIndexToCoord(tilename, pX, pY))
        # Earths radius in the current point (in meters)
        pRadius = radiusCalculation(lat)

        # Account for the earths curvature droping of
        x = math.sin((lSurf*25)/(pRadius))*pRadius
        # Shift in absolute y-position due to earths curvature
        curveShift = math.sqrt(pRadius**2 - x**2)-startRadius
        # Account for the hight data being perpendicular to the earths surface
        x -= math.sin((lSurf*25)/(pRadius))*h

        y = math.cos((lSurf*25)/(pRadius))*h + curveShift - h0 - viewHeight

        # Detect visibility
        v = math.atan(x and y / x or 0)

        if v > vMax and x > 0:
            # Point is visible, add it to the current line (lladd)
            chords = [
                *euTOwm.transform(*tileNameIndexToCoord(tilename, pX, pY))]
            chords.reverse()
            if llon:
                if (len(lladd) > 1):
                    lladd[1] = chords
                else:
                    lladd.append(chords)
            else:
                lladd.append(chords)
                llon = True

            vMax = v
        elif llon:
            # Point is not visible, break and append the current line (lladd) to the latlngs list
            latlngs.append(lladd)
            llon = False
            lladd = []

        # Elevation required to see a point with the current angle
        requiredElev = (math.tan(vMax)*x) - curveShift + h0 + viewHeight
        if requiredElev > maxElev:
            hBreak = True
            break

        lSurf += 1
        pY += math.sin(di)
        pX += math.cos(di)
        #pY += yChange; pX += xChange

    tLon, tLat, stX, stY = coordToTileIndex(
        *tileNameIndexToCoord(tilename, round(pX), round(pY)))
    if hBreak:
        return(latlngs, 0, "")
    elif tileId(tLon, tLat) in demTiles:
      #      print("pxy", pX, pY)
      #      print(tileNameIndexToCoord(tilename, round(pX), round(pY)))
      #      print("stxy",tLon, tLat, stX, stY)
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

    # Open the DEM information file
    demFileData = json.load(open("./serverParameters/demfiles.json", "r"))
    demPath = demFileData["path"]
    demTiles = demFileData["tiles"]

    # Calculate the startingpoints tile, and index within that tile
    tLon, tLat, startX, startY = coordToTileIndex(startLon, startLat)
    startTileId = tileId(tLon, tLat)
    queue = {startTileId: []}  # Prepere the queue

    # Add all directions for the starting point to the queue
    for i in range(res):
        queue[startTileId].append(
            {
                "p": {"x": startX, "y": startY},
                "di": ((2*math.pi)/res) * i,
                "start": {"v": -4, "lSurf": 0, "radius": 0}
            }
        )

    while (len(queue) > 0):
        # Get the next tile to process
        tilename = list(queue)[0]
        element = queue[tilename]
        tile = rasterio.open(demPath + "/dem_" + tilename + ".tif").read()[0]

        # Process all (starting points and directions) in queue for the current tile
        for point in element:
            line, status, ex = calcViewLine(
                tile, point, tilename, viewHeight, demTiles)

            # Add visible lines to the lines list
            for l in line:
                lines.append(l)

            # Add next starting points to the queue or add execution info to the exInfo list
            if status == 1:
                if ex[0] in queue:
                    queue[ex[0]].append(ex[1])
                else:
                    queue[ex[0]] = [ex[1]]
            elif status == 2:
                exInfo.append(ex)

        del queue[tilename]

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

    from datetime import datetime
    from contextlib import redirect_stdout
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
