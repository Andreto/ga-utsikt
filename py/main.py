# Utsiktsberäkning # Andreas Törnkvist, Moltas Lindell # 2021

from posixpath import lexists
import sys

from numpy.lib.function_base import i0
sys.path.append('./py/__pymodules__')

import math
import json
import pyproj as proj
import numpy as np
import plotly.express as px
import rasterio


import worldfiles as wf

# Longitude = X ; Latitude = Y


earthRadius = 6371000 #meters
viewHeight = 2 #meters

equatorRadius = 6378137
poleRadius = 6356752

wmTOeu = proj.Transformer.from_crs("epsg:4326", "epsg:3035", always_xy=True)
euTOwm = proj.Transformer.from_crs("epsg:3035", "epsg:4326", always_xy=True)

def tileIndexToCoord(tLon, tLat, x, y):
    return(tLon*100000 + x*25, (tLat+1)*100000 - y*25) # Longitude, Latitude

def tileNameIndexToCoord(tilename, x, y):
    tLon, tLat = list(map(int, tilename.split("_")))
    return(tLon*100000 + x*25, (tLat+1)*100000 - y*25) # Longitude, Latitude

def coordToTileIndex(lon, lat):
    #lon, lat = lon-12.5, lat+12.5 # Adjust for tif-grid coordinates being referenced top-right instead of center # !!!!Important, To do
    tLon, tLat = math.floor(lon/100000), math.floor(lat/100000)
    x, y = round((lon-(tLon*100000))/25), round((100000-(lat-(tLat*100000)))/25)-1
    return(tLon, tLat, x, y)

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

def radiusCalculation(lat):
    lat = lat*(math.pi/180)
    R = math.sqrt(
        (((equatorRadius**2)*(math.cos(lat)))**2 + ((poleRadius**2)*(math.sin(lat)))**2)
        /
        (((equatorRadius)*(math.cos(lat)))**2 + ((poleRadius)*(math.sin(lat)))**2)
    )
    return(R)

def getLinePoints(tile, startX, startY, endX, endY):
    points = []
    if (startX-endX  != 0):
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
    with open("temp/plotPoints.csv", "w+") as f:
        f.write("sep=,\n")
        for i in range(len(data[0])):
            for d in range(len(data)):
                f.write(str(data[d][i]))
                if d != len(data) - 1:
                    f.write(",")
            f.write("\n")

def tileId(tLon, tLat):
    return(str(tLon) + "_" + str(tLat))

def inBounds(x, y, top, left, bottom, right):
    return(x >= left and x <= right and y >= top and y <= bottom)


def calcViewLine(pX, pY, di, tile, tilename, vMax, lSurf, viewHeight, demTiles): #Returns a polyline object representing visible areas
    maxElev = json.load(open("./calcData/maxElevations.json", "r"))[tilename]

