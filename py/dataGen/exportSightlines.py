from csv import reader
import math

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

            n = n - 1

            x = int(row[0])
            y = int(row[1])
            l = float(row[3])
            di = float(row[4])

            sightlines.append(getPath(x, y, l, di, step))

    #Exports csv.
            with open("./temp/sightlinePath.csv", "w+") as f:
                for i in sightlines:
                    for j in i:
                        f.write(str(j[0]) + "," + str(j[1]) + "\n")

exportSightlines(1, 500)  #Number of sightlines displayed, length of each calculation step (m)
        