import logging

from romwhist.belote.belote_sim import BeloteSim
from romwhist.contree.contree import ContreeGame
from romwhist.contree.contree_state import ContreeState


class ContreeSim(BeloteSim, ContreeGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: ContreeState = None, starting_action=None):
        ContreeGame.__init__(self, state.owner, id=state.game_id)
        BeloteSim.__init__(self, agent, other_agent, sim_player, state, starting_action)

        # Required because eloteSim.__init__ calls BeloteGame.__init__,
        # which sets those to the belote values
        self.nb_cards_first_deal = {1: 8, 2: 8, 3: 8, 4: 8}
        self.init_bets()
        self.BONUS_CAPOT = 250


    def sim_player_won(self):
        logging.debug("Bet for %s: %s", self.sim_player, self.bets[self.sim_player])
        sim_player_wins = (self.sim_player in self.hand_winner)
        logging.debug("Wins: %s", sim_player_wins)
        return sim_player_wins

    def game_loop(self):
        BeloteSim.game_loop(self)
