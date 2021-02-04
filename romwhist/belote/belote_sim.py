import copy
import logging

from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote import BeloteGame

class BeloteSim(BeloteGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: BeloteState = None, starting_action=None):
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
        current_state = BeloteState(self.id, self.sim_player)
        current_state = self.get_state(current_state)
        #the_state = self.get_state(self.initial_state)

        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        elif self.active_player == self.sim_player:
            card = self.agent.get_action(current_state)
        else:
            card = self.other_agent.get_action(current_state)

        winner = self.play_card(self.active_player, card)
        return winner

    def game_loop(self) -> None:
        logging.info("Game phase is %s", self.phase)
        if self.phase == BeloteGame.GamePhase.BET or self.phase == BeloteGame.GamePhase.BET2:
            self.place_bet(self.sim_player, self.bets[self.sim_player])
            self.deal_2()

        winner = None
        while winner is None:
            winner = self.play_single_move()

        # Play rounds until end of hand
        while not self.is_hand_completed():
            round = self.create_round()
            self.play_round(round)
        self.hand_completed()
        logging.debug("Hand completed")
        return


    def play_round(self, round):
        logging.debug("Playing round")
        active_player = self.get_active_player()
        winner = ""
        for i in range(len(self.get_playing_players())):
            winner = self.play_single_move()

        logging.debug("Round completed. Winner is %s", winner)
        return winner

    def run(self) -> bool:
        self.game_loop()
        return True


    def sim_player_won(self):
        logging.debug("Bet for %s: %s", self.sim_player, self.bets[self.sim_player])
        sim_player_wins = (self.sim_player in self.hand_winner)
        logging.debug("Wins: %s", sim_player_wins)
        return sim_player_wins

    def state(self):
        return self.get_state(BeloteState(self.id, self.sim_player))