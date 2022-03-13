# Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

import sys
sys.path.append('./py')
from main import *

from csv import reader
import math
import json
                
#Returns coordinates for the sightlines path
def getPath(x, y, lMax, di, step):
    
    #Defines final coordniates
    endX = x + math.cos(di) * lMax
    endY = y + math.sin(di) * lMax

    path = []
    l = 0

    while (l < float(lMax)):
        ch = [*euTOwm.transform(x, y)]
        ch.reverse()
        path.append(ch)

        x2 = math.cos(di) * step
        y2 = math.sin(di) * step

        l += math.sqrt(x2**2 + y2**2)

        x += x2
        y += y2

    ch = [*euTOwm.transform(endX, endY)]
    ch.reverse()
    path.append(ch)

    return path

def rgb_to_hex(r, g, b):
    return ('{:X}{:X}{:X}').format(r, g, b)

def hex_to_rgb(hex):
    rgb = []
    for i in (0, 2, 4):
        decimal = int(hex[i:i+2], 16)
        rgb.append(decimal)

    return (rgb)

def assignColors(l):

    cMax = '606BA6'
    cMin = 'F4D0D6'

    #If only one sightline is exported, the assigned color is cMax
    if (len(l) < 2):
        return([cMax])

    cMax = hex_to_rgb(cMax)
    cMin = hex_to_rgb(cMin)

    color = []

    lMax = l[0]
    lMin = l[-1]

    lDif = lMax - lMin

    #Defines difference between cMax and cMin.
    cDif = []
    for i in range(len(cMax)):
        cDif.append(cMax[i] - cMin[i])

    #Iterates over number of colors to define.
    for i in range(len(l)):
        cDif2 = []
        color.append([])
        lDif2 = lMax - l[i]

        for j in cDif:
            cDif2.append((j * ((lDif2) / lDif)))

        for j in range(len(cMax)):
            color[i].append(round(cMax[j] - cDif2[j]))

    for i in range(len(color)):
        color[i] = rgb_to_hex(color[i][0], color[i][1], color[i][2])

    return color

def exportSightlinePath(n, step):
    
    export = {
        "sightline": 0,
        "color": 0
    }

    sightlines = []
    length = []

    with open("./calcData/sightlines/sightlines_l_SWE.csv", "r") as csv:    #Reads list of sightlines

        #Gets coordinate paths for n polylines
        for row in reader(csv):
            if n <= 0:
                break

            x = int(row[0])
            y = int(row[1])
            l = float(row[3])
            di = float(row[4])
            
            sightlines.append(getPath(x, y, l, di, step))
            n = n - 1
            length.append(l)

    export["sightline"] = sightlines
    
    export["color"] = assignColors(length)    #Every length gets replaced by a color.

    with open("serverFiles/sightlines/assets/sightlinePath.js", "w+") as f:
        f.write("sightlinePaths=")
        json.dump(export, f)

exportSightlinePath(1, 500)  #Number of sightlines displayed, length of each calculation step (m)