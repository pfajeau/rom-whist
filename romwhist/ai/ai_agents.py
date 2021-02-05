from abc import ABC, abstractmethod
from collections import defaultdict
import configparser
import logging
import numpy as np
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue
from typing import Dict, List, Set


from romwhist.card import Card
from romwhist.game_state import GameState
from romwhist.ohell.ohell_sim import OhellSim
from romwhist.belote.belote_sim import BeloteSim


def lookup(name, namespace):
    """
    Get a method or class from any imported module from its name.
    Usage: lookup(functionName, globals())
    :returns: method/class reference
    :raises Exception: If the number of classes/methods existing in namespace with name is != 1
    """

    dots = name.count('.')
    if dots > 0:
        module_name, obj_name = '.'.join(name.split('.')[:-1]), name.split('.')[-1]
        module = __import__(module_name)
        return getattr(module, obj_name)
    else:
        modules = [obj for obj in namespace.values() if str(type(obj)) == "<type 'module'>"]
        options = [getattr(module, name) for module in modules if name in dir(module)]
        options += [obj[1] for obj in namespace.items() if obj[0] == name]
        if len(options) == 1:
            return options[0]
        if len(options) > 1:
            raise Exception('Name conflict for %s')
        raise Exception('%s not found as a method or class' % name)

class IAgent(ABC):
    """ Interface for playing agents."""

    def __init__(self, ai_player):
        self.ai_player = ai_player
        return

    @abstractmethod
    def get_action(self, state: GameState) -> Card:
        """
        Pick a action to play based on the environment and a programmed strategy.
        :param state:
        :return: The action to play.
        """
        raise NotImplementedError

    def get_bet(self, state: GameState):
        """
        Pick a bet/annouce on the environment and a programmed strategy.
        :param state:
        :return: The announce
        """
        raise NotImplementedError


class SimpleAgent(IAgent):
    """ Deterministic agent that plays according to input action."""

    def __init__(self, ai_player, action_chooser_function='random_action'):
        """
        :param str action_chooser_function: name of action to take, or a function.
            Function should map State -> Card
        :param target: See comment in IAgent's constructor
        """
        if isinstance(action_chooser_function, str):
            self.action_chooser_function = lookup(action_chooser_function, globals())
        else:
            self.action_chooser_function = action_chooser_function
        super().__init__(ai_player)


    def get_action(self, state):
        return self.action_chooser_function(state)


def random_action(state):
    """
    Picks random action.
    :param State state:
    :returns Card: action to take
    """
    logging.info("In random_action, legal actions are: %s", state.get_legal_actions())
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
        #self.evaluation_function = lookup(evaluation_function, globals())
        self.depth = depth
        super().__init__()

    def get_action(self, state):
        return NotImplementedError


