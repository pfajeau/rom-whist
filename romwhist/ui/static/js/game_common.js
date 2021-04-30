
function play_sound(audio_file) {
  const sound = new Audio()
  sound.src = static_folder + "audio/" + audio_file
  sound.play()
}

function submit_form() {
  console.log("Submiting game_form");
  document.getElementById("game_form").submit();
}

function RecursiveUnbind($jElement) {
  // remove this element's and all of its children's click events
  $jElement.unbind();
  $jElement.removeAttr('onclick');
  $jElement.children().each(function () {
    RecursiveUnbind($(this));
  });
}

function make_players_inactive() {
  $("[name='player']").removeClass("active_player");
  $("[name='player']").addClass("normal_player");
}

function make_player_inactive(player_name) {
  $("#name_"+player_name).addClass("normal_player");
  $("#name_"+player_name).removeClass("active_player");
}

function make_player_active(player_name) {
  make_players_inactive()
  $("#name_"+player_name).removeClass("normal_player");
  $("#name_"+player_name).addClass("active_player");
}

function initialize(players) {
  // Prevent form to be submitted when user enter a message in chat area
  $('#chat_input').keydown(function (e) {
    if (e.keyCode == 13) {
      e.preventDefault();
      post_msg();
      return false;
    }
  });

  // Send button for chat
  $("#post_chat").html(i18n["send"])
  $( "#post_chat" ).click(function() {
    post_msg();
  })

  // Add game action buttons
  if (username == ownername) {
    $("#game_action_buttons").append(
    '<button id="start_game" class="btn btn-primary" name="start_game" type="button">' +
    i18n["start_game"] + '</button>');
  }


  if (username == ownername) {
    // $("#game_action_buttons").append('<button id="restart_round" class="btn btn-primary" name="restart_round" type="button">Restart Round</button>');
    $("#game_action_buttons").append(
    '<button id="stop_game" type="button" class="btn btn-warning" name="stop_game">' +
    i18n["stop_game"] + '</button>');
    document.getElementById("stop_game").onclick = function() {
      show_alert("Are you sure you want to stop the game?", "Warning", cancel=true, callback_ok=submit_form, action="stop_game");
    }
  }

  $("#game_action_buttons").append(
      '<button id="leave_game" type="button" class="btn btn-primary" name="leave_game">' +
      i18n["leave_game"] + '</button>');
  document.getElementById("leave_game").onclick = function() {
    show_alert("Are you sure you want to leave the game?", "Warning", cancel=true, callback_ok=submit_form, action="leave_game");
    // show_dialog_ok("Warning", "Are you sure you want to leave the game?", ok_function=submit_form, action="leave_game")
  }

  if (username == ownername) {
    $("#game_action_buttons").append('&nbsp;&nbsp;');

    // Have to use an html framgment here
    // Appending directly to the hame_action_buttons element does not work
    // with the loop otherwise
    var html = '<select name="player_list" id="player_list">'
    for (var i in players) {
      console.log(i)
      html= html.concat('<option value="' + players[i] + '">' + players[i] + '</option>');
    }

    html= html.concat('</select>');
    html= html.concat('&nbsp;');
    $("#game_action_buttons").append(html);
    $("#game_action_buttons").append('<button id="remove_player" class="btn btn-primary" name="remove_player" type="button">' + i18n.remove_player  + '</button>');
    document.getElementById("remove_player").onclick = function() {
      show_alert("Are you sure you want to remove this player?", "Warning", cancel=true, callback_ok=submit_form, action="remove_player");
    }
  }

  if (username == ownername) {
    // $("#game_action_buttons").append('<button id="restart_round" class="btn btn-primary" name="restart_round" type="button">Restart Round</button>');
    $("#game_action_buttons").append(
        '<button id="restart_hand" type="button" class="btn btn-warning" name="restart_hand">' +
        i18n["restart_hand"] +
        '</button>');
    document.getElementById("restart_hand").onclick = function() {
      show_alert("Are you sure you want to restart the hand", "Warning", cancel=true, callback_ok=submit_form, action="restart_hand");
    }
  }

  if (username == ownername) {
    // $("#game_action_buttons").append('<button id="restart_round" class="btn btn-primary" name="restart_round" type="button">Restart Round</button>');
    $("#game_action_buttons").append(
        '<button id="add_ai" type="button" class="btn btn-warning" name="add_ai">' +
        i18n["add_ai"] + '</button>');
    document.getElementById("add_ai").onclick = function() {
      show_alert("Please confirm you want to add an AI player", "Warning", cancel=true, callback_ok=submit_form, action="add_ai");
    }
  }


  make_players_inactive();
}

//function getValue(key, list) {
//    for (var i = 0; i < list.length; i++) {
//        var value = list[i];
//        if (value.id === key) {
//            return value;
//        }
//    }
//
//    return null;
//}

