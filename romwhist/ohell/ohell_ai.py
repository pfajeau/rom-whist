import logging

from romwhist.ai.ai_player import AiPlayer
from romwhist.ai.ai_agents import SimpleAgent, random_action
from romwhist.ohell.ohell_state import OhellState


class OhellAiPlayer(AiPlayer):

    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)
        self.__agent = SimpleAgent(random_action)
        self.state = OhellState(game_id, self.name)


    def new_hand(self, cards):
        super().new_hand(cards)
        self.state.nb_rounds_won = 0
        self.bets = dict()

        for player in self.state.players:
            self.bets[player] = ""

    def player_to_bet(self, allowed_bets):
        logging.debug("Ohell AI PLayer to bet: %s", self.name)
        logging.debug("Ohell Player hand: %s", self.state.hand_cards_as_str)
        nr = self.state.deck_size / 4
        cv = dict()
        vh = 0
        for card in self.state.hand_cards:
            cv[str(card)] = self.compute_card_value(str(card))
            vh += cv[str(card)]
        logging.debug("Hand value: %s", vh)

        # Calculate average value of hand
        avh = len(self.state.hand_cards) * self.vd / self.state.deck_size
        logging.debug("Average value of hand: %s", avh)

        np = len(self.state.players)
        ab = len(self.state.hand_cards) / np
        bet = ab * vh / avh
        logging.debug("Calculated bet: %s", bet)

        # Round and adjust to make it valid
        bet_int = int(round(bet))
        if bet_int in allowed_bets:
            return bet_int
        else:
            # Find closest allowed bet to bet
            for abet in allowed_bets:
                if abs(abet - bet) < 1:
                    return abet

        logging.error("Could not compute bet")
        return allowed_bets[0]


    def player_to_play(self, allowed_cards):
        self.state.allowed_cards = allowed_cards
        return self.__agent.get_action(self.state)

#        play_to_win = False

        # If number of tricks made is less than bets, play to win, otherwise play to loose
        # if self.state.nb_rounds_won[self.name] < self.state.bets[self.name]:
        #     play_to_win = True

        # First to play
        # if len(self.state.cards_played_round) == 0:
        #     # For each card in hand, chek whether one is highest among cards that have
        #     # not been played yet.
        #     for card in allowed_cards:
        #         break
        # else:


        # return AiPlayer.player_to_play(self, allowed_cards)

    def compute_card_value(self, card):
       # No trump.
       if self.state.trump == "":
           rank_win = round(len(self.state.hand_cards_as_str) / 4)
           cv = 0
           for i in range(0,rank_win):
               for suit in ['c', 'h', 'd', 's']:
                   a_card = suit + str(14-i)
                   # TODO: if second highest card is the only one of that suit, don't assign it points
                   if a_card == str(card):
                       cv = 100/(i+1)
                       break
       else:
           cv = AiPlayer.compute_card_value(self, card)

       logging.debug("Card value for %s is: %s", card, cv)
       return cv
