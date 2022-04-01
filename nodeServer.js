// Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

const express = require('express');
const fs = require('fs');
const path = require('path');
const url = require('url');
const querystring = require('querystring');
const ac = require ('ansicolor').nice;
const {spawn} = require('child_process');
const { Console } = require('console');
const calc = require('./serverFiles/calculations.js');
const sFunc = require('./serverFiles/serverFunctions.js');

const port = process.env.PORT || 3000;

const app = express();

app.use('/', express.static('serverFiles/mainPage'));
app.use('/sightlines', express.static('serverFiles/sightlines'));

app.get('/serverStatus', (req, res) => {
    res.send("Server is running");
    res.end();
});

app.get('/api/pjs', (req, res) => {
    res.send(calc.getVeiw(req.query.lon, req.query.lat, req.query.res, req.query.oh));
    res.end();
});

app.get('/api/grid', (req, res) => {
    res.end();
});

app.get('/api/points', (req, res) => {
    res.end();
});

app.get('/api/elev', (req, res) => {
    res.send(calc.getPoint(req.query.lon, req.query.lat, req.query.res, req.query.oh));
    res.end();
});


// Start server
app.listen(port, () => {
    // Check for errors, warnings, etc
    sFunc.serverStart();
    console.log('🔵 SERVER STARTED');
});