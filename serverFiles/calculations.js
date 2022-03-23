const fs = require('fs');
const path = require('path');
const gdal = require('gdal');


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


var demFileData = JSON.parse(fs.readFileSync(path.join(__dirname, '../serverParameters/demfiles.json'), 'utf8'));

console.log(demFileData);

tile = openTile(demFileData, '45_39')