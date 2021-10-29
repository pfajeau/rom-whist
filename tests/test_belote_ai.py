
import copy
import json
import logging
from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote import BeloteGame
from romwhist.player import Player


def main():
    logging.basicConfig(filename='test_belote_ai.log',
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.DEBUG)

    # Test betting
    # players = ["joe", "jack", "AI1", "jim"]
    # belote = BeloteGame("joe", "1")
    # for player in players:
    #     belote.add_player(player)

    player_names = ["Joe", "Jack", "AI1", "Jim"]
    players = []
    players_by_name = dict()

    Joe = Player("Joe")
    belote = BeloteGame(Joe)

    for player_name in player_names:
        player = Player(player_name)
        belote.add_player(player)

        players_by_name[player_name] = player
        players.append(player)

    Jack = players_by_name["Jack"]
    Jim = players_by_name["Jim"]
    AI1 = BeloteAiPlayer(players_by_name["AI1"], "1")

    belote.start_game()
    belote.deal(dealer=Joe)

    AI1.game_started(32, players)
    cards = ["s9", "s11", "d13", "h12", "c10"]
    all_cards = {'Joe': ["s12", "s13", "d8", "h9", "c7"],
                 'Jack': ["s7", "h10", "d7", "d10", "c9"],
                 'AI1': ["s9", "s11", "d13", "h12", "c10"],
                 'Jim': ["s8", "s14", "d11", "d14", "c11"]}

    allowed_bets = ['Pass', 'spade']
    # Create a game state
    AI1.game_state = belote.get_state()
    AI1.game_state.allowed_bets = ['Pass', 'spade']
    AI1.game_state.hand_cards = all_cards

    AI1.game_state.phase = BeloteGame.GamePhase.BET
    AI1.game_state.trump_card = "s10"
    # state_snapshop = copy.deepcopy(AI1.game_state)
    print("In test belote, state is %s:", AI1.game_state.to_json())

    #bet = AI1.player_to_bet(allowed_bets, json.dumps(AI1.game_state.__dict__))
    bet = AI1.player_to_bet(allowed_bets, AI1.game_state.to_json())

    logging.info("bet = %s", bet)

    # AI1.game_state = copy.deepcopy(state_snapshop)
    AI1.game_state.phase = BeloteGame.GamePhase.BET2
    AI1.game_state.allowed_bets = ['Pass', 'club', 'heart', 'diamond', 'spade']
    AI1.game_state.trump_card = "h7"
    bet = AI1.player_to_bet(['pass', 'club', 'heart', 'diamond', 'spade'],
                            AI1.game_state.to_json())
    logging.info("bet = %s", bet)

    # Test playing
    belote.populate_from_state(AI1.game_state)
    belote.place_bet(AI1.player, "spade", True)
    belote.deal_2(dealer=Joe)
    belote.play_card(Jack, "d7")
    AI1.game_state = belote.get_state()
    all_cards = {'Joe': ["s9", "s11", "d8", "d9", "c7", "c8", "h7", "h9"],
                 'Jack': ["s7", "s10", "d10", "c9", "c12", "h8", "h12"],
                 'AI1': ["s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11"],
                 'Jim': ["s8", "s14", "d11", "d14", "c11", "c13", "h13", "h14"]}
    AI1.game_state.hand_cards = all_cards
    AI1.game_state.allowed_cards = ["d13", "d12"]
    card = AI1.player_to_play("", AI1.game_state.to_json())
    logging.debug("AI played card: " + card)
    #assert card in ["s9", "s11", "d13", "h12"], card
    logging.info("Trump is: Heart")
    logging.info("AI cards: %s %s %s %s %s %s %s %s", "s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11")
    logging.info("Card chosen to start is: %s", card)


if __name__ == '__main__':
    main()
