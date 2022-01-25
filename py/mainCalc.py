# Utsiktsberäkning # Andreas Törnkvist, Moltas Lindell # 2021

import json
import math
import sys
from posixpath import lexists
from tkinter import XView

import numpy as np
import plotly.express as px
import pyproj as proj
import rasterio
from numpy.lib.function_base import i0
from datetime import datetime
import time
from contextlib import redirect_stdout

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

def log(*msg):
    with open('temp/py_log.txt', 'a+') as f:
        time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        msgCon = " ".join(map(str, msg))
        with redirect_stdout(f):
            print(time + " -- " + msgCon)


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
    sPl = []
    for i in range(len(data)):
        xPl.append(data[i][0])
        yPl.append(data[i][1])
        cPl.append(data[i][2])
        sPl.append(data[i][3])
    fig = px.scatter(x=xPl, y=yPl, color=cPl, symbol=sPl)
    fig.show()


def inBounds(x, y, top, left, bottom, right):
    return(x >= left and x <= right and y >= top and y <= bottom)


def pointSteps(di):
    # The change between calculation-points should be at least 1 full pixel in x or y direction
    if abs(math.cos(di)) > abs(math.sin(di)):
        xChange = (math.cos(di)/abs(math.cos(di)))
        yChange = abs(math.tan(di)) * ((math.sin(di) / abs(math.sin(di))) if math.sin(di) else 0)
    else:
        yChange = (math.sin(di)/abs(math.sin(di)))
        xChange = abs(1/(math.tan(di) if math.tan(di) else 1)) * ((math.cos(di) / abs(math.cos(di))) if math.cos(di) else 0)
    lChange = math.sqrt(xChange**2 + yChange**2)
    return(xChange, yChange, lChange)


def sssAngle(R1, R2, l):
    cosv = ((R1**2 + R2**2 - l**2)/(2*R1*R2))
    return(math.acos(cosv) if cosv <= 1 else math.acos(cosv**-1))


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

def checkNextTile(tilename, x, y, di, vMax, hOffset, lSurf, demTiles, maxElev, startAngle, startRadius, depth): # :TODO:
    tLonNext, tLatNext, xNext, yNext = nextTileBorder(tilename, x, y, di)
    tilenameNext = tileId(tLonNext, tLatNext)
    lon, lat = tileIndexToCoord(*tileIndex(tilename), x, y)
    lonNext, latNext = tileIndexToCoord(tLonNext, tLatNext, xNext, yNext)
    d_lSurf = math.sqrt(((lon-lonNext)/25)**2 + ((lat-latNext)/25)**2)
    lSurf += d_lSurf

    if tilenameNext in demTiles:
        if False: # :TODO: # [4339550, 3914250]
            l = 0
            step = 4
            calcAngle = startAngle
            while l < d_lSurf:
                l += step
                x += round(math.cos(di)*step)
                y += round(math.sin(di)*step)
                lon, lat = euTOwm.transform(*tileIndexToCoord(*tileIndex(tilename), x, y))
                pRadius = radiusCalculation(lat) # Earths radius in the current point (in meters)

                calcAngle += sssAngle(calcAngle, pRadius, step*25)
                
            xA = math.sin(calcAngle)*pRadius
            curveShift = math.sqrt(pRadius**2 - xA**2) - startRadius
            requiredElev = xA*math.tan(vMax) + curveShift + hOffset
            angle = calcAngle

        else:

            curveShift = maxCurveRadius - math.cos((lSurf*25)/maxCurveRadius)*maxCurveRadius
            requiredElev = math.sin((lSurf*25)/maxCurveRadius)*math.tan(vMax) + curveShift + hOffset
            angle = (lSurf*25)/earthRadius

        if maxElev[tilenameNext] < requiredElev:
            if maxElev["global"] < requiredElev:
                return(0, "")
            else:
                return(checkNextTile(tilenameNext, xNext, yNext, di, vMax, hOffset, lSurf, demTiles, maxElev, startAngle, startRadius, depth+1))
        else:
            lon, lat = euTOwm.transform(*tileIndexToCoord(*tileIndex(tilenameNext), xNext, yNext))
            return(1, [tilenameNext, {"x": xNext, "y": yNext, "lSurf": lSurf, "radius": radiusCalculation(lat), "angle": angle}])
    else:
        return(2, "")

