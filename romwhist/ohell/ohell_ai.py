import logging

from romwhist.ai.ai_player import AiPlayer


class OhellAiPlayer(AiPlayer):

    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)

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
        # TOOD
        return AiPlayer.player_to_play(self, allowed_cards)

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