function add_card_to_table(player, card) {
  if (card == 'None') return

  let image = "img/" + card + ".svg"
  let html = '<figure class="figures">'
  console.log("PLayer: " + player)
  console.log("Card: " + card)
  html = html.concat("<img id=" + card + "_table" + ' class="card_table"' + " src=" + static_folder + image + ">")
  html = html.concat("<figcaption class='trump_caption'>" + player + "</figcaption>")
  html = html.concat("</figure>")
  $('#cards_played').append(html)
}

function populate_header(player, game_id, game_logo_url) {
  let html_frag = ""
  html_frag = html_frag.concat("<span class='game_page_title'>")
  html_frag = html_frag.concat(i18n["game_id"] + ": " + game_id)
  html_frag = html_frag.concat(" - " + player + "</span>")
  html_frag = html_frag.concat(
      "<span class='game_page_title'><a href='#scoresheet_div'>" +
      i18n["scoresheet"] +
      "</a></span>")
  html_frag = html_frag.concat(
      "<span class='logo_game'><img border='0' alt='' src=" +
      game_logo_url + " width='80'></a> </span>")

  $("#topnav").last().after(html_frag);
}

function start_game() {
  socket.emit('cs game started');
  //disable_start_game();
}

function game_stated(data) {
  console.log("game started event received")
  console.log(data)
  $("input[name='rounds']").val(0);
  $("input[name='score']").val(0);

  nb_cards_to_deal = data['nb_cards']
  $('#cards').html('');
  $('#cards_played').empty()
  $('#trump_card').empty()
  $('#button').remove()
  $('#msg_div').empty()

  // Add scoresheet
  $("#scoresheet_div").append("<td>")
}

function new_hand(data, static_url) {
  console.log("new hand event received");
  make_players_inactive();
  $('#cards').html('');
  $('#cards_played').empty()
  $("#nb_cards").removeClass("highlighted_field");
  $('#msg_div').empty()
  cards = data['cards']

  // $('#cards').append('<ul>');
  for (var card_index in cards) {
    // $('#cards').append('<br>' + data[card])
    let card =cards[card_index]
    let image = 'img/' + card + ".svg"
    // let card = data[card]
    $('#cards').append('<td>'+
      "<img id=" + card + " src=" + static_url +
      image + ' alt=' + card + ' class="card_hand"' + '>' + '</td>')

      $('#rounds input').val(0);
      // $('#bets input').html('');
    }
}

function enable_start_game() {
  if (username == ownername) {
    document.getElementById("start_game").onclick = function() {
      start_game();
    }
  }
  $("#start_game").prop("disabled",false);
}

function disable_start_game() {
  RecursiveUnbind($("#start_game"));
  $("#start_game").prop("disabled",true);
}

function make_player_play(player_name, allowed_cards) {
  console.log("In make_player_play")
  make_player_active(player_name);
  if (player_name === username) {
    // play_sound("bicycle_bell.wav")

    $( '#cards img').each(function( index ) {
      card = $(this).attr('id');
      if (allowed_cards.indexOf(card) > -1) {
        $(this).addClass("img_with_border");
        $(this).bind("click", (function () {
          card_played($(this).attr('id'))
        }));
      }
      else {
        $(this).removeClass("img_with_border");
      }
    });
  }
}

// TODO: Rename tnis function to "enable_bet"
function make_player_the_better(player_name, bet1="#bets_", bet2="") {
  let id_bet = bet1 + player_name
  if (player_name == username) {
    //play_sound("bicycle_bell.wav")
    $(id_bet).prop('readonly', false);
    $(id_bet).prop('disabled', false);
    $(id_bet).addClass("highlighted_field");
    $(id_bet).focus();
  }
  if (bet2 != "") {
    let id_bet2 = bet2 + player_name
    if (player_name == username) {
      //play_sound("bicycle_bell.wav")
      $(id_bet2).prop('readonly', false);
      $(id_bet2).prop('disabled', false);
      $(id_bet2).addClass("highlighted_field");
    }
  }
}

function player_to_play(data) {
  // Enable the cards in hand to be played
  console.log("player to play event received: " + data['player']);
  player_name=data['player'];
  allowed_cards = data['allowed_cards'];
  make_player_play(player_name, allowed_cards);
}

function card_played (card) {

  // Remove card from hand being displayed
  document.getElementById(card).remove();

  // Emit an event indicating a card has been card_played
  socket.emit('player played', card);

  // Prevent player from playing again until round is finished
  RecursiveUnbind($('#cards'));

  // Remove borders on cards
  $( '#cards img').removeClass("img_with_border");

  make_player_inactive(username);
  // $("#"+username).removeClass("active_player");
  // $("#"+username).addClass("normal_player");
}


