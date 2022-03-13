# Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

def exportPoints(nPeaks, size):
    
    p = []

    with open("calcData/calcPoints/calcPoints_n.csv", "r") as peaks:
        
        n = 0
        
        for row in peaks:

            if (n >= nPeaks):
                break
            n += 1

            row = row.split(",")

            x = int(row[0])
            y = int(row[1])

            p.append([x, y, n, 0])

            for y2 in range(y - size * 25, y + size * 25 + 1, 25):
                for x2 in range(x - size * 25, x + size * 25 + 1, 25):
                    
                    if (y == y2 and x == x2):
                        continue

                    p.append([x2, y2, n, 1])

    with open("./temp/peaks.csv", "w+") as f:
        for i in p:
            f.write(str(i[0]) + "," + str(i[1]) + "," + str(i[2]) + "," + str(i[3]) + "\n")


exportPoints(5, 10)