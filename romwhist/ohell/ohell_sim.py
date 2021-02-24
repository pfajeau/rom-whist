import copy
import logging

# from romwhist.ai.sim_game import SimGame
from romwhist.game import CardGame
from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_state import OhellState
from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand


class OhellSim(OhellGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: OhellState = None, starting_action=None):
        OhellGame.__init__(self, state.owner, id=state.game_id)
        self.sim_player = sim_player

        self.starting_action = starting_action
        self.first_play = True
        self.agent = agent
        self.other_agent = other_agent
        self.games_counter = [0, 0]
        self.initial_state = copy.deepcopy(state)

        if state is not None:
            state_copy = copy.deepcopy(state)
            self.set_state(state_copy)

    def play_single_move(self):
        logging.debug("Playing single move")
        #current_state = OhellState(self.id, self.sim_player)
        current_state = self.get_state()
        logging.debug("In play_single_move, current_state: %s", current_state.toJson())

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
        current_state = self.get_state()
        logging.debug("In game_loop, current_state: %s", current_state.toJson())

        self.deck = Deck(self.deck_size)
        self.deck.shuffle()

        # Remove sim players cards from deck
        for card in self.hands.get(self.sim_player).cards:
            self.deck.remove_card(card)

        if self.trump_card is not None:
                self.deck.remove_card(self.trump_card)

        if self.phase == OhellGame.GamePhase.BET:
            # Re-create hands from deck for other players for the simulation

            for player in self.players:
                if player != self.sim_player:
                    self.hands[player] = Hand(self.deck, len(self.hands[self.sim_player].cards))

            self.phase = CardGame.GamePhase.PLAY
            self.active_player = self.next_player(self.dealer)
        else:
            # Remove from deck all cards that have been played
            cards_played_per_player = current_state.cards_played_per_player
            for player in self.players:
                 cards_played = cards_played_per_player.get(player)
                 if cards_played is not None:
                    for card in cards_played:
                        self.deck.remove_card(Card.card_from_value(card))

            for player in self.players:
                if player != self.sim_player:
                    self.hands[player] = Hand(self.deck, len(self.hands[player].cards))
                logging.debug("In sim, Hand for player %s: %s", player, self.hands[player].serialize())

        winner = None
        if self.current_round is None:
            self.create_round()

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
        winner = ""
        for i in range(len(self.get_playing_players())):
            winner = self.play_single_move()

        logging.debug("Round completed. Winner is %s", winner)
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
        return self.get_state()