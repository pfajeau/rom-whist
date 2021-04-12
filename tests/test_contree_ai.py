
import copy
import json
import logging
from romwhist.contree.contree_ai import ContreeAiPlayer
from romwhist.contree.contree_state import ContreeState
from romwhist.contree.contree import ContreeGame


def main():
    logging.basicConfig(filename='test_contree_ai.log',
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.DEBUG)

    # Test betting
    contree_ai = ContreeAiPlayer('AI1', '1')
    contree_ai.game_started(32, ["joe", "jack", "AI1", "jim"])

    all_cards = {'AI1': ["s9", "s11", "s14", "s10", "c7", "c8", "h14", "h10"],
                 'jack': ["s7", "d8", "d7", "d10", "c9", "c12", "h8", "h12"],
                 'joe': ["s12", "s13", "d9", "d12", "c10", "c14", "h9", "h11"],
                 'jim': ["s8", "d13", "d11", "d14", "c11", "c13", "h7", "h13"]}

    allowed_bets = ['80', '90','100','Capot']
    # Create a game state
    game_state = ContreeState("test", "AI1", deck_size=32, dealer="joe", players=["joe", "jack", "AI1", "jim"])
    contree_ai.game_state = copy.deepcopy(game_state)
    contree_ai.game_state.players = ["joe", "jack", "AI1", "jim"]
    contree_ai.game_state.allowed_bets = allowed_bets
    contree_ai.game_state.hand_cards = all_cards
    contree_ai.game_state.phase = ContreeGame.GamePhase.BET
    contree_ai.game_state.active_player = "AI1"

    state_snapshop = copy.deepcopy(contree_ai.game_state)
    bet = contree_ai.player_to_bet(allowed_bets, json.dumps(contree_ai.game_state.__dict__))
    logging.info("bet = %s", bet)
    assert bet.suit == "Spade"

    # Test playing
    contree_ai.game_state = copy.deepcopy(state_snapshop)
    contree_ai.game_state.phase = ContreeGame.GamePhase.PLAY
    contree_ai.game_state.trump = "Spade"
    contree_ai.game_state.active_player = "AI1"
    contree_ai.game_state.taker = "joe"
    contree_ai.game_state.allowed_cards = ["s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11"]
    all_cards = {'joe': ["s9", "s11", "d8", "d9", "c7", "c8", "h7", "h9"],
                 'jack': ["s7", "s10", "d7", "d10", "c9", "c12", "h8", "h12"],
                 'AI1': ["s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11"],
                 'jim': ["s8", "s14", "d11", "d14", "c11", "c13", "h13", "h14"]}
    contree_ai.game_state.hand_cards = all_cards
    contree_ai.game_state.bets = {"joe":"Spade_80", "jack":"", "AI1":"", "jim":""}

    card = contree_ai.player_to_play("", contree_ai.game_state.toJson())
    logging.debug("AI played card: " + card)
    #assert card in ["s9", "s11", "d13", "h12"], card
    logging.info("Trump is: Heart")
    logging.info("AI cards: %s %s %s %s %s %s %s %s", "s12", "s13", "d13", "d12", "c10", "c14", "h10", "h11")
    logging.info("Card chosen to start is: %s", card)


if __name__ == '__main__':
    main()
