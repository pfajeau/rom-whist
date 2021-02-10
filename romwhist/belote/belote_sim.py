import copy
import logging

from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_state import BeloteState
from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand


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
        current_state = self.get_state(BeloteState(self.id, self.sim_player))
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()

        for card in self.hands.get(self.sim_player).cards:
            self.deck.remove_card(card)

        if self.phase == BeloteGame.GamePhase.BET or self.phase == BeloteGame.GamePhase.BET2:
            self.place_bet(self.sim_player, self.bets[self.sim_player])

            # Must re-create deck and remove cards that have been distributed
            # to the sim player. Other hands are re-generated randomly
            self.deck.remove_card(self.trump_card)
            for player in self.players:
                if player != self.sim_player:
                    self.hands[player] = Hand(self.deck, BeloteGame.nb_cards_first_deal[len(self.players)])

            self.deal_2()
        else:
            # Remove from deck all cards that have been played
            cards_played_per_player = current_state.cards_played_per_player
            for player in self.players:
                if player != self.sim_player:
                    cards_played = cards_played_per_player.get(player)
                    if cards_played is None:
                        num_cards_played = 0
                    else:
                        num_cards_played = len(cards_played)
                        for card in cards_played:
                            self.deck.remove_card(Card.card_from_value(card))

                    self.hands[player] = Hand(self.deck,
                                          BeloteGame.nb_cards_first_deal[len(self.players)] +
                                          BeloteGame.nb_cards_second_deal[len(self.players)] -
                                          num_cards_played)
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