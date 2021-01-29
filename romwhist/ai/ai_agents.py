from abc import ABC, abstractmethod
import numpy as np
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue
from typing import Dict, List, Set


from romwhist.card import Card
from romwhist.game_state import GameState

class IAgent(ABC):
    """ Interface for bridge-playing agents."""

    @abstractmethod
    def __init__(self):
        return

    @abstractmethod
    def get_action(self, state: GameState) -> Card:
        """
        Pick a action to play based on the environment and a programmed strategy.
        :param state:
        :return: The action to play.
        """
        raise NotImplementedError

class SimpleAgent(IAgent):
    """ Deterministic agent that plays according to input action."""

    def __init__(self, action_chooser_function='random_action'):
        """
        :param str action_chooser_function: name of action to take, or a function.
            Function should map State -> Card
        :param target: See comment in IAgent's constructor
        """

        self.action_chooser_function = action_chooser_function
        super().__init__()

    def get_action(self, state):
        return self.action_chooser_function(state)


def random_action(state):
    """
    Picks random action.
    :param State state:
    :returns Card: action to take
    """
    return np.random.choice(state.get_legal_actions())

class SmartSearchAgent(IAgent):

    """Abstract agent implementing IAgent that searches a game tree"""

    def __init__(self, evaluation_function='score_evaluation_function',
                 depth=-1):
        """
        :param evaluation_function: function mapping (State, *args) -> Card ,
            where *args is determined by the agent itself.
        :param int depth: -1 for full tree, any other number > 1 for depth bounded tree
        :param target:
        """
        self.evaluation_function = lookup(evaluation_function, globals())
        self.depth = depth
        super().__init__()

    def get_action(self, state):
        return NotImplementedError

class SimpleMCTSAgent(IAgent):
    """ Agent implementing simplified version of MCTS -
        only looks at end-results of simulation, without backpropogation.
        Our agent's local decision rule is decided by `action_chooser_function`, while
        the opponent's local decisions are chosen randomly."""

    def __init__(self, action_chooser_function='random_action', num_simulations=100):
        """
        :param str action_chooser_function: See `super().__init__()` docstring
        :param int num_simulations: How many simulations for rollout
        """

        self.action_chooser_function = lookup(action_chooser_function,
                                              globals())
        self.num_simulations_total = 0
        self.action_value = defaultdict(lambda: 0)  # type: Dict[Card, int]  # Maps values of playable actions
        self.num_simulations = num_simulations
        self.executor = ThreadPoolExecutor()
        super().__init__(None)

    def get_action(self, state):
        action = self.rollout(state, self.num_simulations)
        return action

    def rollout(self, state, num_simulations):
        """
        Performs `num_simulations` rollouts - i.e. stochastically simulate `num_simlations` games.

        :param State state: Current state of the game
        :param int num_simulations: How many games to simulate. Our agent's choices are made according to `action_chooser_function`
            while the opoonent's are chosen randomly.
        :returns Card: Best action
        """

        legal_actions = state.get_legal_actions()
        rollout_actions = np.random.choice(legal_actions,  # Pre-select initial actions
                                           size=num_simulations, replace=True)
        best_action = np.random.choice(legal_actions)

        # Simulate games on separate threads
        games = [SimulatedGame(SimpleAgent(self.action_chooser_function),
                               SimpleAgent('random_action'), False,
                               state, action) for action in rollout_actions]
        futures = [self.executor.submit(game.run) for game in games]
        futures_queue = Queue(num_simulations)
        for future in futures:
            futures_queue.put(future)

        # Poll threads for termination. Each future's return value is a boolean.
        while not futures_queue.empty():
            future = futures_queue.get()
            futures_queue.task_done()
            if future.running():
                futures_queue.put(future)
            else:
                assert future.result()

        # Collect results
        for game in games:
            assert game.winning_team != -1
            winning_team = game.teams[game.winning_team]
            if winning_team.has_player(state.curr_player):
                self.action_value[game.starting_action] += 1

            self.num_simulations_total += 1

        # Choose best action
        for action in legal_actions:
            best_action = action if self.action_value[action] > self.action_value[best_action] \
                else best_action

        return best_action
