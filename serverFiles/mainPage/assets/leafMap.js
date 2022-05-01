// Utsiktsberäkning | Copyright (c) 2022 Andreas Törnkvist & Moltas Lindell | CC BY-NC-SA 4.0

var mapElem = document.getElementById('map');
var mapLogElem = document.getElementById('map-log');
var mapLoaderElem = document.getElementById('map-loader');
var calcButtonElem = document.getElementById('calc-button');
var locatorButton = document.getElementById('locator-button');
var locatorSvg = document.getElementById('locator-svg');
var sateliteButton = document.getElementById('satelite-button');
var sateliteSvg = document.getElementById('satelite-svg');
var lineWeightSlider = document.getElementById('line-weight-slider');

var sateliteMapOn = false;
var blockMapClick = false;

proj4.defs([
    ['WGS84', '+proj=longlat +datum=WGS84 +no_defs'],
    ['ETRS89', '+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs']
]);

var calcChoordsETRS = proj4('WGS84', 'ETRS89', [18.07, 59.33]);

var baseApiUrl = '/';
if (window.location.hostname == 'andreto.github.io') {
    baseApiUrl = 'http://utsiktskartan.eu-north-1.elasticbeanstalk.com/';
}


// Configure map element
var map = L.map('map').setView([59.33, 18.07], 6);
mapboxMap = L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 18,
    id: 'mapbox/outdoors-v11',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: 'pk.eyJ1IjoiYW5kcmV0byIsImEiOiJja24zZGxndzUwN3hlMnhvMDhjenlhbHFyIn0.qJGRxlYtndUtH-QNQa8LZA'
})

mapboxMap.addTo(map);

googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}',{
    maxZoom: 20,
    subdomains:['mt0','mt1','mt2','mt3']
});

// Create map-marker and tile bounding-box

var calcLocation = L.marker([59.33, 18.07], {
    color: '#FB5258',
}).addTo(map);

function showTileGrids() {
    var tileBound;
    fetch(baseApiUrl + 'api/grid')
    .then(response => response.json()).then(data => {
        tileBound = L.polyline(
            data.p,
            { color: '#6977BF', weight: 2 })
            .addTo(map);
        for (i in data.l) {
            label = data.l[i];
            var marker = new L.marker(label.ch, { opacity: 0 }); //opacity may be set to zero
            marker.bindTooltip(label.txt, {permanent: true, className: "grid-label", offset: [0, 0] });
            marker.addTo(map);
        }
    });
}
// fetch('http://localhost:3000/api/points')
//     .then(response => response.json()).then(data => {
//         for (item in data) {
//             console.log("Punkt", data[item])
//             L.circle(data[item], {radius: 12.5, color: '#FF9900'}).addTo(map);
//         }
//     });

var pl, hz; // Map-items that displays view-poly-lines and horizon-line
var pld = []; var hzd = [];

// When a point on the map is clicked, this point is set as the calculation base-point
function onMapClick(e) {
    if (!blockMapClick) {
        var chETRS = proj4('WGS84', 'ETRS89', [e.latlng.lng, e.latlng.lat]);
        chETRS = [Math.round(chETRS[0] / 25) * 25, Math.round(chETRS[1] / 25) * 25];
        chWGS = proj4('ETRS89', 'WGS84', chETRS);
        calcLocation.setLatLng(chWGS.reverse());
        document.getElementById('lat-disp').innerText = chWGS[0].toFixed(6);
        document.getElementById('lon-disp').innerText = chWGS[1].toFixed(6);
        calcChoordsETRS = chETRS;
        console.log(calcChoordsETRS);
        updateMapElev(calcChoordsETRS[0], calcChoordsETRS[1]);
        //print height of clicked point
    }
}

// loadMapData runs when the calculation-button is pressed
function loadMapData(latlng) {
    mapElem.classList.add('loading');
    mapLoaderElem.classList.add('show');
    mapLogElem.classList.remove('error');

    var calcResolution = document.getElementById('resInput').value;
    var observerHeight = document.getElementById('obshInput').value;

    console.log(baseApiUrl + 'api/p?lon=' + calcChoordsETRS[0] + '&lat=' + calcChoordsETRS[1] + '&res=' + calcResolution + '&oh=' + observerHeight);
    fetch(baseApiUrl + 'api/p?lon=' + calcChoordsETRS[0] + '&lat=' + calcChoordsETRS[1] + '&res=' + calcResolution + '&oh=' + observerHeight)
        .then(response => response.json()).then(data => {
            console.log(data.toString())
            if (pl) { pl.remove(map) }
            if (hz) { hz.remove(map) }
            pl = L.polyline(data['pl'], { color: '#B13A3C', weight: 2 }).addTo(map);
            hz = L.polygon(data['hz'], { color: '#E06C75', weight: 1, fillOpacity: 0, }).addTo(map);
            mapElem.classList.remove('loading');
            mapLoaderElem.classList.remove('show');
            for (info in data['info']) {
                console.log(data['info'][info]);
            }
        }).catch((err) => {
            mapLogElem.innerHTML = err.message;
            mapLogElem.classList.add('error');
            mapElem.classList.remove('loading');
            mapLoaderElem.classList.remove('show');
            throw (err);
        });
}

