var mapElem = document.getElementById('map');
var mapLogElem = document.getElementById('map-log');
var mapLoaderElem = document.getElementById('map-loader');
var calcButtonElem = document.getElementById('calc-button');
var locatorButton = document.getElementById('locator-button');
var locatorSvg = document.getElementById('locator-svg');
var sateliteButton = document.getElementById('satelite-button');
var sateliteSvg = document.getElementById('satelite-svg');

var sateliteMapOn = false;
var blockMapClick = false;

proj4.defs([
    ['WGS84', '+proj=longlat +datum=WGS84 +no_defs'],
    ['ETRS89', '+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs']
]);

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

var scaleElem = document.createElement('div');
scaleElem.classList.add('scale-indicator');
scaleElem.innerHTML = '<div class="scale-indicator-text" id="scale-ind">100 m</div>';
document.getElementsByClassName('leaflet-control-container')[0].appendChild(scaleElem);

// Define event-listeners
map.on('zoomend', onResize);
L.control.scale().addTo(map);

// Map Action-buttons
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

map.locate({setView: true, maxZoom: 4});

//Display sightlines
console.log(sightlinePaths.sightline)
for (i = sightlinePaths.sightline.length - 1; i >= 0; i--){
    console.log(sightlinePaths.sightline[i])
    a = L.polyline(sightlinePaths.sightline[i], {color: "#" + sightlinePaths.color[i], weight: 2, opacity: 0.5}).addTo(map);
}