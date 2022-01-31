from csv import reader
import math

equatorRadius = 6378137
poleRadius = 6356752

def radiusCalculation(lat):  # Calculates the earths radius at a given latitude
    lat = lat*(math.pi/180)  # Convert to radians
    R = (
        (equatorRadius*poleRadius)
        /
        math.sqrt((poleRadius*math.cos(lat))**2 + ((equatorRadius*math.sin(lat))**2))
    )
    return(R)

def displaySightlines(n):
    line = {"x": 0, "y": 0, "l": 0, "di": 0}

    #Appends n sightlines to the sightline list
    with open("./calcData/sightlines/sightlines_l.csv", "r") as csv:

        for row in reader(csv):
            if n <= 0:
                break

            n = n - 1

            line["x"] = row[0]
            line["y"] = row[1]
            line["l"] = row[3]
            line["di"] = row[4]

            print(line["l"])

displaySightlines(10)
        