function initialize_poker_game(active_player, allowed_cards, game_phase) {
  if (game_phase === "PLAY") {
    make_player_play(active_player, allowed_cards);
  }
  if (the_players.length >= 6) {
    $("#add_ai").prop('disabled', true);
  }
}

function register_poker_events() {
  socket.on('sc game started', function(data) {
    game_started(data);
  });

  socket.on('new hand', function(data) {
    new_hand(data, static_folder);
  });

  socket.on('player to play', function(data) {
    player_to_play(data);
  });

  socket.on('card played', function(data) {
    card_played_event(data);
  });

  socket.on('round ended', function(data) {
    round_ended(data);
  });

  socket.on('hand completed', function(data) {
    poker_hand_completed(data);
  });

  socket.on('poker showdown', function(data) {
    poker_showdown(data);
  });

  socket.on('new player', function(player_name) {
    new_player(player_name);
  });

  socket.on('player left', function(player_name) {
    if (player_name.localeCompare(username) !== 0) {
      show_alert(i18n['user'] + ' ' + player_name + ' ' + i18n['left_game'], 'Warning', false, refresh_display);
    }
  });

  socket.on('game over', function(winners) {
    game_over(winners);
  });

  socket.on('msg posted', function(data) {
    msg_posted(data);
  });

  socket.on('alert', function(msg) {
    show_alert(msg, 'Warning');
  });
}

function poker_hand_completed(data) {
  let scores = data['scores'];
  for (var i in the_players) {
    let player = the_players[i];
    let id_score = '#score_' + player;
    if ($(id_score).length) {
      $(id_score).val(scores[player]);
    }
  }
  $('#msg_div').text('Hand completed');
  fade_msg();
}

function poker_showdown(data) {
  $('#cards_played').empty();
  let winners = data['winners'];
  let hands = data['hands'];
  let handRanks = data['hand_ranks'];
  let winnerText = '';
  if (winners.length === 1) {
    winnerText = i18n['winner'] + ': ' + winners[0];
  } else {
    winnerText = 'Winners: ' + winners.join(', ');
  }
  $('#msg_div').text('Poker showdown - ' + winnerText);
  fade_msg();

  for (let playerName in hands) {
    let cardList = hands[playerName];
    let handRank = handRanks[playerName] || '';
    let html = '<div class="poker_showdown_player">';
    html += '<div class="poker_showdown_header">' + playerName + ' (' + handRank + ')</div>';
    for (let i = 0; i < cardList.length; i++) {
      let card = cardList[i];
      let image = 'img/' + card + '.svg';
      html += '<img class="card_table" src="' + static_folder + image + '">';
    }
    html += '</div>';
    $('#cards_played').append(html);
  }
}
