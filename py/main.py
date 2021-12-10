# Utsiktsberäkning # Andreas Törnkvist, Moltas Lindell # 2021

from posixpath import lexists
import sys
sys.path.append('./py/__pymodules__')

import math
import json
import pyproj as proj
import numpy as np
import plotly.express as px
from PIL import Image, ImageDraw
import rasterio


import worldfiles as wf

# Longitude = X ; Latitude = Y


earthRadius = 6371000 #meters
viewHeight = 2 #meters

wmTOeu = proj.Transformer.from_crs("epsg:4326", "epsg:3035", always_xy=True)
euTOwm = proj.Transformer.from_crs("epsg:3035", "epsg:4326", always_xy=True)

def tileIndexToCoord(tLon, tLat, x, y):
    return(tLon*100000 + x*25, (tLat+1)*100000 - y*25) # Longitude, Latitude

def coordToTileIndex(lon, lat):
    #lon, lat = lon-12.5, lat+12.5 # Adjust for tif-grid coordinates being referenced top-right instead of center # !!!!Important, To do
    tLon, tLat = math.floor(lon/100000), math.floor(lat/100000)
    x, y = round((lon-(tLon*100000))/25), round((100000-(lat-(tLat*100000)))/25)
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

def exportPointsToCSV(x, h, c):
    with open("temp/plotPoints.csv", "w+") as f:
        f.write("sep=,\n")
        for i in range(len(x)):
            f.write(str(x[i]) + "," +str(h[i]) + ","+ str(c[i]) + "\n")

def plotProfile(points):
    hPlot = [] ; xPlot = [] ; cPlot = []
    vMax = -1
    for i in range(len(points)):
        # i # the tile-pixel-index; x-position relative to the ellipsoid edge. i*25 is the length in meters.
        # h # the surface-height perpendicular to the ellipsoid.
        # x # absolute x-position
        if points[i] < -1000: h = 0
        else: h = points[i] 
        x = math.sin((i*25)/(earthRadius))*earthRadius # Account for the earths curvature droping of
        x -= math.sin((i*25)/(earthRadius))*h # Account for the hight data being perpendicular to the earths surface
        xPlot.append(x)

        curveShift = math.sqrt(earthRadius**2 - x**2)-earthRadius # Shift in absolute y-position due to earths curvature

        y = math.cos((i*25)/(earthRadius))*h + curveShift - points[0] - viewHeight
        hPlot.append(y)

        #Detect visibility
        v = math.atan(x and y / x or 0)
        if v >= vMax and x > 0:
            cPlot.append("a")
            vMax = v
        else:
            cPlot.append("b")

    #Create plot
    exportPointsToCSV(xPlot, hPlot, cPlot)
    fig = px.scatter(x=xPlot, y=hPlot, color=cPlot)
    #fig.show()


def getViewLine(startLon, startLat, v): #Returns a polyline object representing visible areas

    startLon, startLat = wmTOeu.transform(startLon, startLat)
    tLon, tLat, pX, pY = coordToTileIndex(startLon, startLat)

    demPath = json.load(open("./serverParameters/demfiles.json", "r"))["path"]

    tile = rasterio.open(demPath + "/dem_" + str(tLon) + "_" + str(tLat) +  ".tif").read()[0]

    #points = getLinePointsAndCoords(tile, tLon, tLat, pX, pY, pX, 0)
    points, coords = getLinePointsAndCoords(tile, tLon, tLat, pX, pY, v)

    if (v == (5/4)*math.pi): 
        plotProfile(points)

    latlngs = []

    lladd = []
    llon = False
    vMax = -4

    for i in range(len(points)):
        # i # the tile-pixel-index; x-position relative to the ellipsoid edge. i*25 is the length in meters.
        # h # the surface-height perpendicular to the ellipsoid.
        # x # absolute x-position
        if points[i] < -1000: h = 0
        else: h = points[i] 
        x = math.sin((i*25)/(earthRadius))*earthRadius # Account for the earths curvature droping of
        x -= math.sin((i*25)/(earthRadius))*h # Account for the hight data being perpendicular to the earths surface

        curveShift = math.sqrt(earthRadius**2 - x**2)-earthRadius # Shift in absolute y-position due to earths curvature

        y = math.cos((i*25)/(earthRadius))*h + curveShift - points[0] - viewHeight

        #Detect visibility
        v = math.atan(x and y / x or 0)
        
        if v >= vMax and x > 0:
            if llon:
                if (len(lladd) > 1):
                    lladd[1] = coords[i]
                else:
                    lladd.append(coords[i])
            else:
                lladd.append(coords[i])
                llon = True

            vMax = v
        elif llon:
            latlngs.append(lladd)
            llon = False
            lladd = []
    return(latlngs)

def getViewPolygons(startLon, startLat, res):
    lines = [] # Sightlines
    hzPoly = [] # Horizon polygon
    #res = 16 #Number of lines in one full rotation

    for i in range(res):
        line = getViewLine(float(startLon), float(startLat), (2*math.pi/res)*i)
        for l in line:
            lines.append(l)
        hzPoly.append(line[-1][-1])
        
    hzPoly.append(hzPoly[0]) # Close polygon

    return(lines, hzPoly)

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


###### MAIN EXC ######
