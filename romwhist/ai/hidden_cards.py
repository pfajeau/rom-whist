"""Constrained assignment of unknown cards to player/undealt slots."""


def allocate_hidden_cards(pool, slots, voids, fixed, rng):
    """Use randomized augmenting-path matching, with no rejection loop.

    ``None`` slots represent undealt cards. Opponents' actual hands are not an
    input: callers provide only capacities and publicly established constraints.
    """
    if len(pool) < len(slots):
        raise ValueError('Public cards and remaining hand sizes are inconsistent')
    slots = list(slots) + [None] * (len(pool) - len(slots))
    pool = list(pool)
    rng.shuffle(pool)
    rng.shuffle(slots)
    choices = [[index for index, player in enumerate(slots)
                if (str(card) not in fixed or player == fixed[str(card)])
                and (player is None or card.get_suit_name() not in voids[player])]
               for card in pool]
    assigned = {}

    def match(card_index, visited):
        for slot in choices[card_index]:
            if slot in visited:
                continue
            visited.add(slot)
            if slot not in assigned or match(assigned[slot], visited):
                assigned[slot] = card_index
                return True
        return False

    for card_index in sorted(range(len(pool)), key=lambda index: len(choices[index])):
        if not match(card_index, set()):
            raise ValueError('No hidden deal satisfies the public play history')
    hands = {}
    for slot, card_index in assigned.items():
        hands.setdefault(slots[slot], []).append(pool[card_index])
    return hands
