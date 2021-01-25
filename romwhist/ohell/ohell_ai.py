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
            cv[str(card)] = self.compute_card_value(card)
            vh += cv[str(card)]

        # Calculate average value of hand
        avh = self.vd / len(self.state.hand_cards)

        # TODO: nb of players should be given in game started event
        # For now assume 8 cards per player
        np = self.state.deck_size / 8
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
