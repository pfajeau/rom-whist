import copy
import logging
from enum import Enum
from flask_babel import gettext as _

from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand
from romwhist.game import CardGame
from romwhist.player import Player
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote_status import BeloteStatus


class BeloteGame(CardGame):
    TOTAL_POINTS = 162
    MAX_PLAYERS = 4

    class GamePhase(str, Enum):
        DEAL = "Deal"
        DEAL2 = "Deal2"
        BET = "Bet"
        BET2 = "Bet2"
        PLAY = "Play"
        OVER = "Over"

    class BeloteAnnounced(str, Enum):
        BELOTE = "belote"
        REBELOTE = "rebelote"

    def __init__(self, game_creator=None, id=0):
        CardGame.__init__(self, game_creator=game_creator, deck_size=0, id=id)
        self.taker = None
        self.teams = []
        # self.__belote_announced = BeloteGame.BeloteAnnounced.No
        self.__belote_status = BeloteStatus.Not_Allowed
        self.__player_with_belote = None
        self.__bonus_litige = 0
        self.__win_game_points = 1000
        self.init_dict(self.hand_points, 0)
        self._hand_winner = []
        self.deck = None
        self._nb_pass_since_bet = 0

        self.reset_card_ranks_and_points()

        # Number of cards to deal depending on number of players
        self.nb_cards_first_deal = {1: 6, 2: 6, 3: 6, 4: 5}
        self.nb_cards_second_deal = {1: 3, 2: 3, 3: 3, 4: 3}

        # Total number of points
        self.TOTAL_POINTS = BeloteGame.TOTAL_POINTS
        self.BONUS_CAPOT = 100
        self.DIX_DE_DER = 10
        self.BELOTE_REBELOTE = 20

    def reset_card_ranks_and_points(self):
        # Points and ranks will change for the trump suit once it is known
        self.card_points = {"c7": 0, "c8": 0, "c9": 0, "c10": 10, "c11": 2, "c12": 3, "c13": 4, "c14": 11,
                            "d7": 0, "d8": 0, "d9": 0, "d10": 10, "d11": 2, "d12": 3, "d13": 4, "d14": 11,
                            "h7": 0, "h8": 0, "h9": 0, "h10": 10, "h11": 2, "h12": 3, "h13": 4, "h14": 11,
                            "s7": 0, "s8": 0, "s9": 0, "s10": 10, "s11": 2, "s12": 3, "s13": 4, "s14": 11}

        self.card_ranks = {"c7": 7, "c8": 8, "c9": 9, "c10": 13, "c11": 10, "c12": 11, "c13": 12, "c14": 14,
                           "d7": 7, "d8": 8, "d9": 9, "d10": 13, "d11": 10, "d12": 11, "d13": 12, "d14": 14,
                           "h7": 7, "h8": 8, "h9": 9, "h10": 13, "h11": 10, "h12": 11, "h13": 12, "h14": 14,
                           "s7": 7, "s8": 8, "s9": 9, "s10": 13, "s11": 10, "s12": 11, "s13": 12, "s14": 14}

        self.ranks_trump = {7: 7, 8: 8, 9: 13, 10: 11, 11: 14, 12: 9, 13: 10, 14: 12}

    @property
    def hand_winner(self):
        return self._hand_winner

    @property
    def bonus_litige(self):
        return self.__bonus_litige

    @bonus_litige.setter
    def bonus_litige(self, value):
        self.__bonus_litige = value

    @property
    def player_with_belote(self):
        return self.__player_with_belote

    @player_with_belote.setter
    def player_with_belote(self, value):
        self.__player_with_belote = value

    @property
    def belote_status(self):
        return self.__belote_status

    @belote_status.setter
    def belote_status(self, value):
        self.__belote_status = value

    @property
    def win_game_points(self):
        return self.__win_game_points

    @win_game_points.setter
    def win_game_points(self, value):
        self.__win_game_points = value

    def get_state(self):
        state = BeloteState(self.id)
        new_state = self.populate_state(state)
        return new_state

    def populate_state(self, state):
        my_state = CardGame.populate_state(self, state)
        my_state.allowed_bets = self.get_allowed_bets(self.active_player)
        my_state.phase = self.phase
        my_state.hand_winner = copy.deepcopy(self.hand_winner)
        my_state.taker = self.taker
        if self.taker is not None:
            my_state.taker = str(self.taker)
        my_state.belote_status = self.belote_status
        return my_state

    def populate_from_state(self, state):
        CardGame.populate_from_state(self, state)
        self.soft_init_dict(self.wins, 0)
        self.soft_init_dict(self.bets, "")
        self.phase = state.phase
        self.soft_init_dict(self.hand_points, 0)

        # self.hand_winner = copy.deepcopy(state.hand_winner)
        if state.taker is not None:
            self.taker = Player(state.taker)

        self.belote_status = state.belote_status

    def player_announced_belote(self, player, value):
        # check player can announce (has the right cards and belote_state ha the right value)
        logging.debug("In player_announced_belote, value is: " + str(value))
        logging.debug("Belote state value: " + self.belote_status.name)
        if value == self.BeloteAnnounced.BELOTE:

            belote_ok = self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12") and \
                        self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13") and \
                        self.belote_status == BeloteStatus.Allowed
            if belote_ok:
                self.belote_status = BeloteStatus.Belote_Announced
        elif value == self.BeloteAnnounced.REBELOTE:
            belote_ok = (self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12") or
                         self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13")) and \
                        self.belote_status == BeloteStatus.Belote_Played
            if belote_ok:
                self.belote_status = BeloteStatus.Rebelote_Announced
        logging.debug("Belote state value: " + self.belote_status.name)
        return self.belote_status

    def has_player_card(self, player, card_as_str):
        for card in self.hands[player].cards:
            if str(card) == card_as_str:
                return True
        return False

    @property
    def belote_status(self):
        return self.__belote_status

    @belote_status.setter
    def belote_status(self, value):
        self.__belote_status = value

    def reset(self):
        CardGame.reset(self)
        self.taker = None

    def is_game_over(self):
        # Return True if one of the player or team has reached
        # the number of points required to win
        for player in self.players:
            if self.scores[player] > self.win_game_points:
                return True
        return False

    def add_player(self, player):
        CardGame.add_player(self, player)
        self.hand_points[player] = 0

    def disable_player(self, player):
        logging.info("In BeloteGame.disable_player, disabling player " + player)
        CardGame.disable_player(self, player)
        if player in self.players:
            self.phase = BeloteGame.GamePhase.DEAL

    def start_game(self):
        self._started = True
        self.deck_size = 32
        self.phase = BeloteGame.GamePhase.BET

    def place_bet(self, player, bet, ai=False):
        logging.info("Player " + player + "bid: " + bet)
        self.bets[player] = bet

        if bet == "pass":
            logging.info("Player passed")
            self._nb_pass_since_bet += 1

            # Ask next player
            self.active_player = self.next_player(player)
            if self.next_player_to_bet(player) is None:
                self.init_bets()
                if self.phase == BeloteGame.GamePhase.BET:
                    logging.debug("Moving to second round of betting")
                    self._nb_pass_since_bet = 0
                    self.phase = BeloteGame.GamePhase.BET2
                else:
                    logging.debug("Everybody has passed twice")
                    # BET2 phase, and nobody has taken
                    self.phase = BeloteGame.GamePhase.DEAL
                    self.dealer = self.next_player_to_deal()
        else:
            logging.info("Player took")
            self.phase = BeloteGame.GamePhase.PLAY
            self.trump_suit = bet
            self.taker = player

            # Note: this is also done in deal_2, so may be redundant
            self.set_cards_rank_and_value()
            
            self.active_player = self.next_player(self.dealer)

        return
    
    # Return None if all players have bet
    def next_player_to_bet(self, player, no_bet_string=""):
        logging.debug("Next player to bet after: " + player)
        next_player = self.next_player(player)
        if str(self.bets[next_player]) == no_bet_string or self._nb_pass_since_bet < len(self.players) - 1:
            logging.debug("Next player to bet after " + player + " is: " + next_player)
            return next_player
        else:
            logging.debug("No more player to bet")
            return None

    def get_allowed_bets(self, player):
        allowed_bets = []
        # if self.hands.get(player) is None:
        #     allowed_bets = []  # No hand yet
        if self.phase == self.GamePhase.BET:
            allowed_bets = ['pass', str(self.trump_card.get_suit_name())]
        elif self.phase == self.GamePhase.BET2:
            allowed_bets = ['pass']
            for suit in Card.SUIT_NAMES:
                if suit != self.trump_card.get_suit_name():
                    allowed_bets.append(suit)

        logging.debug("allowed bets:" + str(allowed_bets))
        return allowed_bets

    # Return list of allowed cards as a list of
    # cards represented as string (e.g. 'c4')
    def get_allowed_cards(self, player):
        # Allowed cards are cars of the same suit than the first card played
        # If no cards are of the same suit, trump cards must be played. If no trump card
        # any card is allowed
        allowed_cards = []
        if player is None or player not in self.hands:
            return allowed_cards
        if self.current_round is None:
            logging.debug("Current round is None")
            return allowed_cards
        if self.current_round.get_first_card_played() is None:
            # Round is just starting, all cards are allowed
            allowed_cards = self.get_hand(player).serialize()
        else:
            asked_suit = self.current_round.get_first_card_played().get_suit_name()
            winning_player = self.current_round.winning_player_for_suit(asked_suit)
            winning_card = self.current_round.cards_played[winning_player]
            trump_asked = (asked_suit == self.trump_suit)
            lower_trumps = []
            higher_trump = False
            logging.debug("Player %s hand is: %s ", player, self.hands[player].serialize())
            logging.debug("Asked suit is %s", asked_suit)
            logging.debug("Trump suit is  %s", self.trump_suit)
            for card in self.hands[player].get_cards():
                if card.get_suit_name() == asked_suit:
                    if trump_asked:
                        if card > winning_card:
                            # Only allow cards higher than already played trump
                            allowed_cards.append(str(card))
                            higher_trump = True
                        else:
                            lower_trumps.append(str(card))
                    else:
                        allowed_cards.append(str(card))

            # Allow smaller trumps if no higher trump
            if not higher_trump and len(lower_trumps) > 0:
                allowed_cards = lower_trumps

            # If player has trump, must play it unless partner has already cut or
            # partner played strongest card.
            # Also need to surcouper if applicable
            if len(allowed_cards) == 0:
                cut = (winning_card.get_suit_name() == self.trump_suit)
                for card in self.hands[player].cards:
                    # Check for trump cards
                    if card.get_suit_name() == self.trump_suit:
                        if not cut:
                            # if partner has highest card, do not have to cut
                            if len(self.players) == 4 and winning_player == self.next_player(self.next_player(player)):
                                return self.hands[player].serialize()
                            else:
                                # Else has to play trump
                                allowed_cards.append(str(card))
                        else:
                            # Somebody has cut already
                            if len(self.players) != 4:
                                if card > winning_card:
                                    # Only allow cards higher than already played trump
                                    allowed_cards.append(str(card))
                                    higher_trump = True
                                else:
                                    lower_trumps.append(str(card))
                            else:
                                # 4 players
                                if winning_player == self.next_player(self.next_player(player)):
                                    return self.hands[player].serialize()
                                else:
                                    if card > winning_card:
                                        # Only allow cards higher than already played trump
                                        allowed_cards.append(str(card))
                                        higher_trump = True
                                    else:
                                        lower_trumps.append(str(card))

                if not higher_trump and len(lower_trumps) > 0:
                    allowed_cards = lower_trumps

            # Any card is allowed if no asked suit and no trump
            if len(allowed_cards) == 0:
                allowed_cards = self.hands[player].serialize()

        # TODO: user has to surcouper if they can

        return allowed_cards

    def update_scores(self):
        # Check each player points
        # If 2 or 3 players, player that took need to have more points that other players to win
        # if 4 players, player that took and partner need to have more points than other players
        nb_players = len(self.players)
        players = []
        players.append(self.taker)
        player_points = []
        player_points.append(self.hand_points[self.taker])
        self._hand_winner = []

        for i in range(1, nb_players):
            players.append(self.next_player(players[i - 1]))
            player_points.append(self.hand_points[players[i]])

        for i in range(nb_players):
            if self.belote_status == BeloteStatus.Rebelote_Played and \
                    self.player_with_belote == players[i]:
                logging.info("In update_scores, adding belote / rebelote points to " + players[i])
                player_points[i] = player_points[i] + self.BELOTE_REBELOTE
                self.hand_points[players[i]] = player_points[i]

        if nb_players == 2:
            if player_points[0] > player_points[1]:
                self.scores[players[0]] += player_points[0] + self.bonus_litige
                self.scores[players[1]] += player_points[1]
                self.bonus_litige = 0
                self._hand_winner.append(players[0])

            elif player_points[1] > player_points[0]:
                self.scores[players[1]] += player_points[0] + player_points[1] + self.bonus_litige
                self.bonus_litige = 0
                self._hand_winner.append(players[1])
                if self.player_with_belote == players[0] :
                    self.scores[players[0]] += self.BELOTE_REBELOTE

            else:
                # Players are tied
                self.bonus_litige += player_points[0]
                logging.info("Points litige: " + str(self.bonus_litige))
                self._hand_winner.append("")

            # Capot
            if self.wins[players[1]] == 0:
                self.scores[players[0]] += self.BONUS_CAPOT - self.DIX_DE_DER
            elif self.wins[players[0]] == 0:
                self.scores[players[1]] += self.BONUS_CAPOT - self.DIX_DE_DER

        elif nb_players == 3:
            if player_points[0] > player_points[1] and player_points[0] > player_points[2]:
                self.scores[players[0]] += player_points[0]
                self.scores[players[1]] += player_points[1]
                self.scores[players[2]] += player_points[2]
                self._hand_winner.append(players[0])

            elif player_points[1] > player_points[2]:
                self.scores[players[1]] += player_points[1] + player_points[0]
                self.scores[players[2]] += player_points[2]
                self._hand_winner.append(players[1])
                if self.player_with_belote == players[0]:
                    self.scores[players[0]] += self.BELOTE_REBELOTE

            elif player_points[2] > player_points[1]:
                self.scores[players[2]] += player_points[2] + player_points[0]
                self.scores[players[1]] += player_points[1]
                self._hand_winner.append(players[2])
                if self.player_with_belote == players[0]:
                    self.scores[players[0]] += self.BELOTE_REBELOTE
                # Player 1 has same number of points than player 2
            else:
                self.scores[players[1]] += player_points[1] + player_points[0] / 2
                self.scores[players[2]] += player_points[2] + player_points[0] / 2

            # Capot
            # TODO: How is dix de der handled?
            for i in range(3):
                if self.wins[players[i]] == 0:
                    np = self.next_player(players[i])
                    nnp = self.next_player(np)
                    if self.wins[np] == 0:
                        # nnp gets the entire bonus
                        self.scores[nnp] += self.BONUS_CAPOT
                    elif self.wins[nnp] == 0:
                        # np gets the entire bonus
                        self.scores[np] += self.BONUS_CAPOT
                    else:
                        # np and nnp share the bonus
                        self.scores[np] += self.BONUS_CAPOT / 2
                        self.scores[nnp] += self.BONUS_CAPOT / 2

        elif nb_players == 4:
            # Required, as AI needs to know the team score for the hand
            self.hand_points[players[0]] = self.hand_points[players[0]] + self.hand_points[players[2]]
            self.hand_points[players[2]] = self.hand_points[players[0]]
            self.hand_points[players[1]] = self.hand_points[players[1]] + self.hand_points[players[3]]
            self.hand_points[players[3]] = self.hand_points[players[1]]

            if player_points[0] + player_points[2] > player_points[1] + player_points[3]:
                self.scores[players[0]] += player_points[0] + player_points[2] + self.bonus_litige
                self.scores[players[2]] = self.scores[players[0]]
                self.scores[players[1]] += player_points[1] + player_points[3]
                self.scores[players[3]] = self.scores[players[1]]
                self.bonus_litige = 0
                self._hand_winner.append(players[0])
                self._hand_winner.append(players[2])

            elif player_points[1] + player_points[3] > player_points[0] + player_points[2]:
                self.scores[players[1]] += self.TOTAL_POINTS + self.bonus_litige
                self.scores[players[3]] = self.scores[players[1]]
                self.bonus_litige = 0
                if self.player_with_belote == players[0] or self.player_with_belote == players[2]:
                    self.scores[players[0]] += self.BELOTE_REBELOTE
                    self.scores[players[2]] = self.scores[players[0]]
                self._hand_winner.append(players[1])
                self._hand_winner.append(players[3])
            else:
                # Same number of points for both teams
                # The team that did not take get their points
                # The other team points are attributed to the winner of the next hand
                self.bonus_litige += player_points[0]
                logging.info("Points litige: " + str(self.bonus_litige))
                self._hand_winner.append("")

            # Capot
            points_capot = self.BONUS_CAPOT - self.DIX_DE_DER
            if self.wins[players[1]] + self.wins[players[3]] == 0:
                self.scores[players[0]] += points_capot
                self.scores[players[2]] = self.scores[players[0]]
            elif self.wins[players[0]] + self.wins[players[2]] == 0:
                self.scores[players[1]] += points_capot
                self.scores[players[3]] = self.scores[players[1]]

        logging.debug("Player points: %s", player_points)
        self.scoresheet.append(self.scores.copy())
        return self.scores

    # Initial deal
    def deal(self, dealer=None):
        hands = self.deal_cards(self.nb_cards_first_deal[len(self.players)], dealer=dealer)
        # Pick up trump card
        self.trump_card = self.deck.deal()
        return hands

    def deal_cards(self, nb_cards, dealer=None):
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.init_bets()
        self.init_dict(self.wins, 0)
        self.init_dict(self.hand_points, 0)
        self.trump_suit = None
        self.rounds = []
        self._nb_pass_since_bet = 0

        # Reset belote/rebelote states
        self.belote_status = BeloteStatus.Not_Allowed
        # self.BeloteAnnounced = BeloteGame.BeloteAnnounced.No
        self.__player_with_belote = None

        if dealer == None:
            self.dealer = self.active_player
        else:
            self.dealer = dealer

        self.active_player = self.next_player(self.dealer)

        # Create a hand with nb_cards for each player
        for player in self.get_playing_players():
            hand = Hand(self.deck, nb_cards, player)
            self.hands[player] = hand.sort()
            logging.debug("Hand for player " + player + " : " + str(hand.serialize()))

        # Pick up trump card
        self.phase = BeloteGame.GamePhase.BET
        return self.hands

    # Distribute 3 cards for each player
    def deal_2(self, dealer=""):
        logging.debug("In deal_2")

        nb_cards = self.nb_cards_second_deal[len(self.players)]

        # Taker takes the top card then two more
        self.hands[self.taker].add(self.trump_card)
        for i in range(nb_cards - 1):
            self.hands[self.taker].add(self.deck.deal())
        self.hands[self.taker].sort()

        # Other players take 3 cards
        for player in self.get_playing_players():
            if player != self.taker:
                for i in range(nb_cards):
                    self.hands[player].add(self.deck.deal())
                self.hands[player].sort()

        self.update_belote_status()

        # Required to make sure the trump card  is also update properly
        self.set_cards_rank_and_value()

        return self.hands

    def update_belote_status(self):
        # Determine whether Belote / Rebelote enabled for each player
        self.belote_status = BeloteStatus.Not_Allowed
        self.player_with_belote = None
        for player in self.get_playing_players():
            queen = False
            king = False
            if self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12"):
                queen = True
            if self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13"):
                king = True
            if queen and king:
                logging.info("Player " + player + " can announce belote/re-belote")
                self.belote_status = BeloteStatus.Allowed
                self.player_with_belote = player
                break
        return

    def play_card(self, player, card_value):
        winner = CardGame.play_card(self, player, card_value)
        if self.is_hand_completed():
            # Add 10 points to the winner of the last round
            self.hand_points[winner] += 10

        # Check whether belote / rebelote card played
        # logging.debug ("In Belote.card_played, belote_state is: " + self.belote_state.name)
        belote_card_played = (card_value == Card.get_suit_initial(self.trump_suit) + "12" or
                              card_value == Card.get_suit_initial(self.trump_suit) + "13")

        if belote_card_played and self.belote_status != BeloteStatus.Not_Allowed:
            if self.belote_status == BeloteStatus.Belote_Announced:
                self.belote_status = BeloteStatus.Belote_Played
                logging.debug("Player " + player + " played belote card: " + card_value)

            elif self.belote_status == BeloteStatus.Rebelote_Announced:
                self.belote_status = BeloteStatus.Rebelote_Played
                logging.debug("Player " + player + " played re-belote card: " + card_value)

            elif self.belote_status == BeloteStatus.Allowed or \
                    self.belote_status == BeloteStatus.Belote_Played:
                # Player lost the points if it was played but not announced
                self.belote_status = BeloteStatus.Lost
                logging.debug("Player " + player + " lost the belote/rebelote points")

        return winner

    def round_ended(self, winner):
        points = self.points_for_round( self.current_round)
        self.hand_points[winner] += points
        return

    def points_for_round(self, round):
        player_cards = round.cards_played
        points = 0
        for player in player_cards:
            card = str(player_cards[player])
            points = points + self.card_points[card]
        logging.debug("Points in round:" + str(points))
        return points

    def hand_completed(self):
        CardGame.hand_completed(self)
        self.belote_status = BeloteStatus.Not_Allowed
        # TODO: check if score threshold has been reached
        # and set game state to OVER if it as

    def set_cards_rank_and_value(self):
        self.reset_card_ranks_and_points()

        suit_trump = Card.get_suit_initial(self.trump_suit)
        self.card_points[suit_trump + "9"] = 14
        self.card_points[suit_trump + "11"] = 20

        for i in range(7, 15):
            self.card_ranks[suit_trump + str(i)] = self.ranks_trump[i]

        for player in self.players:
            for card in self.get_hands()[player].cards:
                card.rank = self.card_ranks[str(card)]
                card.points = self.card_points[str(card)]

        for card in self.deck.cards:
            card.rank = self.card_ranks[str(card)]
            card.points = self.card_points[str(card)]

        if self.current_round is not None:
            for card in self.current_round.cards_played.values():
                if card is not None:
                    card.rank = self.card_ranks[str(card)]
                    card.points = self.card_points[str(card)]

    def init_bet(self, player):
        self.bets[player] = ""

    def init_bets(self):
        self.init_dict(self.bets, "")
