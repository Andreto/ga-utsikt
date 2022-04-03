const fs = require('fs');
const path = require('path');
const gdal = require('gdal');


const demSize = 4000;

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


function saveJson(filename, data) {
    let tileList = []
    let yList;
    for (let y = 0; y < demSize; y++) {
        yList = []
        for (let x = 0; x < demSize; x++) {
            yList.push(Math.round(data.get(x,y)*100)/100)
        }
        tileList.push(yList)
    }   
    let json = JSON.stringify(tileList)
    fs.writeFile(path.join(demFileData.path, ("JSON/" + filename + ".json")), json, 'utf8', (err) => {
        if (err) throw err;
    });
}

filename = "45_39"
let tile = openTile(filename);
saveJson("elev/" + filename, tile.elev);
if (tile.hasObj) {
    saveJson("obj/" + filename, tile.obj);
}