#    print(pY, pX)

    latlngs = [] # List of lines to visualize the view

    lladd = [] # Stores consecutive points to be added to the latlngs list
    llon = False # Keeps track of whether the last point was added to the latlngs list

    h0 = tile[pY, pX] # Elevation of the first point
    hBreak = False # Keeps track of whether the calculation stopped due to max elevation being reached

    lon, lat =  euTOwm.transform(*tileNameIndexToCoord(tilename, pX, pY)) # Longitude, Latitude of the first point (in degrees)
    startRadius = radiusCalculation(lat) # Radius of the first point (in meters)

    #The change between calculationpoints should be at least 1 full pixel in x or y direction
    if math.cos(di) > math.sin(di):
        xChange = (math.cos(di)/abs(math.cos(di))) if math.cos(di) != 0 else 0
        yChange = abs(math.cos(di)*math.tan(di)) * ((math.sin(di)/abs(math.sin(di))) if math.sin(di) != 0 else 0)
    else:
        yChange = math.sin(di)/abs(math.sin(di)) if math.sin(di) != 0 else 0
        xChange = (abs(math.cos(di)/math.tan(di)) if math.tan(di) != 0 else 1) * ((math.cos(di)/abs(math.cos(di))) if math.cos(di) != 0 else 0)

    while inBounds(pX, pY, 0, 0, 3999, 3999):
        # i # the tile-pixel-index; x-position relative to the ellipsoid edge. i*25 is the length in meters.
        # h # the surface-height perpendicular to the ellipsoid.
        # x # absolute x-position
        h = tile[round(pY), round(pX)]
        
        if h < -1000 : h = 0 

        lon, lat =  euTOwm.transform(*tileNameIndexToCoord(tilename, pX, pY))
        pRadius = radiusCalculation(lat)

        x = math.sin((lSurf*25)/(pRadius))*pRadius # Account for the earths curvature droping of
        curveShift = math.sqrt(pRadius**2 - x**2)-startRadius # Shift in absolute y-position due to earths curvature
        x -= math.sin((lSurf*25)/(pRadius))*h # Account for the hight data being perpendicular to the earths surface

        y = math.cos((lSurf*25)/(pRadius))*h + curveShift - h0 - viewHeight

        #Detect visibility
        v = math.atan(x and y / x or 0)
        
        if v >= vMax and x > 0:
            chords = [*euTOwm.transform(*tileNameIndexToCoord(tilename, pX, pY))]
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
            latlngs.append(lladd)
            llon = False
            lladd = []

        requiredElev = (math.tan(vMax)*x) - curveShift + h0 + viewHeight
        if requiredElev > maxElev:
            hBreak = True
            break

        lSurf += 1
        pY += math.sin(di); pX += math.cos(di)
        #pY += yChange; pX += xChange

    tLon, tLat, stX, stY = coordToTileIndex(*tileNameIndexToCoord(tilename, round(pX), round(pY)))
    if hBreak:
        return(latlngs, 0, "")
    elif tileId(tLon, tLat) in demTiles:
  #      print("pxy", pX, pY)
  #      print(tileNameIndexToCoord(tilename, round(pX), round(pY)))
  #      print("stxy",tLon, tLat, stX, stY)
        return(latlngs, 1, [tileId(tLon, tLat),
            {
                "p": {"x": stX, "y": stY},
                "di": [di],
                "start": {"v": vMax, "lSurf": lSurf}
            }
        ])
    else:
        return(latlngs, 2, ["warn", "Some of the view is not visible due to the lack of DEM data"])

    

def calcViewPolys(startLon, startLat, res, viewHeight):
    lines = [] # Sightlines
    hzPoly = [] # Horizon polygon
    exInfo = [] # Extra info about the execution
    vMax = [-4] * res # Max angel for each direction

    demFileData = json.load(open("./serverParameters/demfiles.json", "r"))
    demPath = demFileData["path"]
    demTiles = demFileData["tiles"]
    

    tLon, tLat, startX, startY = coordToTileIndex(startLon, startLat)

    queue = {
        tileId(tLon, tLat): [
            {
                "p": {"x": startX, "y": startY}, 
                "di": list(np.arange(0, math.pi*2, (math.pi*2)/res)),
                "start": {"v": -4, "lSurf": 0}
            }
        ]
    }


    while (len(queue) > 0):
        tilename = list(queue)[0]
        element = queue[tilename]
        tile = rasterio.open(demPath + "/dem_" + tilename +  ".tif").read()[0]
 #       print("element", element)
        for point in element:
 #           print("point: ", point)
            pX = point["p"]["x"] ; pY = point["p"]["y"]
            v = point["start"]["v"] ; lSurf = point["start"]["lSurf"]
            for di in point["di"]:
                line, status, ex = calcViewLine(pX, pY, di, tile, tilename, v, lSurf, viewHeight, demTiles)
                for l in line:
                    lines.append(l)
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
    tile = rasterio.open("./demtiles/dem_" + str(t[0]) + "_" + str(t[1]) +  ".tif").read()[0]

    hSpots = []

    for i in range(1, 3999):
        if (i%100 == 0): print(i)
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
    tile = rasterio.open("./demtiles/dem_" + str(t[0]) + "_" + str(t[1]) +  ".tif").read()[0]
    # y, x ; y: upp till ner ; x: höger till vänster

    points = getLinePointsAndCoords(tile,*coordToTileIndex(15.99838, 58.60397),math.pi/2)[0]

    # y, x = proj.transform(proj.Proj('epsg:3035'))

    #print(tileIndexToCoord(t[0], t[1], x0, y0), tileIndexToCoord(t[0], t[1], x1, y1))
    plotProfile(points)

    #print(wmTOeu.transform(Lon, Lat))

###### MAIN EXC ######

