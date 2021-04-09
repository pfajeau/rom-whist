import logging

from romwhist.belote.belote_sim import BeloteSim
from romwhist.contree.contree import ContreeGame
from romwhist.contree.contree_state import ContreeState


class ContreeSim(BeloteSim, ContreeGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: ContreeState = None, starting_action=None):
        ContreeGame.__init__(self, state.owner, id=state.game_id)
        BeloteSim.__init__(self, agent, other_agent, sim_player, state, starting_action)

    # def game_loop(self) -> None:
    #     logging.debug("Game phase is %s", self.phase)
    #     current_state = self.get_state()
    #     self.deck = Deck(self.deck_size)
    #     self.deck.shuffle()
    #
    #     # Remove sim players cards from deck
    #     for card in self.hands.get(self.sim_player).cards:
    #         self.deck.remove_card(card)
    #
    #     if self.phase == BeloteGame.GamePhase.BET:
    #         bet = self.bets[self.sim_player]
    #         self.place_bet(self.sim_player, bet)
    #         self.trump_suit = self.bets[self.sim_player].suit
    #
    #         # Re-create hands from deck fo other players for the simulation
    #         self.deck.remove_card(self.trump_card)
    #         for player in self.players:
    #             if player != self.sim_player:
    #                 self.hands[player] = Hand(self.deck, BeloteGame.nb_cards_first_deal[len(self.players)])
    #
    #     else:
    #         # Remove from deck all cards that have been played
    #         cards_played_per_player = current_state.cards_played_per_player
    #         for player in self.players:
    #             cards_played = cards_played_per_player.get(player)
    #             if cards_played is not None:
    #                 for card in cards_played:
    #                     self.deck.remove_card(Card.card_from_value(card))
    #
    #         for player in self.players:
    #             if player != self.sim_player:
    #                 self.hands[player] = Hand(self.deck, len(self.hands[player].cards))
    #             logging.debug("In sim, Hand for player %s: %s", player, self.hands[player].serialize())
    #
    #     winner = None
    #     if self.current_round is None:
    #         self.create_round()
    #
    #     while winner is None:
    #         winner = self.play_single_move()
    #
    #     # Play rounds until end of hand
    #     while not self.is_hand_completed():
    #         round = self.create_round()
    #         self.play_round(round)
    #
    #     self.hand_completed()
    #     logging.debug("Hand completed")
    #     return

    def sim_player_won(self):
        logging.debug("Bet for %s: %s", self.sim_player, self.bets[self.sim_player])
        sim_player_wins = (self.sim_player in self.hand_winner)
        logging.debug("Wins: %s", sim_player_wins)
        return sim_player_wins

    def game_loop(self):
       # self.phase = BeloteGame.GamePhase.PLAY
        self.taker = self.sim_player
        self.trump_suit = self.bets[self.sim_player].suit

        BeloteSim.game_loop(self)
        #self.phase = ContreeGame.GamePhase.PLAY