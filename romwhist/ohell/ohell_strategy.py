"""Public-information sampling and target-aware Whist rollout tactics."""

from romwhist.ai.hidden_cards import allocate_hidden_cards
from romwhist.deck import Deck
from romwhist.hand import Hand


def inferred_voids(game):
    voids = {player: set() for player in game.players}
    for trick in game.rounds:
        if not trick.round_started:
            continue
        asked = trick.get_first_card_played().get_suit_name()
        for player, card in trick.cards_played.items():
            if card is not None and card.get_suit_name() != asked:
                voids[player].add(asked)
    return voids


def sample_hidden_hands(game, observer, rng):
    own = {str(card) for card in game.hands[observer].cards}
    played = {str(card) for trick in game.rounds for card in trick.cards_played.values()
              if card is not None}
    # The turned-up trump is outside every player's hand in this variant.
    if game.trump_card is not None:
        played.add(str(game.trump_card))
    pool = [card for card in Deck(game.deck_size).cards if str(card) not in own | played]
    slots = [player for player in game.players if player != observer
             for _ in game.hands[player].cards]
    assignment = allocate_hidden_cards(pool, slots, inferred_voids(game), {}, rng)
    for player in game.players:
        if player != observer:
            game.hands[player] = Hand(None)
            game.hands[player].cards = assignment.get(player, [])
    game.deck = Deck(0)
    game.deck.cards = assignment.get(None, [])
    game.deck._size = len(game.deck.cards)


class WhistTacticalAgent:
    def win_probabilities(self, game, player):
        """A rough bid prior, using only this player's cards and public cards."""
        own = {str(card) for card in game.hands[player].cards}
        seen = {str(card) for trick in game.rounds for card in trick.cards_played.values()
                if card is not None} | own
        if game.trump_card is not None:
            seen.add(str(game.trump_card))
        unseen = [card for card in Deck(game.deck_size).cards if str(card) not in seen]
        probabilities = []
        for card in game.hands[player].cards:
            higher = sum(other.get_suit() == card.get_suit() and other.rank > card.rank for other in unseen)
            if card.get_suit_name() == game.trump_suit:
                chance = 0.4 + 0.6 / (higher + 1)
            else:
                chance = 0.85 / (higher + 1)
                if game.trump_suit is not None:
                    chance *= 0.7
            probabilities.append(chance)
        return probabilities

    def estimate_bid(self, game, player, allowed, rng=None):
        probabilities = self.win_probabilities(game, player)
        estimate = (sum(rng.random() < chance for chance in probabilities) if rng is not None
                    else sum(probabilities))
        return min(allowed, key=lambda bid: (abs(bid - estimate), bid))

    def choose_card(self, game, allowed=None):
        player = game.active_player
        allowed = game.get_allowed_cards(player) if allowed is None else allowed
        if not allowed:
            raise ValueError('No legal card for Whist tactical policy')
        hand = {str(card): card for card in game.hands[player].cards}
        trump = game.trump_suit
        target = max(int(game.bets.get(player, 0)), 0)
        need = target - game.wins[player]

        def strength(value):
            card = hand[value]
            return (card.get_suit_name() == trump, card.rank, value)

        trick = game.current_round
        if trick is None or not trick.round_started:
            if need <= 0:
                return min(allowed, key=strength)
            seen = {str(card) for round_ in game.rounds for card in round_.cards_played.values()
                    if card is not None} | set(hand)
            if game.trump_card is not None:
                seen.add(str(game.trump_card))
            unseen = [card for card in Deck(game.deck_size).cards if str(card) not in seen]
            masters = [value for value in allowed if not any(
                card.get_suit() == hand[value].get_suit() and card.rank > hand[value].rank
                for card in unseen)]
            return min(masters, key=strength) if masters else max(allowed, key=strength)

        asked = trick.get_first_card_played().get_suit_name()
        winner = trick.winning_player_for_suit(asked)
        current = trick.cards_played[winner]
        winners = [value for value in allowed if (
            hand[value].get_suit() == current.get_suit() and hand[value].rank > current.rank) or (
            hand[value].get_suit_name() == trump and current.get_suit_name() != trump)]
        losers = [value for value in allowed if value not in winners]
        if need <= 0:
            # Shed the most dangerous losing card, or burn the highest forced
            # winner so the remaining cards are easier to lose with.
            return max(losers or allowed, key=strength)
        return min(winners, key=strength) if winners else min(allowed, key=strength)

    def get_action(self, state):
        from romwhist.ohell.ohell import OhellGame
        game = OhellGame(state.owner)
        game.populate_from_state(state)
        return self.choose_card(game, state.allowed_cards)
