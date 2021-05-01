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
        BeloteGame.__init__(self, state.owner, id=state.game_id)
        self.sim_player = sim_player

        self.starting_action = starting_action
        self.first_play = True
        self.agent = agent
        self.other_agent = other_agent
        self.games_counter = [0, 0]

        if state is not None:
            state_copy = copy.deepcopy(state)
            self.players = state.players
            self.soft_init_dict(state_copy.bets, "")
            self.set_state(state_copy)
            logging.debug("In BeloteSim, state is %s:", state_copy.toJson())

    def play_single_move(self):
        logging.debug("Playing single move")
        #current_state = BeloteState(self.id, self.sim_player)
        current_state = self.get_state()
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
        logging.debug("Game phase is %s", self.phase)
        current_state = self.get_state()
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()

        # Remove sim players cards from deck
        for card in self.hands.get(self.sim_player).cards:
            self.deck.remove_card(card)

        if self.phase == BeloteGame.GamePhase.BET or self.phase == BeloteGame.GamePhase.BET2:
            self.place_bet(self.sim_player, self.bets[self.sim_player], ai=True)
            self.taker = self.sim_player
            self.current_bet = self.bets[self.sim_player]

            # Re-create hands from deck for other players for the simulation
            self.deck.remove_card(self.trump_card)
            for player in self.players:
                if player != self.sim_player:
                    self.hands[player] = Hand(self.deck, self.nb_cards_first_deal[len(self.players)])

            self.deal_2()
        else:
            # Remove from deck all cards that have been played
            # TODO except the ones played in current round as those need to be part
            # of the simulation
            cards_played_per_player = current_state.cards_played_per_player
            for player in self.players:
                cards_played = cards_played_per_player.get(player)
                if cards_played is not None:
                    for card in cards_played:
                        self.deck.remove_card(Card.card_from_value(card))

            cards_current_round = self.current_round.get_cards_played()
            for card in cards_current_round:
                self.deck.add_top(card)

            for player in self.players:
                if player != self.sim_player:
                    self.hands[player] = Hand(self.deck, len(self.hands[player].cards))
                logging.debug("In sim, Hand for player %s: %s", player, self.hands[player].serialize())

        winner = None
        if self.current_round is None:
            self.create_round()

        self.phase = BeloteGame.GamePhase.PLAY
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
        print ("Evaluating bet: " + str(self.bets[self.sim_player]))
        self.game_loop()
        return True

    def sim_player_won(self):
        logging.debug("Bet for %s: %s", self.sim_player, self.bets[self.sim_player])
        sim_player_wins = (self.sim_player in self.hand_winner)
        logging.debug("Wins: %s", sim_player_wins)
        return sim_player_wins

    def state(self):
        return self.get_state()