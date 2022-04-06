// Utsiktsberäkning 
// Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

const fs = require('fs');
const path = require('path');
const gdal = require('gdal-async');
const proj4 = require('proj4');

proj4.defs([
    ['WM', '+proj=longlat +datum=WGS84 +no_defs'],
    ['EU', '+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs']
]);

const earthRadius = 6371000;
const equatorRadius = 6378137;
const poleRadius = 6356752;
const maxCurveRadius = (equatorRadius**2)/poleRadius;

var exportData = [];

const demFileData = JSON.parse(fs.readFileSync(path.join(__dirname, '../serverParameters/demFiles.json'), 'utf8'));
const maxElevations = JSON.parse(fs.readFileSync(path.join(__dirname, '../serverParameters/maxElevations.json'), 'utf8'));

function openTile(tilename){
    let tile = {};
    tile.elev = gdal.open(path.join(demFileData.path,('elev/dem_' + tilename + '.tif'))).bands.get(1).pixels;
    if (demFileData.tiles.obj.includes(tilename)) {
        tile.obj = gdal.open(path.join(demFileData.path,('objects/' + tilename + '.tif'))).bands.get(1).pixels;
        tile.hasObj = true;
    } else {
        tile.hasObj = false;
    }
    return(tile);
}

function exportCsv(data) {
    let csvContent = ("sep=,\n" + data.map(e => e.join(",")).join("\n"));
    fs.writeFileSync(path.join(__dirname, '../temp/tmpData.csv'), csvContent);
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
        xChange = (Math.cos(di)/Math.abs(Math.cos(di)));
        yChange = Math.abs(Math.tan(di)) * (Math.sin(di) ? (Math.sin(di) / Math.abs(Math.sin(di))) : 0);
    } else {
        yChange = (Math.sin(di)/Math.abs(Math.sin(di)));
        xChange = ((Math.tan(di)) ? Math.abs(1/(Math.tan(di))) : 1) * (Math.cos(di) ? (Math.cos(di) / Math.abs(Math.cos(di))) : 0);
    }    
    let lChange = Math.sqrt(xChange**2 + yChange**2);
    return({'x': xChange, 'y': yChange, 'l': lChange});
}

function sssAngle(r1, r2, l){
    let cosv = ((r1**2 + r2**2 - l**2)/(2*r1*r2));
    return((cosv <= 1) ? Math.acos(cosv) : Math.acos(cosv**-1));
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
    let xLen = ((Math.cos(di) > 0) ? 4000-x : -1-x);
    let yLen = ((Math.sin(di) > 0) ? -1-y : 4000-y);
    let xCost = (Math.cos(di) ? Math.abs(xLen / Math.cos(di)) : 10000);
    let yCost = (Math.sin(di) ? Math.abs(yLen / Math.sin(di)) : 10000);
    let nX; let nY;

    if (xCost < yCost){
        nX = x + xLen;
        nY = y + Math.abs(xLen * Math.tan(di))*((Math.sin(di) > 0) ? 1 : -1);
    } else {
        nX = x + Math.abs(yLen / Math.tan(di))*((Math.cos(di) > 0) ? 1 : -1);
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
        let curveShift = maxCurveRadius - Math.cos((lSurf*25)/maxCurveRadius)*maxCurveRadius;
        let requiredElev = (Math.sin((lSurf*25)/maxCurveRadius)*Math.tan(vMax)) + curveShift + hOffset;
        let angle = (lSurf*25)/earthRadius;

        if (maxElevations[tilenameNext] < requiredElev) {
            if (maxElevations.global < requiredElev) {
                return([0, '', {}]);
            } else {
                return(checkNextTile(tilenameNext, xNext, yNext, di, vMax, hOffset, lSurf, startAngle, startRadius, depth+1));
            }
        } else {
            [lon, lat] = proj4('EU', 'WM', tileIndexToCoord(...tileIndex(tilename), xNext, yNext));
            return([1, tilenameNext, {'x': xNext, 'y': yNext, 'lSurf': lSurf, 'radius': radiusCalculation(lat), 'angle': angle}])
        }
    } else {
        return([2, '', {}]);
    }
}

