"""Bounded Monte Carlo search for Belote and Contrée."""

import copy
import logging
import random

from romwhist.ai.ai_agents import SimpleMCTSAgent
from romwhist.belote.belote_sim import BeloteSim
from romwhist.belote.belote_tactics import TacticalAgent
from romwhist.contree.contree_sim import ContreeSim


class BeloteSearchAgent(SimpleMCTSAgent):
    # Full-hand evaluation is affordable once at most three cards remain each.
    endgame_cards = 3

    def _best(self, actions, bidding=False):
        candidates = [action for action in actions if self.num_simulations_per_action.get(action, 0)]
        if bidding:
            candidates = [action for action in candidates if action == 'pass_0' or
                          self.action_value[action] / self.num_simulations_per_action[action] >= self.win_threshold]
        if not candidates:
            return None
        # Do not reject card choices because the position is unfavorable.
        self.best_action = max(candidates, key=lambda action:
                               self.action_points[action] / self.num_simulations_per_action[action])
        return self.best_action

    def _run(self, state, actions, bidding):
        self.reset_data()
        for action in actions:
            self.action_value[action] = 0
            self.action_points[action] = 0
            self.num_simulations_per_action[action] = 0
        if not actions:
            return None
        contree = self.sim_game_class_name == 'ContreeSim'
        sim_type = ContreeSim if contree else BeloteSim
        groups = {}
        for action in actions:
            # Numeric bids in the same suit share card play. Evaluate every
            # legal contract against those results instead of replaying it.
            group = action.split('_')[0] if bidding and contree else action
            groups.setdefault(group, []).append(action)
        samples = max(self.num_simulations, (self.min_num_simulations + len(actions) - 1) // len(actions))
        seeds = [random.getrandbits(64) for _ in range(samples)]
        full_hand = bidding or max(map(len, state.hand_cards.values()), default=0) <= self.endgame_cards
        jobs = []
        for seed in seeds:
            for candidates in groups.values():
                action = candidates[0]
                if bidding and action == 'pass_0' and state.current_bet in (None, 'None', 'pass_0'):
                    self.num_simulations_per_action[action] += 1
                    continue
                observation = copy.deepcopy(state)
                if bidding:
                    observation.bets[self.ai_player] = action
                sim = sim_type(TacticalAgent(), TacticalAgent(), self.ai_player,
                               observation, None if bidding else action,
                               one_round_only=not full_hand, seed=seed)
                jobs.append((sim, candidates))

        def simulate(job):
            sim, candidates = job
            sim.run()
            results = []
            for action in candidates:
                if bidding and contree:
                    value, won = sim.evaluate_contract(action)
                else:
                    value, won = sim.evaluation_score, sim.sim_player_won()
                results.append((action, value, won))
            return results

        for results in self.executor.map(simulate, jobs):
            for action, value, won in results:
                self.action_points[action] += value
                self.action_value[action] += int(won)
                self.num_simulations_per_action[action] += 1
                self.num_simulations_total += 1
        return self._best(actions, bidding=bidding)

    def get_action(self, state):
        try:
            action = self._run(state, state.get_legal_actions(), bidding=False)
            return action if action is not None else TacticalAgent().get_action(state)
        except ValueError:
            logging.exception('Inconsistent rollout evidence; using a legal tactical move')
            return TacticalAgent().get_action(state)

    def get_bet(self, state):
        try:
            actions = state.get_legal_bets()
            if self.sim_game_class_name == 'BeloteSim':
                actions = [action for action in actions if action.casefold() != 'pass']
            return self._run(state, actions, bidding=True)
        except ValueError:
            logging.exception('Inconsistent bidding evidence; passing')
            return 'pass_0' if self.sim_game_class_name == 'ContreeSim' else None
