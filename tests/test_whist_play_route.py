"""Regression checks for server handling of Whist AI card plays."""
import unittest
from unittest.mock import MagicMock, patch

from romwhist.ohell import ohell_routes
from romwhist.player import Player


class WhistPlayRouteTests(unittest.TestCase):
    def setUp(self):
        self.player = Player('ai470_1')
        self.next_player = Player('ai470_2')
        self.game = MagicMock()
        self.game.get_player_by_name.return_value = self.player
        self.game.get_active_player.side_effect = [self.player, self.next_player]
        self.game.get_allowed_cards.side_effect = [['h11'], ['s9']]
        self.game.play_card.return_value = None

    def test_ai_play_advances_turn_and_notifies_players(self):
        with patch.dict(ohell_routes.games, {'470': self.game}), patch.object(
            ohell_routes.common_routes, 'emit_to_players'
        ) as emit:
            ohell_routes.player_played_ai(
                {'game_id': '470', 'player': 'ai470_1', 'card': 'h11'}
            )
        self.game.get_player_by_name.assert_called_once_with('ai470_1')
        self.game.play_card.assert_called_once_with(self.player, 'h11')
        self.assertEqual([call.args[0] for call in emit.call_args_list],
                         ['card played', 'player to play'])
        self.assertEqual(emit.call_args_list[1].args[1]['player'], self.next_player)

    def test_play_out_of_turn_is_rejected(self):
        self.game.get_active_player.side_effect = None
        self.game.get_active_player.return_value = self.next_player
        with patch.dict(ohell_routes.games, {'470': self.game}):
            result = ohell_routes.player_played_process('470', 'ai470_1', 'h11')
        self.assertEqual(result, {'ok': False, 'error': 'not_your_turn'})
        self.game.play_card.assert_not_called()

    def test_illegal_card_is_rejected(self):
        with patch.dict(ohell_routes.games, {'470': self.game}):
            result = ohell_routes.player_played_process('470', 'ai470_1', 'c14')
        self.assertEqual(result, {'ok': False, 'error': 'illegal_card'})
        self.game.play_card.assert_not_called()
