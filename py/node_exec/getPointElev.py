import sys
import json
import rasterio
sys.path.append('./py')
from main import coordToTileIndex, tileId

lon = int(sys.argv[1])
lat = int(sys.argv[2])

tLon, tLat, x, y = coordToTileIndex(lon, lat)
tilename = tileId(tLon, tLat)

demFileData = json.load(open("./serverParameters/demfiles.json", "r"))
demPath = demFileData["path"]

elevTile = rasterio.open(demPath + "/elev/dem_" + tilename + ".tif").read()[0]
objTile = rasterio.open(demPath + "/objects/" + tilename + ".tif").read()[0]



print(json.dumps({
    "x": str(x), 
    "y": str(y), 
    "elev": str(elevTile[y, x]),
    "obj": str(objTile[y, x])
}))