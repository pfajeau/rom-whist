document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // When connected, configure buttons
    socket.on('connect', function() {
        // Each button should emit a "submit vote" event
        document.querySelector("#deal").onclick = function() {
          socket.emit('get cards', {data:'2'});
        }
    });

    socket.on('new card', function() {
        document.querySelector('#cards').innerHTML = "Ace of Spade";
    });

    socket.on('new hand', function(data) {
        document.getElementById('cards').innerHTML = '';
        for (var card in data) {
            document.getElementById('cards').innerHTML += '<li>' + card + '</li>';
        }
    });


    socket.on('new player', function(player_name) {
        alert('new player joined')
        $('#players').append('<br>' + player_name);
    });
});
