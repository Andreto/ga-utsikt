var mapElem = document.getElementById('map');
var mapLogElem = document.getElementById('map-log');
var mapLoaderElem = document.getElementById('map-loader');
var calcButtonElem = document.getElementById('calc-button');
var locatorButton = document.getElementById('locator-button');
var locatorSvg = locatorButton.getElementsByClassName('locator-svg')[0];


proj4.defs([
    ['WGS84', '+proj=longlat +datum=WGS84 +no_defs'],
    ['ETRS89', '+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs']
]);

var calcChoordsETRS = proj4('WGS84', 'ETRS89', [18.07, 59.33]);

// Configure map element
var map = L.map('map').setView([59.33, 18.07], 6);
L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 18,
    id: 'mapbox/outdoors-v11',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: 'pk.eyJ1IjoiYW5kcmV0byIsImEiOiJja24zZGxndzUwN3hlMnhvMDhjenlhbHFyIn0.qJGRxlYtndUtH-QNQa8LZA'
}).addTo(map);

// Create map-marker and tile bounding-box

var calcLocation = L.marker([59.33, 18.07], {
    color: '#FB5258',
}).addTo(map);

var tileBound;
fetch('http://localhost:3000/api/grid')
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

fetch('http://localhost:3000/api/points')
    .then(response => response.json()).then(data => {
        for (item in data) {
            console.log("Punkt", data[item])
            L.circle(data[item], {radius: 12.5, color: '#FF9900'}).addTo(map);
        }
    });

var pl, hz; // Map-items that displays view-poly-lines and horizon-line

// When a point on the map is clicked, this point is set as the calculation base-point
function onMapClick(e) {
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



// loadMapData runs when the calculation-button is pressed
function loadMapData(latlng) {
    mapElem.classList.add('loading');
    mapLoaderElem.classList.add('show');
    mapLogElem.classList.remove('error');

    var calcResolution = document.getElementById('resInput').value;
    var observerHeight = document.getElementById('obshInput').value;

    console.log('http://localhost:3000/api/p?lon=' + calcChoordsETRS[0] + '&lat=' + calcChoordsETRS[1] + '&res=' + calcResolution + '&oh=' + observerHeight);
    fetch('http://localhost:3000/api/p?lon=' + calcChoordsETRS[0] + '&lat=' + calcChoordsETRS[1] + '&res=' + calcResolution + '&oh=' + observerHeight)
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
    document.getElementById('elevetion-display').innerText = "...";
    console.log('http://localhost:3000/api/elev?lon=' + lon + '&lat=' + lat);
    fetch('http://localhost:3000/api/elev?lon=' + lon + '&lat=' + lat)
    .then(response => response.json()).then(data => {
        console.log(data.elev);
        document.getElementById('elevetion-display').innerText = parseFloat(data.elev);
    });
}

function setCalcPoint(lon, lat) {
    calcChoordsETRS = [lon, lat];
    var chWGS = proj4('ETRS89', 'WGS84', [lon, lat]);
    calcLocation.setLatLng(chWGS.reverse());
    document.getElementById('lat-disp').innerText = chWGS[0].toFixed(6);
    document.getElementById('lon-disp').innerText = chWGS[1].toFixed(6);
    updateMapElev(calcChoordsETRS[0], calcChoordsETRS[1]);
}

var scaleElem = document.createElement('div');
scaleElem.classList.add('scale-indicator');
scaleElem.innerHTML = '<div class="scale-indicator-text" id="scale-ind">100 m</div>';
document.getElementsByClassName('leaflet-control-container')[0].appendChild(scaleElem);

// Define event-listeners
map.on('click', onMapClick);
map.on('zoomend', onResize);
L.control.scale().addTo(map);

L.control.scale().addTo(map);

calcButtonElem.addEventListener('click', function () {
    loadMapData(calcLocation.getLatLng())
});
locatorButton.addEventListener('click', function () {
    locatorSvg.classList.add('spinAnim');
    map.locate({setView: true, maxZoom: 16});
});
locatorSvg.addEventListener('animationend', function () {
    locatorSvg.classList.remove('spinAnim');
});



map.locate({setView: true, maxZoom: 16});

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