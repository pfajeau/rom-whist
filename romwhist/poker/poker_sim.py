"""
This module implements poker simulation functionality for Monte Carlo AI.

The simulation randomises opponents' hole cards and remaining community cards,
then evaluates who would win at showdown.  This gives a win-rate estimate for
each candidate action (fold / check / call / bet / raise) without needing to
simulate the full betting tree.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import copy
import logging

from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand
from romwhist.poker.poker_game import PokerGame
from romwhist.poker.poker_state import PokerState


class PokerSim(PokerGame):
    """
    Simulates a poker hand from a given PokerState by:
      1. Keeping the sim-player's known hole cards.
      2. Randomly dealing hole cards to all other active players from the
         remaining unseen deck.
      3. Randomly completing the community cards if the board is not yet full.
      4. Applying the ``starting_action`` for the sim player.
      5. Running out the hand with random actions for every player.
      6. Determining the winner at showdown.

    ``sim_player_won()`` returns True if the sim player is among the winners.
    ``hand_points`` carries the money won/lost so SimpleMCTSAgent can select
    the action with the highest expected value.
    """

    def __init__(self, agent, other_agent, sim_player,
                 state: PokerState = None, starting_action=None,
                 one_round_only=False):
        PokerGame.__init__(self, state.owner, id=state.game_id,
                           poker_type=state.poker_type,
                           initial_money=100)   # money irrelevant, overwritten below
        self.sim_player = sim_player
        self.starting_action = starting_action
        self.first_action = True
        self.agent = agent
        self.other_agent = other_agent

        if state is not None:
            self._init_from_state(copy.deepcopy(state))

    # ------------------------------------------------------------------
    # State restoration
    # ------------------------------------------------------------------

    def _init_from_state(self, state: PokerState):
        """Populate the game from the serialised PokerState."""
        from romwhist.player import Player

        # Rebuild player list
        self.players = []
        players_by_name = {}
        for name in state.players:
            p = Player(name)
            p.player_status = state.players_status.get(name, Player.PlayerStatus.ACTIVE)
            p.player_type = state.players_type.get(name, Player.PlayerType.HUMAN)
            self.players.append(p)
            players_by_name[name] = p

        self.poker_type = state.poker_type
        self.hole_cards_count = state.hole_cards_count
        self.small_blind = state.small_blind
        self.big_blind = state.big_blind
        self.pot = state.pot
        self.current_bet = state.current_bet
        self.initial_money = max(100, max(state.money.values(), default=100))

        # Restore money, bets
        self.money = {players_by_name[k]: v for k, v in state.money.items()
                      if k in players_by_name}
        self.bets_this_round = {players_by_name[k]: v
                                for k, v in state.bets_this_round.items()
                                if k in players_by_name}

        # Folded players
        self.folded_players = [players_by_name[n] for n in state.folded_players
                               if n in players_by_name]

        # Restore phase
        try:
            self.phase = PokerGame.GamePhase[state.phase]
        except (KeyError, TypeError):
            self.phase = PokerGame.GamePhase.PRE_FLOP

        # Restore dealer / owner
        self.dealer = players_by_name.get(state.dealer, self.players[0])
        self._CardGame__owner = players_by_name.get(state.owner, self.players[0])

        # ---- Restore sim player's known hole cards -------------------------
        self.hands = {}
        sim_player_obj = players_by_name.get(self.sim_player)
        known_hole_cards = []
        if sim_player_obj is not None:
            raw = state.hand_cards.get(self.sim_player, [])
            if raw:
                h = Hand(None, 0)
                for card_str in raw:
                    c = Card.card_from_value(card_str)
                    if c is not None:
                        h.cards.append(c)
                        known_hole_cards.append(c)
                self.hands[sim_player_obj] = h

        # ---- Restore known community cards --------------------------------
        known_community = []
        for card_str in state.community_cards:
            c = Card.card_from_value(card_str)
            if c is not None:
                known_community.append(c)

        # ---- Build a deck with all known cards removed --------------------
        deck = Deck(52)
        for c in known_hole_cards:
            deck.remove_card(c)
        for c in known_community:
            deck.remove_card(c)
        deck.shuffle()

        # ---- Deal random hole cards to other active players ---------------
        active_players = [p for p in self.players if p not in self.folded_players]
        for p in active_players:
            if p == sim_player_obj:
                continue
            h = Hand(deck, self.hole_cards_count)
            self.hands[p] = h

        # ---- Complete community cards to 5 --------------------------------
        full_community = list(known_community)
        while len(full_community) < PokerGame.BOARD_SIZE:
            card = deck.deal()
            if card is not None:
                full_community.append(card)

        comm_hand = Hand(None, 0)
        comm_hand.cards = full_community
        self._all_community_cards = comm_hand
        self.community_cards = comm_hand   # all 5 visible for evaluation

        # Initialise hand_points so SimpleMCTSAgent can read them
        self.hand_points = {p: 0 for p in self.players}

        # Record pre-sim money so we can compute profit/loss
        self._money_before = {p: self.money.get(p, 0) for p in self.players}

    # ------------------------------------------------------------------
    # Simulation entry point
    # ------------------------------------------------------------------

    def game_loop(self) -> None:
        """
        Apply starting_action for the sim player, then run random actions for
        all active players until the hand is over.
        """
        sim_player_obj = self._get_sim_player_obj()
        if sim_player_obj is None:
            return

        # Build a fresh betting queue starting from sim player
        active = self.get_active_players()
        if not active:
            self._finalise()
            return

        if sim_player_obj in active:
            idx = active.index(sim_player_obj)
            ordered = active[idx:] + active[:idx]
        else:
            ordered = active

        self._to_act = list(ordered)
        self.active_player = self._to_act[0] if self._to_act else None

        # Process actions until the betting round is done (or everyone folded)
        max_iterations = len(self.players) * 10  # safety cap
        iterations = 0
        while self.active_player is not None and iterations < max_iterations:
            player = self.active_player
            allowed = self.get_allowed_actions(player)
            if not allowed:
                break

            if player == sim_player_obj and self.first_action and self.starting_action is not None:
                action = self.starting_action
                self.first_action = False
            else:
                action = self._random_action(allowed)

            amount = 0
            if action in ('bet', 'raise'):
                amount = self.big_blind

            self.player_action(player, action, amount)
            iterations += 1

            # After everyone acted, advance phases until showdown
            if self.is_betting_round_complete():
                self.advance_phase()
                if self.phase in (PokerGame.GamePhase.SHOWDOWN,
                                  PokerGame.GamePhase.OVER):
                    break

        # If we never hit showdown (e.g. everyone folded), resolve now
        if self.phase not in (PokerGame.GamePhase.SHOWDOWN, PokerGame.GamePhase.OVER):
            self.advance_phase()

        self._finalise()

    def _finalise(self):
        """Record per-player money profit/loss into hand_points."""
        for p in self.players:
            profit = self.money.get(p, 0) - self._money_before.get(p, 0)
            self.hand_points[p] = profit

    def _random_action(self, allowed):
        """Return a random but weighted action (prefer passive play)."""
        import random
        # Bias toward passive actions to keep simulations realistic
        weights = {'fold': 2, 'check': 5, 'call': 5, 'bet': 2, 'raise': 1}
        choices = [a for a in allowed if a in weights]
        if not choices:
            return allowed[0]
        w = [weights[a] for a in choices]
        return random.choices(choices, weights=w, k=1)[0]

    def _get_sim_player_obj(self):
        for p in self.players:
            if str(p) == str(self.sim_player):
                return p
        return None

    # ------------------------------------------------------------------
    # Result helpers (used by SimpleMCTSAgent)
    # ------------------------------------------------------------------

    def sim_player_won(self):
        """Return True if the sim player is among the hand winners."""
        winners = [str(w) for w in self.hand_winners]
        return str(self.sim_player) in winners

    def run(self) -> bool:
        self.game_loop()
        return True
