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
    elevDems = os.listdir(demPath + "/elev")
    for i in range(len(elevDems)):
        elevDems[i] = elevDems[i].strip(".tif").strip("dem_")
    if (len(elevDems) < 100):
        warnList.append("demtiles-folder only contained " + str(len(elevDems)) + " elevation-tiles")
   
    objDems = os.listdir(demPath + "/objects")
    for i in range(len(objDems)):
        objDems[i] = objDems[i].strip(".tif")
    if (len(objDems) < 100):
        warnList.append("demtiles-folder only contained " + str(len(objDems)) + " objectheight-tiles")

else:
    errorList.append("No demtiles-folder was located")

with open("./serverParameters/demfiles.json", "w+") as f:
    f.write(json.dumps({"path": demPath, "tiles": {"elev": elevDems, "obj": objDems}}))

print(json.dumps({
    "err": errorList, 
    "warn": warnList,
}))