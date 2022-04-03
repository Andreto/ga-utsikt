const fs = require('fs')
const ac = require ('ansicolor').nice;

function findDems() {
    lookupPaths = [
        //"E:/EUDEM_1-1/demtiles",
        "./demtiles"
    ]
    for (let i = 0; i < lookupPaths.length; i++) {
        if (fs.existsSync(lookupPaths[i])) {
            console.log("Found DEMs at " + ac.green(lookupPaths[i]))
            return lookupPaths[i];
        }
    }
    console.log(ac.lightRed("Could not find DEMs"))
    return(false)
}

function countDems(folder) {
    if (!folder) {return(false);}
    let elevDems = fs.readdirSync(folder + "/elev");
    let objDems = fs.readdirSync(folder + "/objects");
    for (let i = 0; i < elevDems.length; i++) {
        elevDems[i] = elevDems[i].replace(/dem_|.tif/g, "");
    }
    for (let i = 0; i < objDems.length; i++) {
        objDems[i] = objDems[i].replace(/.tif/g, "");
    }
    console.log("Found " + 
        (elevDems.length >= 240 ? ac.green(elevDems.length) : ac.yellow(elevDems.length)) + 
    " elevation DEMs");

    console.log("Found " + 
        (objDems.length >= 74 ? ac.green(objDems.length) : ac.yellow(objDems.length)) + 
    " object-height DEMs");
    fs.writeFileSync('./serverParameters/demFiles.json', JSON.stringify({
        "path": folder,
        "tiles": {
            "elev": elevDems,
            "obj": objDems
        }

    }));
}

function serverStart() {
    demFolder = findDems()
    demCounts = countDems(demFolder)
}

function getDemFiles() {
    serverStart();
    return (JSON.parse(fs.readFileSync('./serverParameters/demFiles.json', 'utf8')));
}

module.exports = {serverStart, getDemFiles, countDems}