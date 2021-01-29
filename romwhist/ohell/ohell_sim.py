import logging

from romwhist.ai.sim_game import SimGame
from romwhist.ohell.ohell_state import OhellState

class OhellSim(SimGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: OhellState = None, starting_action=None):

        OhellState.__init__(self, agent, other_agent, sim_player,
                            state, starting_action)

    def sim_player_won(self):
        return self.bets[self.sim_player] == self.wins[self.sim_player]