class SimpleMCTSAgent(IAgent):
    """ Agent implementing simplified version of MCTS -
        only looks at end-results of simulation, without backpropogation.
        Our agent's local decision rule is decided by `action_chooser_function`, while
        the opponent's local decisions are chosen randomly."""

    def __init__(self, sim_game_class_name, ai_player, action_chooser_function='random_action',
                 num_simulations=100):
        """
        :param str action_chooser_function: See `super().__init__()` docstring
        :param int num_simulations: How many simulations for rollout
        """
        max_threads = None

        # Read nb simulation from config file
        config = configparser.ConfigParser()
        config.read('instance/config_ai.ini')
        if config.has_section('ai'):
            logging.info("ai config found")
            ai_config = config['ai']
            if config.has_option('ai', 'number_of_simulations'):
                num_simulations = int(ai_config['number_of_simulations'])
                logging.info("Number of simulations: %s", num_simulations)

            if config.has_option('ai', 'max_thread_number_for_simulation'):
                max_threads = int(ai_config['max_thread_number_for_simulation'])

        self.action_chooser_function = lookup(action_chooser_function,
                                              globals())
        self.num_simulations_total = 0
        self.action_value = dict()
        self.num_simulations_per_action = dict()  # Number of simulations for an action
        self.num_simulations = num_simulations
        self.executor = ThreadPoolExecutor(max_workers=max_threads)
        self.sim_game_class_name = sim_game_class_name
        self.action_points = dict()
        super().__init__(ai_player)

    def reset_data(self):
        self.action_value = dict()
        self.num_simulations_per_action = dict()
        self.action_points = dict()

    def get_action(self, state):
        action = self.rollout(state, self.num_simulations)
        return action

    def get_bet(self, state):
        action = self.rollout2(state, self.num_simulations)
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
        logging.info("Legal actions: %s", legal_actions)
        self.reset_data()

        # If only one choice, return it right away
        if len(legal_actions) == 1:
            return legal_actions[0]

        for action in legal_actions:
            self.action_value[action] = 0
            self.action_points[action] = 0
            self.num_simulations_per_action[action] = 0

        rollout_actions = np.random.choice(legal_actions,  # Pre-select initial actions
                                           size=num_simulations, replace=True)
        best_action = np.random.choice(legal_actions)

        # Simulate games on separate threads
        games = []
        for action in rollout_actions:
            self.num_simulations_per_action[action] += 1
            sim_game_class = globals()[self.sim_game_class_name]
            games.append(sim_game_class(SimpleAgent(self.action_chooser_function),
                                         SimpleAgent(random_action), self.ai_player,
                                         state, action))
        # games = [SimulatedGame(SimpleAgent(self.action_chooser_function),
        #                        SimpleAgent(random_action), False,
        #                        state, action) for action in rollout_actions]
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
            if game.sim_player_won():
                self.action_value[game.starting_action] += 1
            self.action_points[game.starting_action] += game.hand_points[self.ai_player]
            self.num_simulations_total += 1

        logging.info("action_value: %s", self.action_value)

        # Choose best action
        for action in legal_actions:
            logging.info("action: %s, action has value %s", action, self.action_value[action])
            logging.info("action: %s, action has points %s", action, self.action_points[action])
            best_action = action if self.action_value[action] > self.action_value[best_action] \
                else best_action

        return best_action


    def rollout2(self, state, num_simulations):
        """
        Performs `num_simulations` rollouts - i.e. stochastically simulate `num_simlations` games.

        :param State state: Current state of the game
        :param int num_simulations: How many games to simulate. Our agent's choices are made according to `action_chooser_function`
            while the opoonent's are chosen randomly.
        :returns Card: Best action
        """

        legal_actions = state.get_legal_bets()
        logging.info("Legal actions: %s", legal_actions)
        self.reset_data()

        for action in legal_actions:
            self.action_value[action] = 0
            self.num_simulations_per_action[action] = 0
            self.action_points[action] = 0

        rollout_actions = np.random.choice(legal_actions,  # Pre-select initial actions
                                           size=num_simulations, replace=True)
        best_action = np.random.choice(legal_actions)

        # Simulate games on separate threads
        games = []
        for action in rollout_actions:
            self.num_simulations_per_action[action] += 1
            state.bets[self.ai_player] = action
            state.active_player = state.next_player(state.dealer)
            sim_game_class = globals()[self.sim_game_class_name]
            games.append(sim_game_class(SimpleAgent(self.action_chooser_function),
                                         SimpleAgent(random_action), self.ai_player,
                                         state, None))

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

        logging.info("action value before popualating: %s", self.action_value)
        # Collect results
        for game in games:
            if game.sim_player_won():
                self.action_value[game.bets[self.ai_player]] += 1
            self.action_points[game.bets[self.ai_player]] += game.hand_points[self.ai_player]

            self.num_simulations_total += 1

        logging.info("action_value: %s", self.action_value)
        logging.info("action_points: %s", self.action_points)

        # Choose best action
        for action in legal_actions:
            logging.info("bet: %s, bet has value %s", action, self.action_value[action])
            logging.info("action: %s, action has points %s", action, self.action_points[action])
            best_action = action if self.action_value[action] > self.action_value[best_action] \
                else best_action

        return best_action
