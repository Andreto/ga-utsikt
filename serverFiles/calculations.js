// Utsiktsberäkning 
// Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

const fs = require('fs');
const path = require('path');
const gdal = require('gdal');
const proj4 = require('proj4');

proj4.defs([
    ['WM', '+proj=longlat +datum=WGS84 +no_defs'],
    ['EU', '+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs']
]);

const earthRadius = 6371000
const equatorRadius = 6378137
const poleRadius = 6356752
const maxCurveRadius = (equatorRadius**2)/poleRadius

const demFileData = JSON.parse(fs.readFileSync(path.join(__dirname, '../serverParameters/demfiles.json'), 'utf8'));
const maxElevations = JSON.parse(fs.readFileSync(path.join(__dirname, '../serverParameters/maxElevations.json'), 'utf8'));

function openTile(demMeta, tilename){
    tile = {}
    console.log(path.join(demMeta.path,('elev/dem_' + tilename + '.tif')))
    tile.elev = gdal.open(path.join(demMeta.path,('elev/dem_' + tilename + '.tif'))).bands.get(1).pixels
    if (demMeta.tiles.obj.includes(tilename)) {
        tile.obj = gdal.open(path.join(demMeta.path,('objects/' + tilename + '.tif'))).bands.get(1).pixels
        tile.hasObj = true
    } else {
        tile.hasObj = false
    }
    return(tile);
}

function tileIndexToCoord(tLon, tLat, x, y) {
    return([tLon*100000 + x*25, (tLat+1)*100000 - (y+1)*25]);
}

function coordToTileIndex(lon, lat) {
    let tLon = Math.floor(lon/100000);
    let tLat = Math.floor(lat/100000);
    let x = Math.round((lon-(tLon*100000))/25);
    let y = Math.round(3999-((lat-(tLat*100000))/25));
    return([tLon, tLat, x, y]);
}

function tileId(tLon, tLat) { // Convert tile-index (array [x, y]) to tile-id (string "x_y")
    return(tLon.toString() + "_" + tLat.toString());
}
    
function tileIndex(tilename){ // Convert tile-id (string "x_y") to tile-index (array [x, y])
    let x = parseInt(tilename.split("_")[0]);
    let y = parseInt(tilename.split("_")[1]);
    return([x, y]);
} 

function getTileArea(tLon, tLat) { // Get tile-area (array [x, y])
    let latlngs = [
        proj4('EU', "WM", [tLon*100000, tLat*100000]),
        proj4('EU', "WM", [(tLon+1)*100000, tLat*100000]),
        proj4('EU', "WM", [(tLon+1)*100000, (tLat+1)*100000]),
        proj4('EU', "WM", [tLon*100000, (tLat+1)*100000]),
    ];
    latlngs.push(latlngs[0]);
    return(latlngs);
}

function radiusCalculation(lat) { // Calculates the earths radius at a given latitude
    lat = lat*(Math.PI/180) // Convert to radians
    let r = (
        (equatorRadius*poleRadius)
        /
        Math.sqrt((poleRadius*Math.cos(lat))**2 + ((equatorRadius*Math.sin(lat))**2))
    );
    return(r);
}

function inBounds(x, y, top, left, bottom, right) {
    return(x >= left && x <= right && y >= top && y <= bottom);
}

function pointSteps(di){ // The change between calculation-points should be at least 1 full pixel in x or y direction
    let xChange; let yChange;
    if (Math.abs(Math.cos(di)) > Math.abs(Math.sin(di))){
        xChange = (math.cos(di)/abs(math.cos(di)));
        yChange = abs(math.tan(di)) * (math.sin(di) ? (math.sin(di) / abs(math.sin(di))) : 0);
    } else {
        yChange = (math.sin(di)/abs(math.sin(di)));
        xChange = ((math.tan(di)) ? abs(1/(math.tan(di))) : 1) * (math.cos(di) ? (math.cos(di) / abs(math.cos(di))) : 0);
    }    
    let lChange = math.sqrt(xChange**2 + yChange**2);
    return({'x': xChange, 'y': yChange, 'l': lChange});
}

function sssAngle(r1, r2, l){
    let cosv = ((r1**2 + r2**2 - l**2)/(2*r1*r2));
    return((cosv <= 1) ? math.acos(cosv) : math.acos(cosv**-1));
}

function createResQueue(lon, lat, res) {
    let [tLon, tLat, startX, startY] = coordToTileIndex(lon, lat);
    let startTileId = tileId(tLon, tLat);
    let queue = {};
    queue[startTileId] = [];

    for (i = 0; i < res; i++) {
        queue[startTileId].push({
            'p': {'x': startX, 'y': startY},
            'di': ((2*Math.PI)/res) * i,
            'start': {'v': -4, 'lSurf': 0, 'radius': 0},
            'last': 0 
        });
    }
    return(queue);
}

