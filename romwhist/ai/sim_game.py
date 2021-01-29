from romwhist.game import CardGame
from romwhist.game_state import GameState

class SimGame(CardGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: GameState = None, starting_action=None):
        """
        :param State state: Initial game state.
        :param Card starting_action: Initial play of current player.
            If None, chosen according to `agent`'s policy.
        """
        super().__init__()
        state_copy = copy(state)

        self.game_id = state_copy.game_id
        self.players = state_copy.players
        self.trump = state_copy.trump
        self.cards_played_per_player =  state_copy.cards_played_per_player
        self.deck_size = state_copy.deck_size
        self.hand_cards = state_copy.hand_cards
        self.allowed_cards = state_copy.allowed_cards
        self.active_player = state_copy.active_player

        self.sim_player = sim_player

        self.starting_action = starting_action
        self.first_play = True
        self.agent = agent  # type: IAgent
        self.other_agent = other_agent  # type: IAgent
        self.games_counter = [0, 0]

        self._state = state_copy

    def play_single_move(self):
        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        elif self.active_player == self.sim_player:
            card = self.agent.get_action(self._state)
        else:
            card = self.other_agent.get_action(self._state)

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
           winner = self.play_single_move('')

        # Play rounds until end of hand
        while not self.is_hand_completed():
           round = self.create_round()
           self.play_round(round)

        return self.state

    def play_round(round):
        active_player = self.get_active_player()
        winner = ""
        for i in range(len(self.get_playing_players())):
            print("Allowed cards for " + active_player + " : {}".format(self.get_allowed_cards(active_player)))
            winner = self.play_single_move()

        return winner


    def run(self) -> bool:
        self.game_loop()
        return True
