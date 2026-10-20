"""Compare complete Whist bidding/card play on paired, seat-swapped deals.

venv/bin/python scripts/benchmark_whist_ai.py --baseline /tmp/baseline --deals 20
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
from romwhist.game import CardGame
from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_ai import OhellAiPlayer
from romwhist.ohell.ohell_state import OhellState
from romwhist.player import Player


def player(name, samples):
    ai = OhellAiPlayer(Player(name), 'benchmark')
    for agent in (ai._OhellAiPlayer__agent, ai._OhellAiPlayer__agent2):
        agent.num_simulations = agent.min_num_simulations = samples
    return ai


def decide(ai, state):
    started = time.perf_counter()
    if state.phase == 'Bet':
        action = ai.player_to_bet(state.allowed_bets, state.to_json())
    else:
        action = ai.player_to_play(state.allowed_cards, state.to_json())
    return {'action': action, 'seconds': time.perf_counter() - started}


def worker(samples):
    agents = {}
    fields = inspect.signature(OhellState).parameters
    for line in sys.stdin:
        request = json.loads(line)
        random.seed(request['seed'])
        np.random.seed(request['seed'] % (2 ** 32))
        state = OhellState(**{key: value for key, value in request['state'].items() if key in fields})
        name = state.active_player
        if name not in agents:
            agents[name] = player(name, samples)
        print('AI_BENCH:' + json.dumps(decide(agents[name], state)), flush=True)


def compare(baseline, deals, samples, first_seed):
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), '--worker', '--samples', str(samples)],
        env=dict(os.environ, PYTHONPATH=str(Path(baseline).resolve())),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    agents = {name: player(name, samples) for name in 'ABCD'}
    totals = {key: {'score': 0, 'exact': 0, 'player_hands': 0, 'seconds': []}
              for key in ('current', 'baseline')}
    margins = []
    try:
        for seed in range(first_seed, first_seed + deals):
            cards = (1, 3, 5, 7, 8)[seed % 5]
            for swap in range(2):
                random.seed(seed)
                game = OhellGame('A', id='benchmark')
                for name in 'ABCD':
                    game.add_player(Player(name))
                game.dealing_method = CardGame.MANUAL_DEALING
                game.start_game()
                game.deal(nb_cards=cards, with_trump=seed % 2 == 0 and cards < 8,
                          dealer=game.players[seed % 4])
                current = 'AC' if swap == 0 else 'BD'
                turn = 0
                while game.phase == game.GamePhase.BET or not game.is_hand_completed():
                    state = game.get_state()
                    name = str(game.active_player)
                    decision_seed = seed * 1000 + turn
                    label = 'current' if name in current else 'baseline'
                    if label == 'current':
                        random.seed(decision_seed)
                        np.random.seed(decision_seed % (2 ** 32))
                        response = decide(agents[name], state)
                    else:
                        process.stdin.write(json.dumps({'seed': decision_seed,
                                                        'state': json.loads(state.to_json())}) + '\n')
                        process.stdin.flush()
                        while True:
                            line = process.stdout.readline()
                            if not line:
                                raise RuntimeError('Baseline Whist worker exited')
                            if line.startswith('AI_BENCH:'):
                                response = json.loads(line[len('AI_BENCH:'):])
                                break
                    totals[label]['seconds'].append(response['seconds'])
                    if game.phase == game.GamePhase.BET:
                        bid = int(response['action'])
                        if bid not in state.allowed_bets:
                            raise AssertionError(f'Illegal bid: {bid}')
                        game.place_bet(game.active_player, bid)
                        if game.phase == game.GamePhase.PLAY:
                            game.active_player = game.next_player(game.dealer)
                            game.create_round()
                    else:
                        card = response['action']
                        if card not in state.allowed_cards:
                            raise AssertionError(f'Illegal card: {card}')
                        winner = game.play_card(game.active_player, card)
                        if winner is not None and not game.is_hand_completed():
                            game.create_round()
                    turn += 1
                game.hand_completed()
                score_difference = 0
                for name in 'ABCD':
                    label = 'current' if name in current else 'baseline'
                    totals[label]['score'] += game.hand_points[name]
                    totals[label]['exact'] += int(game.bets[name] == game.wins[name])
                    totals[label]['player_hands'] += 1
                    score_difference += game.hand_points[name] * (1 if label == 'current' else -1)
                margins.append(score_difference / 2)
            print(f'Completed {seed - first_seed + 1}/{deals} paired deals', file=sys.stderr, flush=True)
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
        for ai in agents.values():
            ai._OhellAiPlayer__agent.executor.shutdown()
            ai._OhellAiPlayer__agent2.executor.shutdown()
    return {'paired_deals': deals, 'hands': deals * 2, 'first_seed': first_seed,
            'samples_per_action': samples, 'mean_score_advantage_per_player': sum(margins) / len(margins),
            'results': {key: {'mean_score': stats['score'] / stats['player_hands'],
                              'exact_bids': stats['exact'], 'player_hands': stats['player_hands'],
                              'mean_decision_ms': round(sum(stats['seconds']) / len(stats['seconds']) * 1000, 2),
                              'p95_decision_ms': round(float(np.percentile(stats['seconds'], 95)) * 1000, 2)}
                        for key, stats in totals.items()}}


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
