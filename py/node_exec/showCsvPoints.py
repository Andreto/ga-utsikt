# Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

import sys
import json
sys.path.append('./py')
from main import *

out = []

with open("./temp/hillPoints.csv", "r") as f: #read csv file
    for line in f: 
        line = line.split(",")
        chords = [*euTOwm.transform(float(line[0]), float(line[1]))]
        chords.reverse()
        
      
        out.append(chords)

print(out)
