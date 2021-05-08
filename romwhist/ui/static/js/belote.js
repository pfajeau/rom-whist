function add_belote_button(enabled, text) {
  $("#belote_button_div").append('<button id="belote" type="button" class="btn-primary" name="belote">' + text + '</button>');
  document.getElementById("belote").onclick = function() {
    announced = $("#belote").text()
    socket.emit('belote announced', announced);
    console.log ("Belote announced")
    // TODO: change allowed cards to only allow queen and king of trump?
  }
  console.log("In add_belote_button enabled is" + enabled)
  if (enabled == false) {
    $("#belote").prop("disabled", true)
  }
}

function belote_announced(data) {
  // Add Belote/Rebelote button
  console.log("belote announced event received")
  announce_player = data['player']
  announce = data['announced']
  // if (username != announce_player) {
  //   show_alert("Player " + announce_player + " annouced " + data['announced'], data['announced'])
  // }
  $("#msg_div").text(announce_player + " announce " + announce)
  fade_msg()
  if (announce == "Rebelote" && announce_player == username) {
    // Disable Belote button
    $("#belote").remove()
  }
}

function belote_lost(msg) {
  // Disable Belote/Rebelote button
  $("#belote").remove()
  // TODO i18n
  show_alert("", msg)
  $("#msg_div").text(msg)
  fade_msg()
}

function hand_completed(data) {
  console.log("hand completed event received");

  let scores=data['scores']
  let wins = data['wins']
  let hand_nb=data['hand_nb']
  let score_row_id = "#hand_score_nb" + hand_nb
  let winners = data['winners']
  let html = "<tr>"
  // $("#scoresheet_body").append ("<tr id=" + score_row_id + ">/tr")

  for (var i in the_players) {
    let player = the_players[i]
    score = scores[player];
    bet=bets[player]
    win=wins[player]
    let id_score = "#score_" + player
    $(id_score).val(score);
    html = html.concat("<td><table class='padding-between-cols'><tr>")
    html = html.concat("<td class='scoresheet_nb'>" + score + "</td></tr></table></td>")
    // Reset the bid selection list
    bet_id = "#bets_" + player
    $(bet_id).empty()
  }

  html = html.concat("</tr>")
  $("#scoresheet_body").append(html)

  // TODO: message indicating who won the hand
  if (winners[0] == "") {
     msg = "It's a tie! Points of team who took will be given to next hand winner"
  }
  else {
    // TODO: need to translate
    msg = i18n["winners_hand"] + ": "
    for (i in winners) {
      if (i == 0) {
        msg = msg + winners[i]
      }
      else {
        msg = msg + ", and " + winners[i]
      }
    }
  }
  $("#msg_div").append("<p>" + msg + "</p>")
  fade_msg()

  let image = 'img/' + trump_card + ".svg"
  $('#trump_card').html('')
  $('#cards_played').empty()
}
