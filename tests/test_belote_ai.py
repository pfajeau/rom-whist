
import copy
import json
import logging
from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote import BeloteGame


def main():
    logging.basicConfig(filename='test_belote_ai.log',
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.INFO)

    # Test betting
    belote_ai = BeloteAiPlayer('AI1', '1')
    belote_ai.game_started(32, ["joe", "jack", "AI1", "jim"])
    cards = ["s9", "s11", "d13", "h12", "c10"]
    all_cards = {'joe': ["s12", "s13", "d8", "h9", "c7"],
                 'jack': ["s7", "h10", "d7", "d10", "c9"],
                 'AI1': ["s9", "s11", "d13", "h12", "c10"],
                 'jim': ["s8", "s14", "d11", "d14", "c11"]}

    allowed_bets = ['Pass', 'spade']
    # Create a game state
    game_state = BeloteState("test", "AI1", deck_size=32, dealer="joe", players=["joe", "jack", "AI1", "jim"])
    belote_ai.game_state = copy.deepcopy(game_state)
    belote_ai.game_state.allowed_bets = ['Pass', 'spade']
    belote_ai.game_state.hand_cards = all_cards
    belote_ai.game_state.phase = BeloteGame.GamePhase.BET
    belote_ai.game_state.trump_card = "s10"
    state_snapshop = copy.deepcopy(belote_ai.game_state)
    bet = belote_ai.player_to_bet(allowed_bets, json.dumps(belote_ai.game_state.__dict__))
    logging.info("bet = %s", bet)

    belote_ai.game_state = copy.deepcopy(state_snapshop)
    belote_ai.game_state.phase = BeloteGame.GamePhase.BET2
    belote_ai.game_state.allowed_bets = ['Pass', 'club', 'heart', 'diamond', 'spade']
    belote_ai.game_state.trump_card = "h7"
    bet = belote_ai.player_to_bet(['pass', 'club', 'heart', 'diamond', 'spade'], json.dumps(belote_ai.game_state.__dict__))
    logging.info("bet = %s", bet)

    # Test playing
    belote_ai.game_state = copy.deepcopy(state_snapshop)
    belote_ai.game_state.phase = BeloteGame.GamePhase.PLAY
    belote_ai.game_state.trump_card = "h7"
    belote_ai.game_state.trump = "heart"
    belote_ai.game_state.active_player = "AI1"
    belote_ai.game_state.taker = "AI1"
    belote_ai.game_state.allowed_cards = ["s9", "s11", "d8", "d9", "c7", "c18", "h7", "h9"]
    all_cards = {'joe': ["s9", "s11", "d8", "d9", "c7", "c18", "h7", "h9"],
                 'jack': ["s7", "s10", "d7", "d10", "c9", "c12", "h8", "h12"],
                 'AI1': ["s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11"],
                 'jim': ["s8", "s14", "d11", "d14", "c11", "c13", "h13", "h14"]}
    belote_ai.game_state.hand_cards = all_cards
    card = belote_ai.player_to_play("", belote_ai.game_state.toJson())
    logging.debug("AI played card: " + card)
    #assert card in ["s9", "s11", "d13", "h12"], card
    logging.info("Trump is: Heart")
    logging.info("AI cards: %s %s %s %s %s %s %s %s", "s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11")
    logging.info("Card chosen to start is: %s", card)


if __name__ == '__main__':
    main()
