import sys
import json
import os

errorList = []
warnList = []
demList = []
demPath = ""

## Check if main python file can be accessed
try:
    sys.path.append('./py')
    from main import *
except ImportError:
    errorList.append("Main python file cant be accessed")

## Locate correct demtiles folder
lookupPaths = [
    "E:/EUDEM_1-1/demtiles",
    "D:/EUDEM_1-1/demtiles",
    "./demtiles"
]

for path in lookupPaths:
    if os.path.isdir(path):
        demPath = path
        break

## Check how many dem-tiles present in the dem-folder
if (demPath != ""):
    demList = os.listdir(demPath)
    for i in range(len(demList)):
        demList[i] = list(map(int, demList[i].strip(".tif").split("_")[1:3]))
    if (len(demList) < 100):
        warnList.append("demtiles-folder only contained " + str(len(demList)) + " tiles")
else:
    errorList.append("No demtiles-folder was located")

with open("./serverParameters/demfiles.json", "w+") as f:
    f.write(json.dumps({"path": demPath, "tiles": demList}))

print(json.dumps({
    "err": errorList, 
    "warn": warnList,
}))