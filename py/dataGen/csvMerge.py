import pandas

#Merges tiles into one csv file
with open("./calcData/sightlines/sightlines.csv", "w+") as merge:

    n = 0

    merge.write("x,y,n,l,di\n")    #Adds headers allowing sorting of data

    for i in range(1, 3):

        with open("./calcData/sightlines/generated" + str(i) + ".csv", "r") as tile:
            merge.write(tile.read())

            n += 1

            print("Merged " + str(n) + " files")

#Sorts merged file by l-vale
print("Sorting by l...")
csvData = pandas.read_csv("./calcData/sightlines/sightlines.csv")
csvData.sort_values(["l"], axis=0, ascending=[False], inplace=True)
csvData.to_csv("./calcData/sightlines/sightlines_l.csv", mode="w+", index=False, header=False)

# #Sorts merged file by n-value
print("Sorting by n...")
csvData = pandas.read_csv("./calcData/sightlines/sightlines.csv")
csvData.sort_values(["n"], axis=0, ascending=[False], inplace=True)
csvData.to_csv("./calcData/sightlines/sightlines_n.csv", mode="w+", index=False, header=False)