function loadMapDataDirs(latlng) {
    mapElem.classList.add('loading');
    mapLoaderElem.classList.add('show');
    mapLogElem.classList.remove('error');

    var calcResolution = document.getElementById('resInput').value;
    var observerHeight = document.getElementById('obshInput').value;

    if (pld.length > 0) {
        for (let i=0; i < pld.length; i++) {
            pld[i].remove(map);
        }
    }
    pld = [];

    for (let i=0; i < calcResolution; i++) {
        fetch(baseApiUrl + 'api/pd?lon=' + calcChoordsETRS[0] + '&lat=' + calcChoordsETRS[1] + '&di=' + String(i*2*(Math.PI/calcResolution)) + '&oh=' + observerHeight)
            .then(response => response.json()).then(data => {
                let p = L.polyline(data['pl'], { color: '#B13A3C', weight: 2 }).addTo(map);
                pld.push(p);
                if (parseFloat(data.di) > (2*Math.PI - ((4*Math.PI)/calcResolution))) {
                    mapElem.classList.remove('loading');
                    mapLoaderElem.classList.remove('show');
                }
            });
    }
    // fetch('/api/pd?lon=' + calcChoordsETRS[0] + '&lat=' + calcChoordsETRS[1] + '&di=' + "1.8" + '&oh=' + observerHeight)
    // .then(response => response.json()).then(data => {
    //     let p = L.polyline(data['pl'], { color: '#B13A3C', weight: 2 }).addTo(map);
    //     pld.push(p);
    // });
}

function onResize(e) {
    var leafScale = document.getElementsByClassName('leaflet-control-scale-line')[0];
    var scaleInd = document.getElementById('scale-ind');
    var lfTxt = leafScale.innerText.split(' ');
    scaleInd.style.width = (String(parseInt(leafScale.style.width.replace('px', ''))*4)+'px');
    scaleInd.innerText = String(parseInt(lfTxt[0])*4) + ' ' + lfTxt[1];
}

function showGridLabels() {
    document.body.classList.toggle('show-grid-labels');
}

function updateMapElev(lon, lat) {
    document.getElementById('elevetion-display').innerHTML = 'Uppdaterar<br>...';
    console.log(baseApiUrl +'api/elev?lon=' + lon + '&lat=' + lat);
    fetch(baseApiUrl + 'api/elev?lon=' + lon + '&lat=' + lat)
    .then(response => response.json()).then(data => {
        console.log(data.elev);
        document.getElementById('elevetion-display').innerHTML = '<b>Markhöjd:</b> ' + data.elev + ' möh <br><b>Objekthöjd:</b> ' + data.obj + ' m';
    });
}

var scaleElem = document.createElement('div');
scaleElem.classList.add('scale-indicator');
scaleElem.innerHTML = '<div class="scale-indicator-text" id="scale-ind">100 m</div>';
document.getElementsByClassName('leaflet-control-container')[0].appendChild(scaleElem);

// Define event-listeners
map.on('click', onMapClick);
map.on('zoomend', onResize);
L.control.scale().addTo(map);

// Map Action-buttons
calcButtonElem.addEventListener('click', function () {
    loadMapDataDirs(calcLocation.getLatLng())
});
locatorButton.addEventListener('click', function () {
    locatorSvg.classList.add('spinAnim');
    map.locate({setView: true, maxZoom: 16});
});
locatorSvg.addEventListener('animationend', function () {
    locatorSvg.classList.remove('spinAnim');
});
locatorSvg.addEventListener('mouseover', function () {
    blockMapClick = true;
});
locatorSvg.addEventListener('mouseout', function () {
    blockMapClick = false;
});

sateliteButton.addEventListener('click', function () {
    if (sateliteMapOn) {
        googleSat.remove(map);
        sateliteMapOn = false;
    } else {
        googleSat.addTo(map);
        sateliteMapOn = true;
    }
    sateliteSvg.classList.add('flipCardAnim');
});
sateliteSvg.addEventListener('animationend', function () {
    sateliteSvg.classList.remove('flipCardAnim');
});
sateliteSvg.addEventListener('mouseover', function () {
    blockMapClick = true;
});
sateliteSvg.addEventListener('mouseout', function () {
    blockMapClick = false;
});
lineWeightSlider.addEventListener('input', function () {
    pl.setStyle({ weight: this.value });
});

map.locate({setView: true, maxZoom: 9});

// for (const property in hillExport) {
//     item = hillExport[property]
//     x = item.y*25 + 4600000
//     y = -item.x*25 + 4000000
//     if(item.h > 250){
//         console.log("Punkt", )
//         L.circle(proj4('ETRS89', 'WGS84', [x, y]).reverse(), {radius: 12.5, color: '#FF9900'}).addTo(map);
//     }
// }

//d0vis = L.polyline(testData0['pl'], {color: '#AACB41', weight: 4}).addTo(map);
//d1vis = L.polyline(testData1['pl'], {color: '#519ABA', weight: 2}).addTo(map);