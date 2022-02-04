import sys
sys.path.append('./py')
from main import *

from csv import reader
import math
import shapefile
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

def inSweden(x, y):
    shape = shapefile.Reader("calcData/swedenBorders/ne_10m_admin_0_countries_swe.shp") #250 polygons

    feature = shape.shapeRecords()[50]  #Sweden = 50
    sweden = feature.shape.__geo_interface__  
    sweden = sweden["coordinates"] #Revoves unnecessary info
    
    x, y = [*euTOwm.transform(x, y)]

    point = Point(x, y)
    polygon = Polygon(sweden[0][0])

    if polygon.contains(point):
        return(True)
        
    else:
        return(False)
                


#Returns coordinates for the sightlines path
def getPath(x, y, lMax, di, step):
    
    path = []
    l = 0

    while (l < float(lMax)):

        path.append([x, y])

        x2 = math.cos(di) * step
        y2 = math.sin(di) * step

        l += math.sqrt(x2**2 + y2**2)

        x += x2
        y += y2

    return path

def exportSightlines(n, step):

    sightlines = []

    with open("./calcData/sightlines/sightlines_l.csv", "r") as csv:    #Reads list of sightlines

        #Gets coordinate paths for n sightlines
        for row in reader(csv):
            if n <= 0:
                break

            x = int(row[0])
            y = int(row[1])
            l = float(row[3])
            di = float(row[4])
            
            if(inSweden(x, y)):
                sightlines.append(getPath(x, y, l, di, step))
                n = n - 1

    #Exports csv.
            with open("./temp/sightlinePath.csv", "w+") as f:
                for i in sightlines:
                    for j in i:
                        f.write(str(j[0]) + "," + str(j[1]) + "\n")

exportSightlines(1, 500)  #Number of sightlines displayed, length of each calculation step (m)
        