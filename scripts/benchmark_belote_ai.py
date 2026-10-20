"""Compare this AI with a baseline checkout on identical deals, swapping teams.

Example: venv/bin/python scripts/benchmark_belote_ai.py --baseline /tmp/baseline --deals 40
The baseline directory must contain its own romwhist package and instance config.
This measures card play with a fixed contract, not bidding strength.
"""

import argparse
import inspect
import json
import logging
import os
from pathlib import Path
import random
import subprocess
import sys
import time

if '--worker' not in sys.argv:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote_status import BeloteStatus
from romwhist.card import Card
from romwhist.player import Player


def player(name, samples):
    ai = BeloteAiPlayer(Player(name), 'benchmark')
    ai._agent.num_simulations = samples
    ai._agent.min_num_simulations = samples
    return ai


def worker(samples):
    agents = {}
    fields = inspect.signature(BeloteState).parameters
    for line in sys.stdin:
        request = json.loads(line)
        random.seed(request['seed'])
        np.random.seed(request['seed'] % (2 ** 32))
        state = BeloteState(**{key: value for key, value in request['state'].items() if key in fields})
        name = state.active_player
        if name not in agents:
            agents[name] = player(name, samples)
        started = time.perf_counter()
        card = agents[name].player_to_play_from_state(state)
        response = {'card': str(card), 'seconds': time.perf_counter() - started}
        print('AI_BENCH:' + json.dumps(response), flush=True)


def announce(game, name, card):
    suit = Card.get_suit_initial(game.trump_suit)
    if name == game.player_with_belote and card in (suit + '12', suit + '13'):
        if game.belote_status == BeloteStatus.Allowed:
            game.player_announced_belote(name, game.BeloteAnnounced.BELOTE)
        elif game.belote_status == BeloteStatus.Belote_Played:
            game.player_announced_belote(name, game.BeloteAnnounced.REBELOTE)


def compare(baseline, deals, samples, first_seed):
    env = dict(os.environ, PYTHONPATH=str(Path(baseline).resolve()))
    command = [sys.executable, str(Path(__file__).resolve()), '--worker', '--samples', str(samples)]
    process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               text=True, bufsize=1)
    agents = {name: player(name, samples) for name in 'ABCD'}
    margins, wins, timings = [], 0, {'current': [], 'baseline': []}
    try:
        for seed in range(first_seed, first_seed + deals):
            for swap in range(2):
                random.seed(seed)
                game = BeloteGame('A', id='benchmark')
                for name in 'ABCD':
                    game.add_player(Player(name))
                game.start_game()
                game.deal(dealer=game.players[-1])
                game.place_bet(game.players[0], Card.SUIT_NAMES[seed % 4])
                game.deal_2()
                game.create_round()
                turn = 0
                current_team = 'AC' if swap == 0 else 'BD'
                while not game.is_hand_completed():
                    name = str(game.active_player)
                    state = game.get_state()
                    decision_seed = seed * 100 + turn
                    if name in current_team:
                        random.seed(decision_seed)
                        np.random.seed(decision_seed % (2 ** 32))
                        started = time.perf_counter()
                        card = agents[name].player_to_play_from_state(state)
                        timings['current'].append(time.perf_counter() - started)
                    else:
                        process.stdin.write(json.dumps({'seed': decision_seed,
                                                        'state': json.loads(state.to_json())}) + '\n')
                        process.stdin.flush()
                        while True:
                            response = process.stdout.readline()
                            if not response:
                                raise RuntimeError('Baseline AI worker exited')
                            if response.startswith('AI_BENCH:'):
                                response = json.loads(response[len('AI_BENCH:'):])
                                break
                        card = response['card']
                        timings['baseline'].append(response['seconds'])
                    if card not in game.get_allowed_cards(game.active_player):
                        raise AssertionError(f'Illegal benchmark move: {name}: {card}')
                    announce(game, name, card)
                    winner = game.play_card(game.active_player, card)
                    if winner is not None and not game.is_hand_completed():
                        game.create_round()
                    turn += 1
                game.hand_completed()
                margin = game.scores[current_team[0]] - game.scores['B' if swap == 0 else 'A']
                margins.append(margin)
                wins += int(margin > 0)
            print(f'Completed {seed - first_seed + 1}/{deals} paired deals', file=sys.stderr, flush=True)
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
        for ai in agents.values():
            ai._agent.executor.shutdown()
            ai._agent2.executor.shutdown()
    return {'paired_deals': deals, 'hands': len(margins), 'samples_per_action': samples,
            'first_seed': first_seed, 'current_wins': wins,
            'ties': sum(margin == 0 for margin in margins),
            'mean_score_margin': sum(margins) / len(margins),
            'mean_decision_ms': {key: round(sum(values) / len(values) * 1000, 2)
                                 for key, values in timings.items()},
            'p95_decision_ms': {key: round(float(np.percentile(values, 95)) * 1000, 2)
                                for key, values in timings.items()},
            'margins': margins}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline')
    parser.add_argument('--deals', type=int, default=20)
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--first-seed', type=int, default=0)
    parser.add_argument('--output')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    if args.worker:
        worker(args.samples)
    else:
        if not args.baseline or args.deals <= 0 or args.samples <= 0:
            parser.error('Provide --baseline and positive --deals/--samples')
        result = compare(args.baseline, args.deals, args.samples, args.first_seed)
        print(json.dumps(result, indent=2))
        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
