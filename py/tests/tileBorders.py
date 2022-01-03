import math

def tileIndexToCoord(tLon, tLat, x, y):
    return(tLon*100000 + x*25, (tLat+1)*100000 - (y+1)*25)  # Longitude, Latitude


def tileIndex(tilename):
    return(list(map(int, tilename.split("_"))))


def coordToTileIndex(lon, lat):
    # lon, lat = lon-12.5, lat+12.5 # Adjust for tif-grid coordinates being referenced top-right instead of center # :TODO:
    tLon, tLat = math.floor(lon/100000), math.floor(lat/100000)
    x, y = round((lon-(tLon*100000))/25), round(3999-((lat-(tLat*100000))/25))
    return(tLon, tLat, x, y)


def tileId(tLon, tLat):
    return(str(tLon) + "_" + str(tLat))


def nextTileBorder(tilename, x, y, di):

    xLen = (4000-x) if math.cos(di) > 0 else -1-x
    yLen = -1-y if math.sin(di) > 0 else (4000-y)

    xCost = abs(xLen / math.cos(di)) if math.cos(di) else 10000
    yCost = abs(yLen / math.sin(di)) if math.sin(di) else 10000

    if xCost < yCost:
        nX = x + xLen
        nY = y + abs(xLen * math.tan(di))*(1 if math.sin(di) > 0 else -1)
    else:
        nX = x + abs(yLen / math.tan(di))*(1 if math.cos(di) > 0 else -1)
        nY = y + yLen

    return(coordToTileIndex(*tileIndexToCoord(*tileIndex(tilename), nX, nY)))


def pointSteps(di):
    # The change between calculationpoints should be at least 1 full pixel in x or y direction
    if abs(math.cos(di)) > abs(math.sin(di)):
        xChange = (math.cos(di)/abs(math.cos(di)))
        yChange = abs(math.tan(di)) * ((math.sin(di) / abs(math.sin(di))) if math.sin(di) else 0)
    else:
        yChange = (math.sin(di)/abs(math.sin(di)))
        xChange = abs(1/(math.tan(di) if math.tan(di) else 1)) * ((math.cos(di) / abs(math.cos(di))) if math.cos(di) else 0)
    return(xChange, yChange)


nextTileBorder("40_39", 3000, 3500, di=math.radians(-60))
