// Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

const express = require('express');
const fs = require('fs');
const path = require('path');
const url = require('url');
const querystring = require('querystring');
const ac = require ('ansicolor').nice;
const {spawn} = require('child_process');
const { Console } = require('console');

const port = process.env.PORT || 3000

const app = express();

function spawnPythonProc(req, res, command, funcData) {
    var dataToSend = '';
    // spawn new child process to call the python script
    const pyPrcs = spawn('python', command, { maxBuffer: Infinity });
    // collect data from script
    pyPrcs.stdout.on('data', function (data) {
     console.log(ac.lightBlue((new Date()).toISOString()), 'Running', command[0]);
     dataToSend += data.toString();
    });
    pyPrcs.on('close', (code) => {
        funcData(req, res, dataToSend, code);
    });
    pyPrcs.stderr.on('data', (data) => {
        console.log(ac.red((new Date()).toISOString()), ac.lightRed('Error: ' + data.toString()));
    });

    pyPrcs.on('error', (err) => {
        console.log(err.ac.red);
    }); 
}

app.use('/', express.static('serverFiles/mainPage'))
app.use('/sightlines', express.static('serverFiles/sightlines'))

app.get('/api/p', (req, res) => {
    spawnPythonProc(req, res, 
        ['./py/node_exec/getViewPolygons.py', req.query.lon, req.query.lat, req.query.res,  req.query.oh],
        function(req, res, data, code) {
            console.log(`getViewPolygons.py closed with ${code}`);
            res.send(data);
            res.end();
        }
    )
});

app.get('/api/grid', (req, res) => {
    spawnPythonProc(req, res, 
        ['./py/node_exec/gridPattern.py'],
        function(req, res, data, code) {
            console.log(`gridPattern.py closed with ${code}`);
            res.send(data);
            res.end();
        }
    )
});

app.get('/api/points', (req, res) => {
    spawnPythonProc(req, res, 
        ['./py/node_exec/showCsvPoints.py'],
        function(req, res, data, code) {
            console.log(`showCsvPoints.py closed with ${code}`);
            res.send(data);
            res.end();
        }
    )
});

app.get('/api/elev', (req, res) => {
    spawnPythonProc(req, res, 
        ['./py/node_exec/getPointElev.py', req.query.lon, req.query.lat],
        function(req, res, data, code) {
            console.log(`getPointElev.py closed with ${code}`);
            res.send(data);
            res.end();
        }
    )
});


// Start server
app.listen(port, () => {
    // Check for errors, warnings, etc
    spawnPythonProc({}, {}, 
        ['./py/node_exec/serverStart.py'],
        function(req, res, data, code) {
            data = JSON.parse(data);
            console.log("Running startup-checks:")
            if(data.err.length) {n = ac.red(data.err.length)} else {n = ac.green(data.err.length)}
            console.log(n, "errors");
            for (e in data.err) {console.log(ac.red(data.err[e]))}
            if(data.warn.length) {n = ac.yellow(data.warn.length)} else {n = ac.green(data.warn.length)}
            console.log(n, "warnings");
            for (e in data.warn) {console.log(ac.yellow('- ' + data.warn[e]))}
        }
    )

    console.log('🔵 SERVER STARTED');
});