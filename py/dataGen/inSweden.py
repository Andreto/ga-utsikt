# Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

import sys
sys.path.append('./py')
from main import *

from csv import reader
import shapefile
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

#Returns true if point is inside sweden's borders.
def inSWE(x, y):
    shape = shapefile.Reader("calcData/swedenBorders/ne_10m_admin_0_countries_swe.shp")

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

#Exports n sightlines
def exportSightlines():

    slSWE = []
    a = 0
    b = 0

    with open("./calcData/sightlines/sightlines_l.csv", "r") as csv:    #Reads list of sightlines

        for row in reader(csv):

            a += 1

            x = int(row[0])
            y = int(row[1])

            if(inSWE(x, y)):
                
                b += 1

                print(b , "sightlines found,", a, "sightlines investigated.")
                slSWE.append(row)
    
    with open("./calcData/sightlines/sightlines_l_SWE.csv", "w+") as csv:    #Export list of sightlines
        
        for i in slSWE:
            csv.write(str(i[0]) + "," + str(i[1]) + "," + str(i[2]) + "," + str(i[3]) + "," + str(i[4]) + "\n")

exportSightlines()