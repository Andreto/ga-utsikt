const fs = require('fs')

function serverStart() {
    try {
        if (fs.existsSync("./demtiles")) {
           console.log("Demfiles located")
        }
    } catch(err) {
        console.error(err)
    }
}

serverStart()