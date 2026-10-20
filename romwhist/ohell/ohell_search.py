"""Monte Carlo choices evaluated by this variant's exact-bid scoring."""

import copy
import logging
import random

from romwhist.ai.ai_agents import SimpleMCTSAgent
from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_sim import OhellSim
from romwhist.ohell.ohell_strategy import WhistTacticalAgent


class WhistSearchAgent(SimpleMCTSAgent):
    def _best(self, actions):
        candidates = [action for action in actions if self.num_simulations_per_action.get(action, 0)]
        if not candidates:
            raise ValueError('No evaluated Whist action')
        self.best_action = max(candidates, key=lambda action: (
            self.action_points[action] / self.num_simulations_per_action[action],
            self.action_value[action] / self.num_simulations_per_action[action]))
        return self.best_action

    def _run(self, state, actions, bidding=False):
        self.reset_data()
        if not actions:
            raise ValueError('No legal Whist action')
        for action in actions:
            self.action_value[action] = 0
            self.action_points[action] = 0
            self.num_simulations_per_action[action] = 0
        samples = max(self.num_simulations,
                      (self.min_num_simulations + len(actions) - 1) // len(actions))
        jobs = []
        for _ in range(samples):
            seed = random.getrandbits(64)
            for action in actions:
                observation = copy.deepcopy(state)
                if bidding:
                    observation.bets[self.ai_player] = int(action)
                    observation.phase = OhellGame.GamePhase.BET
                    observation.active_player = observation.next_player(observation.dealer)
                sim = OhellSim(WhistTacticalAgent(), WhistTacticalAgent(), self.ai_player,
                               observation, None if bidding else action, seed=seed)
                jobs.append((action, sim))

        def simulate(job):
            action, sim = job
            sim.run()
            return action, sim.evaluation_score, sim.sim_player_won()

        for action, value, exact in self.executor.map(simulate, jobs):
            self.action_points[action] += value
            self.action_value[action] += int(exact)
            self.num_simulations_per_action[action] += 1
            self.num_simulations_total += 1
        # A legal card/bid is needed even when no option reaches the old
        # win-percentage threshold. Negative expectations remain comparable.
        return self._best(actions)

    def get_action(self, state):
        try:
            return self._run(state, state.allowed_cards)
        except ValueError:
            logging.exception('Inconsistent Whist evidence; using tactical fallback')
            return WhistTacticalAgent().get_action(state)

    def get_bet(self, state):
        actions = [str(int(bid)) for bid in state.allowed_bets]
        if not actions:
            raise ValueError('No legal Whist bid')
        try:
            return self._run(state, actions, bidding=True)
        except ValueError:
            logging.exception('Inconsistent Whist bidding evidence; using bid estimate')
            observation = copy.deepcopy(state)
            observation.active_player = self.ai_player
            game = OhellGame(state.owner)
            game.populate_from_state(observation)
            return str(WhistTacticalAgent().estimate_bid(game, self.ai_player,
                                                       [int(action) for action in actions]))
