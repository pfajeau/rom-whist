"""Regression coverage for timestamped snapshots sent to AI services."""
import json
import unittest

from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.belote.belote_state import BeloteState
from romwhist.contree.contree_ai import ContreeAiPlayer
from romwhist.contree.contree_state import ContreeState
from romwhist.ohell.ohell_ai import OhellAiPlayer
from romwhist.ohell.ohell_state import OhellState
from romwhist.player import Player
from romwhist.poker.poker_ai import PokerAiPlayer
from romwhist.poker.poker_state import PokerState


class StateSnapshotTests(unittest.TestCase):
    def test_ai_snapshot_round_trip_preserves_timestamp(self):
        for state_type, ai_type in [
            (OhellState, OhellAiPlayer),
            (BeloteState, BeloteAiPlayer),
            (ContreeState, ContreeAiPlayer),
            (PokerState, PokerAiPlayer),
        ]:
            with self.subTest(game=state_type.__name__):
                state = state_type('286')
                # Game.get_state adds the timestamp before sending the snapshot.
                state.timestamp = 1791497687.394284
                restored = ai_type.get_game_state_from_json(state.to_json())
                self.assertEqual(json.loads(restored.to_json()), json.loads(state.to_json()))

    def test_whist_ai_bets_and_plays_with_timestamped_snapshot(self):
        players = ['joe', 'ai286_1', 'ai286_2', 'ai286_3']
        state = OhellState(
            '286', players=players, trump='heart', deck_size=32,
            hand_cards=dict(zip(players, [['h14'], ['c14'], ['s9'], ['c12']])),
            active_player='ai286_1', dealer='ai286_3', owner='joe',
            allowed_cards=['c14'], allowed_bets=[0, 1],
            bets=dict(zip(players, [1, -1, -1, -1])),
            scores=dict.fromkeys(players, 0),
            nb_rounds_won=dict.fromkeys(players, 0),
            cards_played_per_player={player: [] for player in players},
            cards_played_per_round={'0': dict.fromkeys(players, 'None')},
            players_status=dict.fromkeys(players, 'Active'),
            players_type=dict(zip(players, ['Human', 'AI', 'AI', 'AI'])),
            trump_card='h8', phase='Bet', timestamp=1791497687.394284,
        )
        ai = OhellAiPlayer(Player('ai286_1'), '286')
        self.assertIn(ai.player_to_bet([0, 1], state.to_json()), [0, 1])
        self.assertEqual(ai.player_to_play(['c14'], state.to_json()), 'c14')


if __name__ == '__main__':
    unittest.main()