function createDiQueue(lon, lat, dis) {
    let [tLon, tLat, startX, startY] = coordToTileIndex(lon, lat);
    let startTileId = tileId(tLon, tLat);
    let queue = {};
    queue[startTileId] = [];

    for (i = 0; i < dis.length; i++) {
        queue[startTileId].push({
            'p': {'x': startX, 'y': startY},
            'di': dis[i],
            'start': {'v': -4, 'lSurf': 0, 'radius': 0},
            'last': 0 
        });
    }
    return(queue);
}

function nextTileBorder(tilename, x, y, di) {
    let xLen = ((math.cos(di) > 0) ? 4000-x : -1-x);
    let yLen = ((math.sin(di) > 0) ? -1-y : 4000-y);
    let xCost = (math.cos(di) ? abs(xLen / math.cos(di)) : 10000);
    let yCost = (math.sin(di) ? abs(yLen / math.sin(di)) : 10000);
    let nX; let nY;

    if (xCost < yCost){
        nX = x + xLen;
        nY = y + abs(xLen * math.tan(di))*((math.sin(di) > 0) ? 1 : -1);
    } else {
        nX = x + abs(yLen / math.tan(di))*((math.cos(di) > 0) ? 1 : -1);
        nY = y + yLen;
    }
    return(coordToTileIndex(...tileIndexToCoord(...tileIndex(tilename), nX, nY))); //:TODO: Check if this is correct
}

function checkNextTile(tilename, x, y, di, vMax, hOffset, lSurf, startAngle, startRadius, depth) {
    let [tLonNext, tLatNext, xNext, yNext] = nextTileBorder(tilename, x, y, di);
    let tilenameNext = tileId(tLonNext, tLatNext);
    let [lon, lat] = tileIndexToCoord(...tileIndex(tilename), x, y);
    let [lonNext, latNext] = tileIndexToCoord(tLonNext, tLatNext, xNext, yNext);
    let d_lSurf = Math.sqrt(((lon-lonNext)/25)**2 + ((lat-latNext)/25)**2);
    lSurf += d_lSurf;

    if (demFileData.tiles.elev.includes(tilenameNext)) {
        let curveShift = maxCurveRadius - math.cos((lSurf*25)/maxCurveRadius)*maxCurveRadius;
        let requiredElev = math.sin((lSurf*25)/maxCurveRadius)*math.tan(vMax) + curveShift + hOffset;
        let angle = (lSurf*25)/earthRadius;

        if (maxElevations[tilenameNext] < requiredElev) {
            if (maxElevations.global < requiredElev) {
                return(0, '');
            } else {
                return(checkNextTile(tilenameNext, xNext, yNext, di, vMax, hOffset, lSurf, startAngle, startRadius, depth+1));
            }
        } else {
            [lon, lat] = proj4('EU', 'WM', [tLon*100000, tLat*100000]);
            return(1, [tilenameNext, {'x': xNext, 'y': yNext, 'lSurf': lSurf, 'radius': radiusCalculation(lat), 'angle': angle}])
        }
    }
}

function calcViewLine(tiles, point, tilename, viewHeight, skipObj) {
    let pX = point.p.x;
    let pY = point.p.y;
    let di = point.di;
    let vMax = point.start.v;
    let lSurf = point.start.lsurf;
    let tileMaxElev = maxElevations[tilename];
    let hBreak = false;
    let h0 = 0;

    let latlngs = [];
    let lladd = [];
    let llon = [];

    let [lon, lat] = proj4('EU', "WM", tileIndexToCoord(...tileIndex(tilename), pX, pY));
    let startRadius = (point.start.radius ? point.start.radius : radiusCalculation(lat));  // Earths radius in the first point (in meters)
    let ps = pointSteps(di);
    let lastPoint = (point.last ? point.last : {
        'radius': radiusCalculation(lat),
        'angle': 0
    });
    let calcAngle = lastPoint.angle;

    if (point.start.hasOwnProperty('h')) {
        h0 = point.start.h;
    } else {
        h0 = tiles.elev.get(pX, pY);
    }

    let h; let objH; let x; let pRadius;

    while (inBounds(pX, pY, -.5, -.5, 3999.5, 3999.5)){
        h = tiles.elev.get(Math.round(pX), Math.round(pY));
        h = (h > -10000 ? h : 0);
        if (tiles.hasObj) {
            objH = tiles.obj.get(Math.round(pX), Math.round(pY));
            objH = (objH >= 0 ? objH : 0);
            if (lSurf > skipObj/25) {
                h += objH;
            }
        }

        [lon, lat] = proj4('EU', "WM", tileIndexToCoord(...tileIndex(tilename), pX, pY));
        pRadius = radiusCalculation(lat);

        x = Math.sin(calcAngle)*pRadius;
        
    }





}

// var queue = createResQueue(200, 500, 8)
// console.log(
//     queue
// )

//tile = openTile(demFileData, '45_39')
//console.log(tile.elev.get(1, 0))