function calcViewLine(tiles, point, tilename, viewHeight, skipObj) {
    let pX = point.p.x;
    let pY = point.p.y;
    let di = point.di;
    let vMax = point.start.v;
    let lSurf = point.start.lSurf;
    let tileMaxElev = maxElevations[tilename];
    let hBreak = false;
    let h0 = 0;

    let latlngs = [];
    let lladd = [];
    let llon = false;


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

    h0 = (h0 > -10000 ? h0 : 0);

    let h; let objH; let x; let y; let v; let pRadius; let curveShift; let requiredElev;
    while (inBounds(pX, pY, -.5, -.5, 3999.5, 3999.5)) {
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
        curveShift = Math.sqrt(Math.pow(pRadius, 2) - Math.pow(x, 2)) - startRadius;
        x -= Math.sin(calcAngle)*h;
        y = Math.cos(calcAngle)*h + curveShift - h0 - viewHeight;
        
        calcAngle += sssAngle(lastPoint.radius, pRadius, ps.l*25);
        lastPoint = {
            'radius': pRadius,
            'angle': calcAngle
        };

        v = (x != 0 ? Math.atan(y/x) : -Math.PI/2);

        //exportData.push([x, y, h, v, vMax, curveShift, lSurf, pRadius]);

        if (v > vMax && x > 0) {
            if (llon) {
                if (lladd.length > 1) {
                    lladd[1] = [lat, lon];
                } else {
                    lladd.push([lat, lon]);
                }
            } else {
                lladd.push([lat, lon]);
                llon = true;
            }
            vMax = v;
        } else if (llon) {
            if (lladd.length < 2) {
                lladd = [lladd[0], lladd[0]];
            }
            latlngs.push(lladd);
            llon = false;
            lladd = [];
        }

        requiredElev = (Math.tan(vMax)*x) - curveShift + h0 + viewHeight;
        if (requiredElev > tileMaxElev && x > 0) {
            hBreak = true;
            break;
        }

        lSurf += ps.l;
        pX += ps.x;
        pY -= ps.y;
    }
    if (llon) {
        latlngs.push(lladd);
    }

    queueObj = {
        'p': {'x': 0, 'y': 0},
        'di': di,
        'start': {'v': vMax, 'lSurf': lSurf, 'radius': startRadius, 'h': h0},
        'last': lastPoint
    }

    let tLon; let tLat; let stX; let stY;
    [tLon, tLat, stX, stY] = coordToTileIndex(...tileIndexToCoord(...tileIndex(tilename), Math.round(pX), Math.round(pY)))
    let cnCode; let cnObj;

    if (hBreak) {
        [cnCode, cnTile, cnObj] = checkNextTile(tilename, stX, stY, di, vMax, (h0 + viewHeight), lSurf, lastPoint.angle, startRadius, 0);
        
        if (cnCode == 0) {
            return({'ll': latlngs, 'status': 0, 'msg': ''});
        } else if (cnCode == 1) {
            queueObj.p = {'x': cnObj.x, 'y': cnObj.y};
            queueObj.start.lSurf = cnObj.lSurf;
            queueObj.last = {'radius': cnObj.radius, 'angle': cnObj.angle}
            return({'ll': latlngs, 'status': 1, 'msg': {'t': cnTile, 'q': queueObj}});
        } else if (cnCode == 2) {
            return({'ll': latlngs, 'status': 2, 'msg': ["warn", "Some of the view is not visible due to the lack of DEM data"]});
        }
    } else if (demFileData.tiles.elev.includes(tileId(tLon, tLat))) {
        queueObj.p = {'x': stX, 'y': stY};
        return({'ll': latlngs, 'status': 1, 'msg': {'t': tileId(tLon, tLat), 'q': queueObj}});
    } else {
        return({'ll': latlngs, 'status': 2, 'msg': ["warn", "Some of the view is not visible due to the lack of DEM data"]});
    }
}

function calcVeiwPolys(queue, viewHeight) {
    let lines = [];
    let hzPoly = [];
    let exInfo = [];

    let skipObj = 200;
    
    let tilename; let element; let tile; let point; let vLine

    

    while (Object.keys(queue).length > 0) {
        tilename = Object.keys(queue)[0];
        tile = openTile(tilename);

        while (queue[tilename].length > 0) {
            point = queue[tilename].pop();
            vLine = calcViewLine(tile, point, tilename, viewHeight, skipObj);
            for (let i = 0; i < vLine.ll.length; i++) {
                lines.push(vLine.ll[i]);
            }

            if (vLine.status == 1) {
                if (queue.hasOwnProperty(vLine.msg.t)) {
                    queue[vLine.msg.t].push(vLine.msg.q);
                } else {
                    queue[vLine.msg.t] = [vLine.msg.q];
                }
            } else if (vLine.status == 2 && ! exInfo.includes(vLine.msg)) {
                exInfo.push(vLine.msg);
            }
        }
        
        delete queue[tilename];
    }
    return({'pl': lines, 'hz': hzPoly, 'info': exInfo});
}



function getVeiw(lon, lat, res, viewHeight) { //Returns a list of latlngs of the view from a point (lon, lat) with a resolution (res) and a view height (viewHeight)
    queue = createResQueue(lon, lat, res);
    return(calcVeiwPolys(queue, viewHeight));
}

function getVeiwOneDir(lon, lat, di, viewHeight) { //Returns a list of latlngs of the view from a point (lon, lat) in one direction (di) and a view height (viewHeight)
    queue = createDiQueue(lon, lat, [di]);
    var calcD = calcVeiwPolys(queue, viewHeight);
    calcD.di = di;
    //exportCsv(exportData);
    return(calcD);
}

function getPoint(lon, lat) {
    let [tLon, tLat, x, y] = coordToTileIndex(lon, lat);
    let tile = openTile(tileId(tLon, tLat));
    return({
        'lon': lon,
        'lat': lat,
        'elev': Math.round(tile.elev.get(x, y)*100)/100,
        'obj': (tile.hasObj ? tile.obj.get(x, y) : null)
    })
}

module.exports = { getVeiw, getPoint, getVeiwOneDir};

// var queue = createResQueue(200, 500, 8)
// console.log(
//     queue
// )

//getVeiw(4511250, 3320700, 9, 2)
// var tiles = openTile("44_39");

// var p = {
//     'p': {'x': 0, 'y': 0},
//     'di': 0,
//     'start': {'v': -4, 'lSurf': 0, 'radius': 0},
//     'last': 0 
// }
// console.log(calcViewLine(tiles, p, "44_39", 2, 100).ll);
