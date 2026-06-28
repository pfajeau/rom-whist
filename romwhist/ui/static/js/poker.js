// ---------------------------------------------------------------------------
// Poker game JS — Texas Hold'em phase support
// ---------------------------------------------------------------------------

function initialize_poker_game(active_player, allowed_actions, game_phase) {
  if (game_phase !== 'DEAL' && game_phase !== 'OVER') {
    if (active_player === username) {
      show_betting_actions(allowed_actions, window._poker_current_bet || 0);
    }
  }
  if (the_players.length >= 6) {
    $('#add_ai').prop('disabled', true);
  }
}

// ---------------------------------------------------------------------------
// Community card board
// ---------------------------------------------------------------------------

function render_poker_cards(cards, containerId) {
  let html = '';
  for (let i = 0; i < cards.length; i++) {
    let image = 'img/' + cards[i] + '.svg';
    html += '<img class="card_table" src="' + static_folder + image + '">';
  }
  $(containerId).html(html);
}

function render_poker_board(cards) {
  if (!cards || !cards.length) {
    $('#poker_board').empty();
    return;
  }
  let html = '<div style="display:flex;align-items:center;padding:6px 8px;">'
           + '<span class="poker_board_label">' + (i18n['board'] || 'Board') + '&nbsp;&nbsp;</span>'
           + '<div id="poker_board_cards" style="display:flex;gap:4px;flex-wrap:wrap;"></div></div>';
  $('#poker_board').html(html);
  render_poker_cards(cards, '#poker_board_cards');
}

// ---------------------------------------------------------------------------
// Betting UI
// ---------------------------------------------------------------------------

function show_betting_actions(allowed_actions, current_bet) {
  let html = '<div id="poker_bet_panel">';

  if (allowed_actions.indexOf('fold') >= 0) {
    html += '<button class="btn btn-danger" onclick="send_poker_action(\'fold\')" style="margin:2px">' + (i18n['fold'] || 'Fold') + '</button> ';
  }
  if (allowed_actions.indexOf('check') >= 0) {
    html += '<button class="btn btn-secondary" onclick="send_poker_action(\'check\')" style="margin:2px">' + (i18n['check'] || 'Check') + '</button> ';
  }
  if (allowed_actions.indexOf('call') >= 0) {
    html += '<button class="btn btn-primary" onclick="send_poker_action(\'call\')" style="margin:2px">' + (i18n['call'] || 'Call') + ' ' + current_bet + '</button> ';
  }
  if (allowed_actions.indexOf('bet') >= 0) {
    html += '<input type="number" id="poker_bet_amount" value="' + (window._poker_big_blind || current_bet || 1)
          + '" min="1" style="width:80px;margin:2px"> ';
    html += '<button class="btn btn-warning" onclick="send_poker_action(\'bet\', document.getElementById(\'poker_bet_amount\').value)" style="margin:2px">' + (i18n['bet'] || 'Bet') + '</button> ';
  }
  if (allowed_actions.indexOf('raise') >= 0) {
    html += '<input type="number" id="poker_bet_amount" value="' + (window._poker_big_blind || current_bet || 1)
          + '" min="1" style="width:80px;margin:2px"> ';
    html += '<button class="btn btn-warning" onclick="send_poker_action(\'raise\', document.getElementById(\'poker_bet_amount\').value)" style="margin:2px">' + (i18n['raise'] || 'Raise') + '</button> ';
  }

  html += '</div>';
  $('#poker_bet_buttons').html(html);
}

function hide_betting_actions() {
  $('#poker_bet_buttons').html('');
}

function send_poker_action(action, amount) {
  hide_betting_actions();
  socket.emit('poker action', {action: action, amount: parseInt(amount) || 0});
}

function dealNextHand() {
  hide_betting_actions();
  socket.emit('cs game started');
}

// ---------------------------------------------------------------------------
// Display helpers
// ---------------------------------------------------------------------------

function update_money_display(money) {
  for (let player in money) {
    let el = document.getElementById('money_' + player);
    if (el) el.value = money[player];
  }
}

function update_bets_display(bets) {
  for (let player in bets) {
    let el = document.getElementById('bet_round_' + player);
    if (el) el.value = bets[player];
  }
}

function update_pot_display(pot) {
  let el = document.getElementById('poker_pot_value');
  if (el) el.textContent = pot;
}

function update_phase_display(phase_label) {
  let el = document.getElementById('poker_phase_label');
  if (el) el.textContent = phase_label;
}

// ---------------------------------------------------------------------------
// Socket event registration
// ---------------------------------------------------------------------------

