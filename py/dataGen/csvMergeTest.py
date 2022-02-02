import pandas



#Sorts merged file by h-vale
print("Sorting by h...")
csvData = pandas.read_csv("./calcData/calcPoints/45_42.csv")
csvData.sort_values(["h"], axis=0, ascending=[False], inplace=True)
csvData.to_csv("./calcData/calcPoints/45_42_h.csv", mode="w+", index=False, header=False)

