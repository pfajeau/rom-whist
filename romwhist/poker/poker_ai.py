"""
This module implements poker AI player functionality.

The AI uses Monte Carlo simulation to estimate its win probability (equity)
for the current hand, then maps that equity — together with pot odds — to the
most sensible betting action (fold / check / call / bet / raise).

Monte Carlo is the right algorithm here: it is the same technique used by
professional equity calculators (PokerStove, Equilab).  For each candidate
action the agent runs N simulated showdowns with randomised opponent hole
cards and random remaining community cards; the action with the best
win-rate is selected.  The approach generalises to both Texas Hold'em and
Omaha because hand evaluation is delegated to PokerGame.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import json
import logging

from romwhist.ai.ai_agents import SimpleMCTSAgent
from romwhist.ai.ai_player import AiPlayer
from romwhist.poker.poker_state import PokerState


class PokerAiPlayer(AiPlayer):
    """AI player for poker games.

    Decision flow
    -------------
    1. Deserialise the game state into a ``PokerState``.
    2. Run ``SimpleMCTSAgent`` which calls ``PokerSim`` for every candidate
       action to estimate win-rate per action.
    3. Compute pot odds for the current situation.
    4. Apply a pot-odds filter on top of the raw win-rate to decide the
       final action and (for bet/raise) the bet amount.
    """

    def __init__(self, player, game_id):
        AiPlayer.__init__(self, player, game_id)
        self._agent = SimpleMCTSAgent(
            'PokerSim', self.player,
            action_chooser_function='random_action',
            num_simulations=50,
        )
        self.game_state = PokerState(game_id, sim_player=self.player.name)

    # ------------------------------------------------------------------
    # AiPlayer interface
    # ------------------------------------------------------------------

    def player_to_act(self, allowed_actions, game_state_json):
        """Called when it is this player's turn to act."""
        logging.debug("Poker AI player_to_act: %s", self.player.name)
        game_state = PokerState(**json.loads(game_state_json))
        game_state.sim_player = self.player.name
        game_state.allowed_actions = allowed_actions
        self.game_state = game_state
        return self._choose_action(game_state)

    # Keep compatibility with the generic AiPlayer.player_to_bet name used in
    # ai.py so the poker AI can be dispatched via the same code path.
    def player_to_bet(self, allowed_actions, game_state_json):
        return self.player_to_act(allowed_actions, game_state_json)

    @staticmethod
    def get_game_state_from_json(state_as_json):
        return PokerState(**json.loads(state_as_json))

    def set_game_state_from_json(self, state_as_json):
        self.game_state = self.get_game_state_from_json(state_as_json)

    # ------------------------------------------------------------------
    # Core decision logic
    # ------------------------------------------------------------------

    def _choose_action(self, state: PokerState) -> dict:
        """Return {'action': str, 'amount': int}."""
        allowed = state.get_legal_actions()

        if not allowed:
            return {'action': 'fold', 'amount': 0}

        if len(allowed) == 1:
            return self._action_response(allowed[0], state)

        # Run Monte Carlo simulations
        best_action = self._agent.get_action(state)

        if best_action is None:
            # Fallback: prefer check > call > fold
            for preferred in ('check', 'call', 'fold'):
                if preferred in allowed:
                    return self._action_response(preferred, state)
            return self._action_response(allowed[0], state)

        # Compute raw win-rate for the best action
        n_sims = self._agent.num_simulations_per_action.get(best_action, 0)
        n_wins = self._agent.action_value.get(best_action, 0)
        win_rate = n_wins / n_sims if n_sims > 0 else 0.0

        # Pot-odds adjustment
        # If calling would cost more than the implied odds justify, downgrade.
        best_action = self._apply_pot_odds(best_action, win_rate, state, allowed)

        logging.info(
            "Poker AI %s: best_action=%s win_rate=%.2f",
            self.player.name, best_action, win_rate,
        )
        return self._action_response(best_action, state)

    def _apply_pot_odds(self, action, win_rate, state: PokerState, allowed):
        """Downgrade aggressive actions when equity does not justify them."""
        player_name = self.player.name
        player_bet_so_far = state.bets_this_round.get(player_name, 0)
        to_call = max(0, state.current_bet - player_bet_so_far)
        pot = state.pot

        # Pot odds: the fraction of the final pot we must invest to call.
        if to_call > 0 and (pot + to_call) > 0:
            pot_odds = to_call / (pot + to_call)
        else:
            pot_odds = 0.0

        # Very strong hand → bet / raise aggressively
        if win_rate >= 0.65:
            if 'raise' in allowed:
                return 'raise'
            if 'bet' in allowed:
                return 'bet'
            if 'call' in allowed:
                return 'call'
            return 'check' if 'check' in allowed else action

        # Decent equity and positive expected value → call / check
        if win_rate >= pot_odds and win_rate >= 0.35:
            if 'check' in allowed:
                return 'check'
            if 'call' in allowed:
                return 'call'
            return action

        # Weak hand: give up if we have to pay, otherwise check
        if 'check' in allowed:
            return 'check'
        if 'fold' in allowed:
            return 'fold'

        return action

    def _action_response(self, action, state: PokerState) -> dict:
        """Return a response dict with action and bet amount."""
        amount = 0
        if action in ('bet', 'raise'):
            # Size the bet at pot-size for value, half-pot otherwise
            amount = max(state.big_blind, state.pot // 2)
        return {'action': action, 'amount': amount}
