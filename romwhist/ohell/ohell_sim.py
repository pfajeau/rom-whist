import copy
import logging

#from romwhist.ai.sim_game import SimGame
from romwhist.ohell.ohell_state import OhellState
from romwhist.ohell.ohell import OhellGame

class OhellSim(OhellGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: OhellState = None, starting_action=None):
        super().__init__(state.owner, id=state.game_id)
        self.sim_player = sim_player

        self.starting_action = starting_action
        self.first_play = True
        self.agent = agent  # type: IAgent
        self.other_agent = other_agent  # type: IAgent
        self.games_counter = [0, 0]
        self.initial_state = copy.deepcopy(state)

        if state is not None:
            state_copy = copy.deepcopy(state)
            self.set_state(state_copy)

    def play_single_move(self):
        logging.debug("Playing single move")
        the_state = self.get_state(self.initial_state)

        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        elif self.active_player == self.sim_player:
            card = self.agent.get_action(the_state)
        else:
            card = self.other_agent.get_action(the_state)

        winner = self.play_card(self.active_player, card)
        return winner

    def game_loop(self) -> None:
        winner = None
        while winner is None:
            winner = self.play_single_move()

        # Play rounds until end of hand
        while not self.is_hand_completed():
            round = self.create_round()
            self.play_round(round)
        logging.debug("Hand completed")
        return


    def play_round(self, round):
        logging.debug("Playing round")
        active_player = self.get_active_player()
        winner = ""
        for i in range(len(self.get_playing_players())):
            winner = self.play_single_move()

        logging.debug("Round completed. Winner is %s, winner")
        return winner

    def run(self) -> bool:
        self.game_loop()
        return True


    def sim_player_won(self):
        logging.debug("Bets for %s: %s", self.sim_player, self.bets[self.sim_player])
        logging.debug("Wins: %s", self.wins[self.sim_player])
        sim_player_wins = (self.bets[self.sim_player] == self.wins[self.sim_player])
        return sim_player_wins

    def state(self):
        return self.get_state(OhellState(self.id, self.sim_player))