function register_poker_events() {
  socket.on('sc game started', function(data) {
    hide_betting_actions();
    render_poker_board(data['community_cards'] || []);
    update_pot_display(data['pot'] || 0);
    update_bets_display({});
    window._poker_big_blind = data['big_blind'];
    game_started(data);
  });

  socket.on('new hand', function(data) {
    new_hand(data, static_folder);
  });

  // Phase advanced: reveal (more) community cards, reset pot/bet displays
  socket.on('poker_phase_change', function(data) {
    update_phase_display(data['phase_label'] || data['phase']);
    render_poker_board(data['community_cards'] || []);
    update_pot_display(data['pot'] || 0);
    update_bets_display(data['bets_this_round'] || {});
    window._poker_current_bet = data['current_bet'] || 0;
    update_money_display(data['money'] || {});
    hide_betting_actions();
    // Clear cards-played area (used for inline bets)
    $('#cards_played').empty();
    let phase = data['phase_label'] || data['phase'];
    show_msg(i18n[phase.toLowerCase()] || phase);
  });

  // Whose turn it is to bet
  socket.on('poker_to_act', function(data) {
    let player = data['player'];
    window._poker_current_bet = data['current_bet'] || 0;
    update_pot_display(data['pot'] || 0);
    update_bets_display(data['bets_this_round'] || {});
    make_player_active(player);
    if (player === username) {
      show_betting_actions(data['allowed_actions'] || [], data['current_bet'] || 0);
    } else {
      hide_betting_actions();
    }
  });

  // A player has acted (fold/check/call/bet/raise)
  socket.on('poker_player_acted', function(data) {
    let player = data['player'];
    let action = data['action'];
    let amount = data['amount'];
    update_money_display(data['money'] || {});
    update_bets_display(data['bets_this_round'] || {});
    update_pot_display(data['pot'] || 0);
    make_player_inactive(player);

    // Show action in the cards_played area as a badge
    let label = action.charAt(0).toUpperCase() + action.slice(1);
    if ((action === 'bet' || action === 'raise') && amount) label += ' ' + amount;
    if (action === 'call') label += ' ' + data['pot'];
    let badge_class = action === 'fold' ? 'badge-danger'
                    : action === 'raise' || action === 'bet' ? 'badge-warning'
                    : 'badge-secondary';
    $('#cards_played').append(
      '<span class="badge ' + badge_class + '" style="margin:4px;font-size:1em">'
      + player + ': ' + label + '</span>');
  });

  socket.on('poker_next_hand', function(data) {
    update_money_display(data['money'] || {});
    update_pot_display(0);
    update_bets_display({});
    $('#cards').html('');
    update_phase_display(i18n['showdown'] || 'Showdown');

    if (username === ownername) {
      $('#poker_bet_buttons').html(
        '<button class="btn btn-success" onclick="dealNextHand()" style="margin:4px">'
        + (i18n['deal_next_hand'] || 'Deal Next Hand') + '</button>');
      show_msg(i18n['showdown_complete_deal'] || 'Showdown complete \u2014 click "Deal Next Hand" to continue.');
    } else {
      show_msg(i18n['showdown_complete_wait'] || 'Showdown complete \u2014 waiting for the dealer\u2026');
    }
  });

  socket.on('poker showdown', function(data) {
    poker_showdown(data);
  });

  socket.on('new player', function(player_name) {
    new_player(player_name);
  });

  socket.on('player left', function(player_name) {
    if (player_name.localeCompare(username) !== 0) {
      show_alert(i18n['user'] + ' ' + player_name + ' ' + i18n['left_game'],
                 'Warning', false, refresh_display);
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

// ---------------------------------------------------------------------------
// Showdown handler
// ---------------------------------------------------------------------------

function poker_showdown(data) {
  hide_betting_actions();

  let winners = data['winners'] || [];
  let hands = data['hands'] || {};
  let bestHands = data['best_hands'] || {};
  let communityCards = data['community_cards'] || [];
  let handRanks = data['hand_ranks'] || {};
  let money = data['money'] || {};

  let winnerText = winners.length === 1
    ? (i18n['winner'] || 'Winner') + ': ' + winners[0]
    : (i18n['winners'] || 'Winners') + ': ' + winners.join(', ');

  update_phase_display(i18n['showdown'] || 'Showdown');
  show_msg((i18n['showdown'] || 'Showdown') + ' \u2014 ' + winnerText);
  update_money_display(money);
  render_poker_board(communityCards);

  let html = '<div class="poker_showdown_container">';
  for (let playerName in hands) {
    let cardList = hands[playerName] || [];
    let bestCardList = bestHands[playerName] || [];
    let handRank = handRanks[playerName] || '';
    let isWinner = winners.indexOf(playerName) >= 0;
    let panelClass = 'poker_showdown_player' + (isWinner ? ' poker_showdown_winner' : '');

    html += '<div class="' + panelClass + '">';
    if (isWinner) {
      html += '<div class="poker_showdown_winner_badge">' + (i18n['winner'] || 'WINNER').toUpperCase() + '</div>';
    }
    html += '<div class="poker_showdown_player_name">' + playerName + '</div>';
    html += '<div class="poker_showdown_rank">' + (handRank || '&mdash;') + '</div>';

    html += '<div class="poker_showdown_cards_label">' + (i18n['hole_cards'] || 'Hole cards') + '</div>';
    html += '<div class="poker_showdown_cards">';
    for (let i = 0; i < cardList.length; i++) {
      html += '<img class="card_showdown" src="' + static_folder + 'img/' + cardList[i] + '.svg">';
    }
    html += '</div>';

    if (bestCardList.length) {
      html += '<div class="poker_showdown_cards_label">' + (i18n['best_hand'] || 'Best hand') + '</div>';
      html += '<div class="poker_showdown_cards">';
      for (let i = 0; i < bestCardList.length; i++) {
        html += '<img class="card_showdown" src="' + static_folder + 'img/' + bestCardList[i] + '.svg">';
      }
      html += '</div>';
    }

    html += '</div>';  // end player panel
  }
  html += '</div>';  // end container

  $('#cards_played').html(html);
}

// Small helpers
function show_msg(msg) {
  $('#msg_div').text(msg);
}

function fade_msg() {
  setTimeout(function() { $('#msg_div').fadeOut(2000, function() { $(this).show().text(''); }); }, 3000);
}
