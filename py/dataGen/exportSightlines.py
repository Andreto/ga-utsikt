import sys
sys.path.append('./py')
from main import *

from csv import reader
import math
                
#Returns coordinates for the sightlines path
def getPath(x, y, lMax, di, step):
    
    #Defines final coordniates
    endX = x + math.cos(di) * lMax
    endY = y + math.sin(di) * lMax

    path = []
    l = 0

    while (l < float(lMax)):

        path.append([x, y])

        x2 = math.cos(di) * step
        y2 = math.sin(di) * step

        l += math.sqrt(x2**2 + y2**2)

        x += x2
        y += y2

    path.append([endX, endY])

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

    color = []

    lMax = l[0]
    lMin = l[-1]

    lDif = lMax - lMin

    cMax = hex_to_rgb('F24B6A')
    cMin = hex_to_rgb('5D9DF1')

    #Defines difference between cMax abd cMin
    cDif = []
    for i in range(len(cMax)):
        cDif.append(cMax[i] - cMin[i])

    #Iterates over number of colors to define.
    for i in range(len(l)):
        cDif2 = []
        color.append([])
        lDif2 = lMax - l[i]

        for j in cDif:
            cDif2.append((j * (lDif2/lDif)))

        for j in range(len(cMax)):
            color[i].append(round(cMax[j] - cDif2[j]))

    for i in range(len(color)):
        color[i] = rgb_to_hex(color[i][0], color[i][1], color[i][2])

    return color

def exportSightlinePath(n, step):
    
    pl = []
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
            

            pl.append(getPath(x, y, l, di, step))
            pl.append([[0, 0]]) #Allows for recognitions of end of sightline
            n = n - 1
            length.append(l)

    #Exports csv of sightlines
    with open("./temp/sightlinePath.csv", "w+") as f:
        for i in pl:
            for j in i:
                f.write(str(j[0]) + "," + str(j[1]) + "\n")
    
    color = assignColors(length)    #Every length gets replaced by a color.

    #Exports csv of colors
    with open("./temp/colors.csv", "w+") as f:
        for i in color:
            f.write(str(i) + "\n")

exportSightlinePath(100, 10000)  #Number of sightlines displayed, length of each calculation step (m)