import sys
import json
sys.path.append('./py')
from main import *

out = []
polyline = []
color = []

with open("./temp/sightlinePath.csv", "r") as f: #read csv file
    for line in f:

        #Divides .csv into different arrays for different sightlines.
        if ("0,0" in line):
            out.append(polyline)
            polyline = []

        else:    
            line = line.split(',')
            chords = [*euTOwm.transform(float(line[0]), float(line[1]))]
            chords.reverse()
            polyline.append(chords)

with open("./temp/colors.csv", "r") as f: #read csv file
    for line in f:
        line = line.replace("\n", "")
        color.append(line)

print(json.dumps({
    "pl": out,
    "color": color
}))