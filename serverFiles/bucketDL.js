const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');

function dlDemTile(filename) {
    var params = { Bucket: "utsiktskartan-data", Key: filename};
    var file = fs.createWriteStream('./' + filename);
    stream = s3.getObject(params).createReadStream().pipe(file);
    stream.on('close', () => {
        console.timeEnd("DL_" + filename);

    });
}

function dlDems(fileList) {    
    // Set the region 
    AWS.config.update({region: 'eu-north-1'});

    AWS.config.getCredentials(function(err) {
        if (err) console.log(err.stack);
        else {
        console.log("Access key:", AWS.config.credentials.accessKeyId);
        }
    });

    // Create S3 service object
    s3 = new AWS.S3({apiVersion: '2006-03-01'});

    const demFileData = JSON.parse(fs.readFileSync(path.join(__dirname, '../serverParameters/demFilesLock.json'), 'utf8'));
    for (let i = 0; i < demFileData.tiles.elev.length; i++) {
        try {
            dlDemTile("demtiles/elev/dem_" + demFileData.tiles.elev[i] + ".tif");
        } catch (err) {
            console.log(err);
        }
        
    }
    for (let i = 0; i < demFileData.tiles.obj.length; i++) {
        try {
            dlDemTile("demtiles/objects/" + demFileData.tiles.obj[i] + ".tif");
        } catch (err) {
            console.log(err);
        }
    }
}


module.exports = {dlDems};