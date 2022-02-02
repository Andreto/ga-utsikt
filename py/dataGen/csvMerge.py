import pandas

#Lists tiles that does not cover Sweden.
outOfBounds = [
    "43_35", "46_35", "47_35", "48_35", "49_35",
    "43_36", "48_36", "49_36",
    "43_37", "49_37",
    "43_38", "49_38", 
    "49_39",
    "49_40",
    "43_41", "49_41",
    "43_42", "48_42", "49_42",
    "43_43", "48_43", "49_43",
    "43_44", "48_44", "49_44",
    "43_45", "49_45",
    "43_46", "49_46",
    "43_47", "44_47",
    "43_48", "44_48",
    "43_49", "44_49",
    "43_50", "44_50", "45_50", "49_50",
    "43_51", "44_51", "45_51", "46_51", "48_51", "49_51"
]

#Merges tiles into one csv file
with open("./calcData/calcPoints/calcPoints.csv", "w+") as merge:

    n = 0

    merge.write("x,y,h,n\n")    #Adds headers allowing sorting of data

    #Iterates through tiles
    for tileY in range(35, 52): #Sweden: 35_52
        for tileX in range(43, 50): #Sweden: 43_50

            tileID = str(tileX) + "_" + str(tileY)

            #Skips unwanted tiles.
            if (tileID in outOfBounds):
                continue
            
            with open("./calcData/hills/hillPoints_" + str(tileX) + "_" + str(tileY) + ".csv", "r") as tile:
                merge.write(tile.read())

                n += 1

                print("Merged " + str(n) + " files")

#Sorts merged file by h-vale
print("Sorting by h...")
csvData = pandas.read_csv("./calcData/calcPoints/calcPoints.csv")
csvData.sort_values(["h"], axis=0, ascending=[False], inplace=True)
csvData.to_csv("./calcData/calcPoints/calcPoints_h.csv", mode="w+", index=False, header=False)

#Sorts merged file by n-value
print("Sorting by n...")
csvData = pandas.read_csv("./calcData/calcPoints/calcPoints.csv")
csvData.sort_values(["n"], axis=0, ascending=[False], inplace=True)
csvData.to_csv("./calcData/calcPoints/calcPoints_n.csv", mode="w+", index=False, header=False)