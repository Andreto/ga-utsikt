with open("./calcData/calcPoints/calcPoints.csv", "w+") as merge:

    #   ---Merges tiles into one csv file---
    for tileY in range(39, 41): #Sweden: 35_52
        for tileX in range(45, 48): #Sweden: 43_50

            tileID = str(tileX) + "_" + str(tileY)

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

            #Skips unwanted tiles.
            if (tileID in outOfBounds):
                continue
            
            with open("./calcData/hills/hillPoints_" + str(tileX) + "_" + str(tileY) + ".csv", "r") as tile:
                merge.write(tile.read())
    
    #Sorts merged file by height
    


    