# Returns a leaflet polyline object representing visible areas
def calcViewLine(tile, point, tilename, viewHeight, demTiles, maxElev, N, longestLine):

    pX = point["p"]["x"]
    pY = point["p"]["y"]
    di = point["di"]
    vMax = point["start"]["v"]
    lSurf = point["start"]["lSurf"]

    log("---", tilename, "---") # :TEMP: # :HERE:

    tileMaxElev = maxElev[tilename]

    latlngs = []  # List of lines to visualize the view

    lladd = []  # Stores consecutive points to be added to the latlngs list
    llon = False  # Keeps track of whether the last point was added to the latlngs list

    if "h" in point["start"]:
        h0 = point["start"]["h"]
    else:
        h0 = tile[pY, pX] if tile[pY, pX] > -1000 else 0  # Elevation of the first point
    
    hBreak = False  # Keeps track of whether the calculation stopped due to max elevation being reached

    # Longitude, Latitude of the first point (in degrees)
    lon, lat = euTOwm.transform(*tileIndexToCoord(*tileIndex(tilename), pX, pY))

    startRadius = point["start"]["radius"] if point["start"]["radius"] else radiusCalculation(lat)  # Earths radius in the first point (in meters)

    xChange, yChange, lChange = pointSteps(di)

    lastPoint = point["last"] if point["last"] else {
        "radius": radiusCalculation(lat),
        "angle": 0
    }

    calcAngle = lastPoint["angle"]

    while inBounds(pX, pY, -.5, -.5, 3999.5, 3999.5):
        # h # the surface-height perpendicular to the ellipsoid.
        # x # absolute x-position
        h = tile[round(pY), round(pX)]
        if h < -1000: 
            h = 0

        lon, lat = euTOwm.transform(*tileIndexToCoord(*tileIndex(tilename), pX, pY))
        pRadius = radiusCalculation(lat) # Earths radius in the current point (in meters)
        
        # print(calcAngle) # :TEMP:
        x = math.sin(calcAngle)*pRadius # Account for the earths curvature droping of
        curveShift = math.sqrt(pRadius**2 - x**2) - startRadius # Shift in absolute y-position due to earths curvature
        x -= math.sin(calcAngle)*h # Account for the hight data being perpendicular to the earths surface
        y = math.cos(calcAngle)*h + curveShift - h0 - viewHeight

        calcAngle += sssAngle(lastPoint["radius"], pRadius, lChange*25)

        lastPoint = {
            "radius": pRadius,
            "angle": calcAngle
        }

        # Detect visibility
        v = math.atan(x and y / x or 0)

        global exportData
        exportData.append([x, lSurf, ("a" if v > vMax else "b"), di]) # :TEMP:

        if v > vMax and x > 0:
            vMax = v
            N += 1
            if lSurf > longestLine["l"]:
                longestLine["l"] = lSurf
                longestLine["di"] = di

        # Elevation required to see a point with the current angle
        requiredElev = (math.tan(vMax)*x) - curveShift + h0 + viewHeight
        if requiredElev > tileMaxElev:
            hBreak = True
            break

        lSurf += lChange
        #pY -= math.sin(di) ; pX += math.cos(di) # :TEMP:
        pY -= yChange; pX += xChange


    #exportPointsToCSV(data=exportData) # :TEMP:

    queueObj = {
        "p": {"x": 0, "y": 0},
        "di": di,
        "start": {"v": vMax, "lSurf": lSurf, "radius": startRadius, "h": h0},
        "last": lastPoint
    }
    
    tLon, tLat, stX, stY = coordToTileIndex(*tileIndexToCoord(*tileIndex(tilename), round(pX), round(pY)))
    if hBreak:
        lTime = time.time()
        cnCode, cnObj =  checkNextTile(tilename, pX, pY, di, vMax, (h0 + viewHeight), lSurf, demTiles, maxElev, lastPoint["angle"], startRadius, 0)
        #cnCode = 0 # :TEMP:
        # log("checkTiles time:", time.time()-lTime);
        if cnCode == 0:
            return(0, "", N, longestLine)
        elif cnCode == 1:
            # print("Next tile:", cnObj[0], "at", cnObj[1], "with dir", di) # :TEMP:
            queueObj["p"] = {"x": cnObj[1]["x"], "y": cnObj[1]["y"]}
            queueObj["start"]["lSurf"] = cnObj[1]["lSurf"]
            queueObj["last"] = {"radius": cnObj[1]["radius"], "angle": cnObj[1]["angle"]}
            log(math.sin(cnObj[1]["angle"])*earthRadius, queueObj)
            return(1, [cnObj[0], queueObj], N, longestLine)
        elif cnCode == 2:
            return(2, ["warn", "Some of the view is not visible due to the lack of DEM data"], N, longestLine)
            

    elif tileId(tLon, tLat) in demTiles:
        queueObj["p"] = {"x": stX, "y": stY}
        return(1, [tileId(tLon, tLat), queueObj], N, longestLine)
    else:
        return(2, ["warn", "Some of the view is not visible due to the lack of DEM data"], N, longestLine)


