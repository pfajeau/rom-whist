document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // When connected, configure buttons
    socket.on('connect', function() {
        // Each button should emit a "submit vote" event
        document.querySelector("#gcbutton").onclick = function() {
          socket.emit('get card', {data:'1'});
    }});

    socket.on('new card', function() {
        document.querySelector('#cards').innerHTML = "Ace of Spade";
    });
});
