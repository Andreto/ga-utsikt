import random

tile = [45, 41]
bounds = [(tile[0]*100000)/25, (tile[1]*100000)/25, (((tile[0]+1)*100000)/25)-1, (((tile[1]+1)*100000)/25)-1]
print(bounds)

fileLength = sum(1 for line in open("./calcData/hills/hillPoints_" + str(tile[0]) + "_" + str(tile[1]) + ".csv", "r"))
expN = 100
pickN = int(fileLength/expN)
print(pickN)

xPoints = []
yPoints = []

with open("./calcData/calcPoints/randomPoints.csv", "w+") as f, open("./calcData/hills/hillPoints_" + str(tile[0]) + "_" + str(tile[1]) + ".csv", "r") as tile:
    i = 0
    for line in tile:
        x, y, h, n = line.split(",")
        xPoints.append(int(x)/25)
        yPoints.append(int(y)/25)
        if i%pickN == 0:
            f.write(x + "," + y + ",H\n")
        i+=1

    extraN = 0
    while extraN < expN:
        x = random.randint(bounds[0], bounds[2])
        y = random.randint(bounds[1], bounds[3])
        if (x, y) in zip(xPoints, yPoints):
            continue
        else:
            extraN += 1
            f.write(str(x*25) + "," + str(y*25) + ",R\n")