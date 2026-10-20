"""A small rollout policy that uses the player's cards and public history."""

from romwhist.card import Card
from romwhist.deck import Deck


class TacticalAgent:
    def choose_card(self, game, allowed=None):
        player = game.active_player
        allowed = game.get_allowed_cards(player) if allowed is None else allowed
        if not allowed:
            raise ValueError('No legal card for tactical policy')
        ranks, points = game.card_ranks, game.card_points
        trump = Card.get_suit_initial(game.trump_suit)
        own = {str(card) for card in game.hands[player].cards}
        played = {str(card) for trick in game.rounds for card in trick.cards_played.values()
                  if card is not None}
        unseen = [str(card) for card in Deck(game.deck_size).cards if str(card) not in own | played]

        def cheap(card):
            return (card[0] == trump, points[card], ranks[card], card)

        def master(card):
            return not any(other[0] == card[0] and ranks[other] > ranks[card] for other in unseen)

        trick = game.current_round
        if trick is None or not trick.round_started:
            side_masters = [card for card in allowed if card[0] != trump and master(card)]
            if side_masters:
                return max(side_masters, key=lambda card: (points[card], ranks[card]))
            takers = game._scoring_sides()[0] if game.taker is not None else []
            trumps = [card for card in allowed if card[0] == trump]
            if player in takers and len(trumps) >= 2:
                masters = [card for card in trumps if master(card)]
                if masters:
                    return min(masters, key=cheap)
            side_cards = [card for card in allowed if card[0] != trump]
            return min(side_cards or allowed, key=cheap)

        asked = trick.get_first_card_played().get_suit_name()
        winner = trick.winning_player_for_suit(asked)
        winning = str(trick.cards_played[winner])
        partner = game.next_player(game.next_player(player)) if len(game.players) == 4 else None

        def beats(card):
            return ((card[0] == winning[0] and ranks[card] > ranks[winning]) or
                    (card[0] == trump and winning[0] != trump))

        if winner == partner:
            last = sum(card is not None for card in trick.cards_played.values()) == len(game.players) - 1
            secure = last or (master(winning) and (
                winning[0] == trump or not any(card[0] == trump for card in unseen)))
            under = [card for card in allowed if not beats(card)]
            choices = under or allowed
            if secure:
                non_trumps = [card for card in choices if card[0] != trump]
                return max(non_trumps or choices, key=lambda card: (points[card], -ranks[card]))
            return min(choices, key=cheap)
        winners = [card for card in allowed if beats(card)]
        return min(winners or allowed, key=cheap)

    def get_action(self, state):
        # Fallback for callers that expose only a serialized observation.
        from romwhist.belote.belote import BeloteGame
        game = BeloteGame(state.owner)
        game.populate_from_state(state)
        return self.choose_card(game, state.allowed_cards)