def calcViewPolys(startLon, startLat, res, viewHeight):
    N = 0
    longestLine = {"l": 0, "di": 0}

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

    for i in range(res):
        queue[startTileId].append(
            {
                "p": {"x": startX, "y": startY},
                "di": ((2*math.pi)/res) * i,
                "start": {"v": -4, "lSurf": 0, "radius": 0},
                "last": 0
            }
        )
    #print("Queue:", queue) # :TEMP:
    #input("Press Enter to continue...") # :TEMP:

    # queue[startTileId].append( # :TEMP:
    #     {
    #         "p": {"x": startX, "y": startY},
    #         "di": ((7/4)*math.pi),
    #         "start": {"v": -4, "lSurf": 0, "radius": 0},
    #         "last": 0
    #     }
    # )

    
    while (len(queue) > 0):
        # Get the next tile to process
        tilename = list(queue)[0]
        element = queue[tilename]
        tile = rasterio.open(demPath + "/dem_" + tilename + ".tif").read()[0]

        # Process all (starting points and directions) in queue for the current tile
        while len(element) > 0:
            point = element.pop(0)
            status, ex, N, longestLine = calcViewLine(tile, point, tilename, viewHeight, demTiles, maxElev, N, longestLine)

            # Add next starting points to the queue or add execution info to the exInfo list
            if status == 1:
                if ex[0] in queue:
                    queue[ex[0]].append(ex[1])
                else:
                    queue[ex[0]] = [ex[1]]
            elif status == 2 and ex not in exInfo:
                exInfo.append(ex)

        del queue[tilename]

    # plotlyShow(exportData) # :TEMP:
    longestLine["l"] = longestLine["l"]*25
    return(N, longestLine)


def start():
    # f = open('./calcData/calcPoints/calcPoints_h.csv', 'r')
    f = open('./calcData/hills/hillPoints_46_39.csv', 'r')
    Lines = f.readlines()
    lCount = 0
    linesLen = len(Lines)
    for line in Lines:
        print("Line", line)
        point = list(map(int, line.split(',')[0:2]))
        print("Calculating:", point[0], point[1], ("("+ str(lCount) + "/" + str(linesLen) + ")"))
        pointN, pointLongest = calcViewPolys(point[0], point[1], 90, 2)
        with open("./temp/generated.csv", "a+") as saveFile:
            print("Saving:", point[0], point[1], "; N:", pointN, "; N:", pointLongest["l"])
            saveFile.write(str(point[0]) + "," + str(point[1]) + "," + str(pointN) + "," + str(pointLongest["l"]) + "\n")
        lCount += 1

start()