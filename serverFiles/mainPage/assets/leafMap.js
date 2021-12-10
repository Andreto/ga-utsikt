var mapElem = document.getElementById("map");
var mapLogElem = document.getElementById("map-log");
var mapLoaderElem = document.getElementById("map-loader");
var calcButtonElem = document.getElementById("calc-button");



var calcResolution = 40;

// Configure map element
var map = L.map('map').setView([59, 13], 10);
L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 18,
    id: 'mapbox/outdoors-v11',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: 'pk.eyJ1IjoiYW5kcmV0byIsImEiOiJja24zZGxndzUwN3hlMnhvMDhjenlhbHFyIn0.qJGRxlYtndUtH-QNQa8LZA'
}).addTo(map);

// Create map-marker and tile bounding-box

var calcLocation = L.marker([59.5587, 13.8991], {
    color: '#FB5258',
}).addTo(map);

var tileBound;
fetch('http://localhost:3000/api/grid')
.then(response => response.json()).then(data => {
    tileBound = L.polyline(
        data,
        {color: '#6977BF', weight: 2})
        .addTo(map);
});

var pl, hz; // Map-items that displays view-poly-lines and horizon-line

// When a point on the map is clicked, this point is set as the calculation base-point
function onMapClick(e) {
    console.log(e.latlng);
    calcLocation.setLatLng([e.latlng.lat, e.latlng.lng]);
    document.getElementById("lat-disp").innerText = e.latlng.lat;
    document.getElementById("lon-disp").innerText = e.latlng.lng;
}

// loadMapData runs when the calculation-button is pressed
function loadMapData(latlng) {
    mapElem.classList.add("loading");
    mapLoaderElem.classList.add("show");
    mapLogElem.classList.remove("error");

    calcResolution = document.getElementById("resInput").value;


    fetch('http://localhost:3000/api/p?lon=' + latlng.lng + '&lat=' + latlng.lat +"&res=" + calcResolution)
    .then(response => response.json()).then(data => {
        console.log(data.toString())
        if (pl) { pl.remove(map) }
        if (hz) { hz.remove(map) }
        pl = L.polyline(data["pl"], {color: '#B13A3C', weight: 2}).addTo(map);
        hz = L.polygon(data["hz"], {color: '#E06C75', weight: 1, fillOpacity: 0,}).addTo(map);
        mapElem.classList.remove("loading");
        mapLoaderElem.classList.remove("show");
    }).catch((err) => {
        mapLogElem.innerHTML = err.message;
        mapLogElem.classList.add("error");
        mapElem.classList.remove("loading");
        mapLoaderElem.classList.remove("show");
        throw(err);
    });
}

// Define event-listeners
map.on('click', onMapClick);

calcButtonElem.addEventListener("click", function(){
    loadMapData(calcLocation.getLatLng())
});


