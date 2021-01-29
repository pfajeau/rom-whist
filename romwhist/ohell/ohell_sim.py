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
        self.initial_state = state
        self.set_state(state)

    def play_single_move(self):
        logging.debug("Playing single move")
        state = self.state()

        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        elif self.active_player == self.sim_player:
            card = self.agent.get_action(state)
        else:
            card = self.other_agent.get_action(state)

        winner = self.play_card(self.active_player, card)
        return winner

    def game_loop(self) -> None:
        # Active player plays
        # until end of round
        # Then while there is still a card in hand
        # Play each round
        # Determine whether AI player won or not (game dependant)
        winner = None
        while winner is None:
            winner = self.play_single_move()

        # Play rounds until end of hand
        while not self.is_hand_completed():
            round = self.create_round()
            self.play_round(round)
        return


    def play_round(self, round):
        logging.debug("Playing round")
        active_player = self.get_active_player()
        winner = ""
        for i in range(len(self.get_playing_players())):
            winner = self.play_single_move()

        return winner

    def run(self) -> bool:
        self.game_loop()
        return True


    def sim_player_won(self):
        logging.debug("sim_player_won: %s",  self.bets[self.sim_player] == self.wins[self.sim_player])
        return self.bets[self.sim_player] == self.wins[self.sim_player]

    def state(self):
        return self.get_state(OhellState(self.id, self.sim_player))