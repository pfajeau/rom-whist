"""Sample unknown cards using only the observer's hand and public evidence."""

from romwhist.belote.belote_status import BeloteStatus
from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand
from romwhist.round import Round
from romwhist.ai.hidden_cards import allocate_hidden_cards


def inferred_voids(game):
    voids = {player: set() for player in game.players}
    for game_round in game.rounds:
        if not game_round.round_started:
            continue
        prefix = Round(game.players, game.trump_suit)
        player = game_round.first_player
        asked = game_round.get_first_card_played().get_suit_name()
        for _ in game.players:
            card = game_round.cards_played.get(player)
            if card is None:
                break
            if card.get_suit_name() != asked:
                voids[player].add(asked)
                winner = prefix.winning_player_for_suit(asked)
                partner = game.next_player(game.next_player(player)) if len(game.players) == 4 else None
                winning_card = prefix.cards_played[winner]
                # Contrée permits discarding while holding lower trumps when
                # an opponent has cut. That does not prove trump exhaustion.
                must_cut = winner != partner and (
                    game.MUST_UNDERTRUMP or winning_card.get_suit_name() != game.trump_suit)
                if must_cut and card.get_suit_name() != game.trump_suit:
                    voids[player].add(game.trump_suit)
            prefix.card_played(player, card)
            player = game.next_player(player)
    return voids


def sample_hidden_hands(game, observer, rng, betting=False):
    """Match unknown cards to hand slots without ignoring known suit voids.

    Augmenting-path matching avoids unbounded rejection sampling. Opponents'
    actual card values are never inspected; only their remaining hand sizes are.
    """
    own = {str(card) for card in game.hands[observer].cards}
    played = {str(card) for trick in game.rounds for card in trick.cards_played.values()
              if card is not None}
    face_up = str(game.trump_card) if game.trump_card is not None else None
    pool = [card for card in Deck(game.deck_size).cards if str(card) not in own | played]
    if betting and face_up is not None:
        pool = [card for card in pool if str(card) != face_up]
    voids = inferred_voids(game) if not betting else {player: set() for player in game.players}
    public_belote = game._belote_started or game.belote_status in (
        BeloteStatus.Belote_Announced, BeloteStatus.Belote_Played,
        BeloteStatus.Rebelote_Announced, BeloteStatus.Rebelote_Played)
    fixed = {}
    if not betting and face_up is not None and game.taker != observer:
        fixed[face_up] = game.taker
    if public_belote and game.player_with_belote != observer:
        suit = Card.get_suit_initial(game.trump_suit)
        fixed.update({suit + number: game.player_with_belote for number in ('12', '13')})

    slots = [player for player in game.players if player != observer
             for _ in game.hands[player].cards]
    assignment = allocate_hidden_cards(pool, slots, voids, fixed, rng)
    for player in game.players:
        if player != observer:
            game.hands[player] = Hand(None)
            game.hands[player].cards = assignment.get(player, [])
    game.deck = Deck(0)
    game.deck.cards = assignment.get(None, [])
    game.deck._size = len(game.deck.cards)
    if not betting and not public_belote:
        # The engine knows the real pair's owner before it is announced; that
        # private fact must not constrain the AI's hypothetical deals.
        game.update_belote_status()
