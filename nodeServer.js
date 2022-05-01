// Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

const express = require('express');
const fs = require('fs');
const path = require('path');
const url = require('url');
const querystring = require('querystring');
const ac = require ('ansicolor').nice;
const { spawn } = require('child_process');
const { Console } = require('console');
const calc = require('./serverFiles/calculations.js');
const sFunc = require('./serverFiles/serverFunctions.js');
const bucketDL = require('./serverFiles/bucketDL.js');

const port = process.env.PORT || 3000;

const app = express();

app.get('/serverStatus', (req, res) => {
    res.send("Server is running");
    res.end();
});

app.get('/p', (req, res) => {
    res.send(calc.getVeiw(req.query.lon, req.query.lat, req.query.res, req.query.oh));
});

app.get('/pd', (req, res) => {
    res.send(calc.getVeiwOneDir(req.query.lon, req.query.lat, req.query.di, req.query.oh))
});

app.get('/grid', (req, res) => {
    res.send(calc.getGridLines(req.query.layer));
});

app.get('/elev', (req, res) => {
    res.send(calc.getPoint(req.query.lon, req.query.lat, req.query.res, req.query.oh));
});

app.get('/demFiles', (req, res) => {
    res.send(JSON.stringify(sFunc.getDemFiles()));
});

// Start server
app.listen(port, () => {
    // Check for errors, warnings, etc
    sFunc.serverStart();
    //bucketDL.dlDems();
    console.log('🔵 SERVER STARTED');
});