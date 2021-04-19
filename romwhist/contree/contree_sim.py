import logging

from romwhist.belote.belote_sim import BeloteSim
from romwhist.contree.contree import ContreeGame
from romwhist.contree.contree_state import ContreeState


class ContreeSim(BeloteSim, ContreeGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: ContreeState = None, starting_action=None):
        ContreeGame.__init__(self, state.owner, id=state.game_id)
        BeloteSim.__init__(self, agent, other_agent, sim_player, state, starting_action)


    def sim_player_won(self):
        logging.debug("Bet for %s: %s", self.sim_player, self.bets[self.sim_player])
        sim_player_wins = (self.sim_player in self.hand_winner)
        logging.debug("Wins: %s", sim_player_wins)
        return sim_player_wins

    def game_loop(self):
        BeloteSim.game_loop(self)
