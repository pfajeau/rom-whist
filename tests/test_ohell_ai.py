
import copy
import json
import logging
from romwhist.ohell.ohell_ai import OhellAiPlayer
from romwhist.ohell.ohell_state import OhellState
from tests import test_common

if __name__ == '__main__':

    logging.basicConfig(filename='test_ohell_ai.log', level=logging.INFO)

    ohell_ai = OhellAiPlayer('AI1', '1')
    ohell_ai.game_started(32, ["joe", "jack", "AI1", "jim"])
    cards = ["s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11"]
    all_cards = {'joe': ["s9", "s11", "d8", "d9", "c7", "c18", "h7", "h9"],
                 'jack': ["s7", "s10", "d7", "d10", "c9", "c12", "h8", "h12"],
                 'AI1': ["s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11"],
                 'jim': ["s8", "s14", "d11", "d14", "c11", "c13", "h13", "h14"]}
    ohell_ai.new_hand(cards)

    # allowed_bets = ['0','1','2','3','4','5','6']
    allowed_bets = [0,1,2,3,4,5,6]
    # Create a game state
    game_state = OhellState("test", "AI1", trump="s", deck_size=32, dealer="joe", players=["joe", "jack", "AI1", "jim"],
                            allowed_bets=allowed_bets)
    ohell_ai.game_state = copy.deepcopy(game_state)
    ohell_ai.game_state.allowed_bets = [0,1,2,3,4,5,6]
    ohell_ai.game_state.hand_cards = all_cards
    state_snapshop = copy.deepcopy(ohell_ai.game_state)
    bet = ohell_ai.player_to_bet(allowed_bets, json.dumps(ohell_ai.game_state.__dict__))
    logging.info("bet = %s", bet)
    #assert bet == 3, bet

    ohell_ai.game_state = copy.deepcopy(state_snapshop)
    ohell_ai.game_state.trump = ""
    ohell_ai.game_state.allowed_bets = [0,1,2,3,4,5,6]
    bet = ohell_ai.player_to_bet(allowed_bets, json.dumps(ohell_ai.game_state.__dict__))
    logging.info("bet = %s", bet)
    #assert bet == 2, bet


    #ohell_ai = OhellAiPlayer('AI1', '2')
    #ohell_ai.game_started(32)
    ohell_ai.game_state = copy.deepcopy(state_snapshop)
    ohell_ai.game_state.trump = ""
    ohell_ai.game_state.hand_cards = all_cards
    ohell_ai.game_state.allowed_bets = [0,1,2,3,4,5,6]
    bet = ohell_ai.player_to_bet(allowed_bets, ohell_ai.game_state.toJson())
    logging.info("bet = %s", bet)
    #assert bet == 2, bet

    ohell_ai.game_state = copy.deepcopy(state_snapshop)
    ohell_ai.game_state.trump = ""
    ohell_ai.game_state.hand_cards = all_cards
    ohell_ai.game_state.allowed_bets = [0,1,2,3,4,5,6]
    bet = ohell_ai.player_to_bet(allowed_bets, ohell_ai.game_state.toJson())
    logging.info("bet = %s", bet)
    #assert bet == 0, bet

    ohell_ai.card_played("joe", "s7")
    # assert len(ohell_ai.game_state.deck.cards)== 31, len(ohell_ai.state.deck.cards)
    # assert ohell_ai.game_state.cards_played_per_player["joe"][0] == "s7"
    # assert ohell_ai.game_state.cards_played_by_suit["s"][0] == "s7"
    # assert len(ohell_ai.game_state.cards_played) == 1

    for i in range(1,5):
        ohell_ai.game_state = copy.deepcopy(state_snapshop)
        print (i)
        all_cards = {'joe': ["s9", "s11", "d8", "d9", "c7", "c18", "h7", "h9"],
                     'jack': ["s7", "s10", "d7", "d10", "c9", "c12", "h8", "h12"],
                     'AI1': ["s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11"],
                     'jim': ["s8", "s14", "d11", "d14", "c11", "c13", "h13", "h14"]}
        ohell_ai.game_state.hand_cards = all_cards
        ohell_ai.game_state.bets['joe'] = int(0)
        ohell_ai.game_state.bets['jack'] = int(0)
        ohell_ai.game_state.allowed_bets = [0, 1, 2, 3, 4, 5, 6]
        bet = ohell_ai.player_to_bet(allowed_bets, ohell_ai.game_state.toJson())
        ohell_ai.game_state.bets['AI1'] = bet
        ohell_ai.game_state.active_player = "AI1"
        ohell_ai.game_state.dealer = "jack"


        card = ohell_ai.player_to_play(["s9", "s11", "d8", "d9", "c7"], ohell_ai.game_state.toJson())
        logging.debug("AI played card: " + card)
        assert card in ["s9", "s11", "d8", "d9", "c7"], card