function card_played_event(data) {

  console.log("card played event received");
  if (new_round) {
    // $('#cards_played').empty();
    new_round = false;
    first_card = data['card'];
  }
  let player_name = data['player']
  let card = data['card']
  // Display card on table

  let image = 'img/' + card + ".svg"
  // $('#cards_played').append("<img id=" + card + "_table" + " src=" + static_folder + image + ">");

  // TOOD: this  does not work for some reason
  // play_sound("cardSlide5.wav");

  let html = '<figure class="figures">'
  html = html.concat("<img id=" + card + "_table" + ' class="card_table"' + " src=" + static_folder + image + ">")
  html = html.concat("<figcaption class='trump_caption'>" + player_name + "</figcaption>")
  html = html.concat("</figure>")
  $('#cards_played').append(html)

  make_player_inactive(player_name);
}

function round_ended(data) {
  let player_name = data["winner"]
  let last_player = data["last_player"]
  console.log("round ended event received: " + player_name);

  $("#msg_div").text(i18n['round_winner'] + ": " + player_name + " " +
                     i18n['with_the'] + " " + data["card"])
  fade_msg()

  // alertify.alert("Round ended", "Round winner is: " + data["winner"] + " with the " + data["card"])
  // sleep(3000)
  make_player_inactive(last_player);
  new_round = true;
}

function clear_round() {
  console.log("clear round event received");
  $('#cards_played').empty();
}

function trump_card_received(data, caption) {
  console.log("trump card event received");
  trump_suit = data["trump_suit"]
  trump_card = data["trump_card"]
  let image = 'img/' + trump_card + ".svg"
  $('#trump_card').html('')
  $('#trump_card').append("<figure>");
  // $('#trump_card').append("<img src={{ url_for('static', filename='') }}" +
  // image + ' alt=' + trump_card + 'width=80 height=80' + '>');
  $('#trump_card').append("<img src = " + static_folder +
  image + ' alt=' + trump_card + 'width=80 height=80' + '>');
  $('#trump_card').append("<figcaption><h3 class='trump_caption'>" + caption + "</h3></figcaption>");
  $('#trump_card').append("</figure>");
  // $('#trump_card').append("Trump")

  $("#trump").prop('checked', true);
}

function new_player(player_name) {
  console.log("new player event received");
  socket.emit('join game', player_name);
  window.location.reload(false);
}

function game_over(winners) {
  console.log("Game over event received")
  console.log(winners)
  var nb_winner = 0
  var winner_list = ""
  winners.forEach(function(item, index) {
    winner_list = winner_list.concat(item, " ");
  });

  show_alert(i18n['game_over'] + " - Winner: " + winner_list);
  play_sound("applause2_x.wav")
}

function post_msg() {
  socket.emit("client post", document.getElementById("chat_input").value);
  $("#chat_input").val("");
}


function msg_posted(data) {
  sender=data['sender'];
  msg = data['msg'];
  // Display messages
  textarea = $('#chat_text')
  content = textarea.val();
  textarea.val(content + sender + ": " + msg + "\n");
  textarea.animate({scrollTop:textarea[0].scrollHeight - textarea.height()},1000);

  // For testing TODO: remove
  if (msg == "alert") {
    show_dialog_ok("Title", "Hello!")
  }
  // play_sound("beep.wav");
}

function show_question(msg, title, rsp1=i18n["ok"], rsp1_callback, rsp2=i18n["cancel"], rsp2_callback) {
  alertify.confirm().set('labels', {ok:rsp1, cancel:rsp2});
  alertify.confirm(title, msg, function() { rsp1_callback(); }, function(){ rsp2_callback });
}

function show_alert(msg, title, cancel=false, callback_ok, action="") {
  if (cancel) {
    alertify.confirm(title, msg, function() {
      //after clicking OK
      if (callback_ok) {
        $("#action_game").val(action);
        callback_ok();
      }
    }, function(){});
  }

  else {
    alertify.alert(title, msg, function() {
      if (callback_ok) {
        $("#action_game").val(action);
        callback_ok();
      }
    });
  }
}

function show_dialog_ok(title,text,ok_function, action="") {
  console.log("In show_dialog_ok...")
  $( "#dialog-message" ).dialog({
    modal: true,
    title: title,
    buttons: {
      Ok: ok_function
    }
  })
  $( "#dialog-message").html(text)
  $("#action_game").val(action);
}


function sleep(miliseconds) {
 var currentTime = new Date().getTime();
 while (currentTime + miliseconds >= new Date().getTime()) {}
}

function fade_msg() {
  $('#msg_div').fadeIn('slow', function(){
            $('#msg_div').delay(7000).fadeOut();
  });
}
