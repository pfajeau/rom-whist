from enum import Enum
from random import choice
from random import randrange
from ..card import Card
from ..deck import Deck
from ..hand import Hand
from ..round import Round
from ..game import CardGame

class BeloteGame(CardGame):

    class GamePhase(Enum):
        DEAL = "Deal"
        DEAL2 = "Deal2"
        BET = "Bet"
        BET2 = "Bet2"
        PLAY = "Play"

    class BeloteAnnounced(Enum):
        BELOTE = "Belote"
        REBELOTE = "Rebelote"

    class BeloteState(Enum):
        Not_Allowed = 1
        Allowed = 2
        Belote_Announced = 3
        Belote_Played = 4
        Rebelote_Announced = 5
        Rebelote_Played = 6


    # Number of cards to deal depending on number of players
    # TODO: change for 2 players
    nb_cards_first_deal = {1:6, 2:6, 3:6, 4: 5}
    nb_cards_second_deal = {1:3, 2:3, 3:3, 4:3}

    # Total number of points
    TOTAL_POINTS = 162
    BONUS_CAPOT = 100
    BONUS_CAPOT = 100
    DIX_DE_DER = 10
    BELOTE_REBELOTE = 20

    def __init__(self, game_creator = ""):
        CardGame.__init__(self, game_creator, 0)
        self.taker = None
        self.teams = []
        self.hand_points=dict()   # The number of points collected while the hand is played
        #self.__belote_announced = BeloteGame.BeloteAnnounced.No
        self.__belote_state = BeloteGame.BeloteState.Not_Allowed
        self.__player_with_belote = None
        self.init_dict(self.hand_points,0)


        # Points and ranks will change for the trump suit once it is known
        self.card_points={"c7": 0, "c8":0, "c9":0, "c10":10, "c11":2, "c12":3, "c13":4, "c14":11,
                          "d7": 0, "d8":0, "d9":0, "d10":10, "d11":2, "d12":3, "d13":4, "d14":11,
                          "h7": 0, "h8": 0, "h9": 0, "h10": 10, "h11": 2, "h12": 3, "h13": 4, "h14": 11,
                          "s7": 0, "s8": 0, "s9": 0, "s10": 10, "s11": 2, "s12": 3, "s13": 4, "s14": 11}

        self.card_ranks={"c7": 7, "c8": 8, "c9": 9, "c10": 14, "c11": 11, "c12": 12, "c13": 13, "c14": 15,
                         "d7": 7, "d8": 8, "d9": 9, "d10": 14, "d11": 11, "d12": 12, "d13": 13, "d14": 15,
                         "h7": 7, "h8": 8, "h9": 9, "h10": 14, "h11": 11, "h12": 12, "h13": 13, "h14": 15,
                         "s7": 7, "s8": 8, "s9": 9, "s10": 14, "s11": 11, "s12": 12, "s13": 14, "s14": 15}

    @property
    def player_with_belote(self):
        return self.__player_with_belote

    @player_with_belote.setter
    def player_with_belote(self, value):
        self.__player_with_belote = value

    # @property
    # def belote_announced(self):
    #     return self.__belote_announced

    def player_announced_belote(self, player, value):
        # check player can announce (has the right cards and belote_state ha the right value)
        print("In player_announced_belote, value is: " + str(value))
        print (self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12"))
        print (self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12"))
        print("Belote state value: " + self.belote_state.name)
        print (self.belote_state.name == self.BeloteState.Allowed.name)
        if value == self.BeloteAnnounced.BELOTE:
            belote_ok = self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12") and \
                        self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13") and \
                        self.belote_state == self.BeloteState.Allowed
            if belote_ok:
                self.belote_state = self.BeloteState.Belote_Announced
        elif value == self.BeloteAnnounced.REBELOTE:
            belote_ok = (self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12") or \
                        self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13")) and \
                        self.belote_state == self.BeloteState.Belote_Played
            if belote_ok:
                self.belote_state = self.BeloteState.Rebelote_Announced
        print("Belote state value: " + self.belote_state.name)
        return self.belote_state

    def has_player_card(self, player, card_as_str):
        for card in self.hands[player].cards:
            if str(card) == card_as_str:
                return True
        return False

    @property
    def belote_state(self):
        return self.__belote_state

    @belote_state.setter
    def belote_state(self, value):
        self.__belote_state = value

    def reset(self):
        CardGame.reset(self)
        self.taker = None

    def phase(self):
        return self.__phase

    def add_player(self, player):
        if player in self.players:
            print ("player already exits - re-enabling")
            self._player_status[player] = 1
            # Need to re-start hands
            self.active_player = self.dealer
            self.game_phase = BeloteGame.GamePhase.DEAL
            self.current_round = None
            # self.trump_card = None
            self.bets = dict()
            self.wins = dict()
            self.init_dict(self.bets, "")
            self.init_dict(self.wins, 0)
            self.hand_points[player] = 0

        else:
            self.players.append(player)
            self._player_status[player] = 1
            self.scores[player] = 0
            self.bets[player] = ""
            self.wins[player] = 0
            self.hand_points[player] = 0

    def disable_player(self, player):
        print("In Game.disable_player, disabloing playerL " + player)
        if player in self.players:
            self._player_status[player] = 0
            print(self._player_status)
            if player == self.dealer:
                self.dealer = self.next_player_to_deal()
            self.active_player = self.dealer
            self.game_phase = BeloteGame.GamePhase.DEAL
            self.current_round = None
            # self.trump_card = None
            self.bets = dict()
            self.wins = dict()
            self.init_dict(self.bets, -1)
            self.init_dict(self.wins, 0)

    def start_game(self):
        self._started = True;

        # Set deck size based on number of players
        self.deck_size = 32

        # Create hand progression
        self._phase = BeloteGame.GamePhase.BET

    def place_bet(self, player, bet):
        print("place_bet for player {} is {}".format(player, bet))
        self.bets[player] = bet

        if (bet == "Pass"):
            print ("Player passed")
            # Ask next player
            self.active_player = self.next_player(player)
            if self.next_player_to_bet(player) is None:
                if self.phase == BeloteGame.GamePhase.BET:
                    self.phase = BeloteGame.GamePhase.BET2
                    self.init_dict(self.bets,"")
                else:
                    # TODO: redistribute cards and reset game
                    self.init_bets()
                    self.phase = BeloteGame.GamePhase.DEAL
                    self.dealer = self.next_player_to_deal()
        else:
            print ("Player took")
            self.phase = BeloteGame.GamePhase.PLAY
            # TODO: this will not work when UI translated to diferent language, as string passed will be diifferent
            # than what is in the enum
            self.trump_suit = bet
            self.taker = player
            self.set_cards_rank_and_value()
            self.active_player = self.next_player(self.dealer)

            # Determine whether Belote / Rebelote enabled for each player
            for player in self.get_playing_players():
                print ("Teesting " + player)
                queen = False
                king = False
                print (Card.get_suit_initial(self.trump_suit) + "12")
                if self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12"):
                    queen = True
                if self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13"):
                    king = True
                print (queen)
                print (king)
                if queen and king:
                    print ("Player " + player + " can announce belote/re-belote")
                    self.belote_state = BeloteGame.BeloteState.Allowed
                    self.player_with_belote = player
                    return
            self.belote_state = BeloteGame.BeloteState.Not_Allowed
            self.player_with_belote = None

            # TODO: active player must now be the one after the one that dealt the cards

    # Return None if all players have bet
    def next_player_to_bet(self, player):
        print("Next player to bet after: "+ player)
        nplayer = self.next_player(player)
        if self.bets[nplayer] != "" or len(self.get_playing_players()) == 1:
            print ("No more player to bet")
            return None
        else:
            print ("Next player to bet after {} is: {}", player, nplayer)
            return nplayer

    def allowed_bets(self, player):
        allowed_bets = []
        # if self.hands.get(player) is None:
        #     allowed_bets = []  # No hand yet
        if self.phase == self.GamePhase.BET:
            allowed_bets = ['Pass', str(self.trump_card.get_suit_name())]
        elif self.phase == self.GamePhase.BET2:
            allowed_bets = ['Pass']
            for suit in Card.SUIT_NAMES:
                if suit != self.trump_card.get_suit_name():
                    allowed_bets.append(suit)

        print("allowed bets:", allowed_bets)
        return allowed_bets

    # Return list of allowed cards as a list of
    # cards represented as string (e.g. 'c4')
    def get_allowed_cards(self, player):
        # Allowed cards are cars of the same suit than the first card played
        # If no cards are of the same suit, trump cards must be played. If no trump card
        # any card is allowed
        allowed_cards = []
        if self.current_round is None:
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

            # If player has trump, must play it unless partner has already cut.
            # Also need to surcouper if applicable
            if len(allowed_cards) == 0:
                cut = (winning_card.get_suit_name == self.trump_suit)
                for card in self.hands[player].cards:
                    # Check for trump cards
                    if card.get_suit_name() == self.trump_suit:
                        if not cut:
                            # Then trump card allowed
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
                                 if winning_player != self.next_player(self.next_player(player)):
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

    # TODO: Belote / Rebelote
    def update_scores(self):
        # Check each player points
        # If 2 or 3 players, player that took need to have more points that other players to win
        # if 4 players, player that took and partner neeed to have more points than other pplayers
        nb_players = len(self.players)
        players = []
        players.append(self.taker)
        player_points = []
        player_points.append(self.hand_points[self.taker])
        player = self.taker
        for i in range(1, nb_players):
            players.append(self.next_player(players[i-1]))
            player_points.append(self.hand_points[players[i]])

        # Belote / Rebelote
        if self.belote_state == BeloteGame.BeloteState.Rebelote_Played:
            points_to_reach = (BeloteGame.TOTAL_POINTS + BeloteGame.BELOTE_REBELOTE) / 2
        else:
            points_to_reach = BeloteGame.TOTAL_POINTS/2

        # TODO: handle case where both players have the same number of points
        if nb_players == 2:
            if player_points[0] > player_points[1]:
                self.scores[players[0]] += player_points[0]
                self.scores[players[1]] += player_points[1]
            else:
                self.scores[players[1]] += player_points[0] + player_points[1]

            # Capot
            if self.wins[players[1]] == 0:
                self.scores[players[0]] += BeloteGame.BONUS_CAPOT - BeloteGame.DIX_DE_DER
            elif self.wins[players[0]] == 0:
                self.scores[players[1]] += BeloteGame.BONUS_CAPOT - BeloteGame.DIX_DE_DER

        elif nb_players == 3:
            if player_points[0] > player_points[1] and player_points[0] > player_points[2]:
                self.scores[players[0]] += player_points[0]
                self.scores[players[1]] += player_points[1]
                self.scores[players[2]] += player_points[2]
            elif player_points[1] > player_points[2]:
                self.scores[players[1]] += player_points[1] + player_points[0]
                self.scores[players[2]] += player_points[2]
            elif player_points[2] > player_points[1]:
                self.scores[players[2]] += player_points[2] + player_points[0]
                self.scores[players[1]] += player_points[1]
            # Player 1 has same number of points than player 2
            else:
                self.scores[players[1]] += player_points[1] + player_points[0] / 2
                self.scores[players[2]] += player_points[2] + player_points[0] / 2

            # Capot
            # TODO: How is dix de der handled?
            for i in range(3):
                if self.wins[players[i]] == 0:
                    np = self.next_player(players[i])
                    nnp = self.next_player(players[np])
                    if self.wins[np] == 0:
                        # nnp gets the entire bonus
                        self.scores[nnp] += BeloteGame.BONUS_CAPOT
                    elif self.wins[nnp] == 0:
                        # np gets the entire bonus
                        self.scores[np] += BeloteGame.BONUS_CAPOT
                    else:
                        # np and nnp share the bonus
                        self.scores[np] += BeloteGame.BONUS_CAPOT / 2
                        self.scores[nnp] += BeloteGame.BONUS_CAPOT / 2

        elif nb_players == 4:
            if player_points[0] + player_points[2] > points_to_reach:
                self.scores[players[0]] += player_points[0] + player_points[2]
                self.scores[players[2]]  = self.scores[players[0]]
                self.scores[players[1]] += player_points[1] + player_points[3]
                self.scores[players[3]] = self.scores[players[1]]
            else:
                # TODO: SOme rules give more points to the team in this case
                self.scores[players[1]] += BeloteGame.TOTAL_POINTS
                self.scores[players[3]] = self.scores[players[1]]

            # Capot
            points_capot = BeloteGame.BONUS_CAPOT - BeloteGame.DIX_DE_DER
            if self.wins[players[1]] + self.wins[players[3]] == 0:
                self.scores[players[0]] += points_capot
                self.scores[players[2]] = self.scores[players[0]]
            elif self.wins[players[0]] + self.wins[players[2]] == 0:
                self.scores[players[1]] += points_capot
                self.scores[players[3]] = self.scores[players[1]]

        self.scoresheet.append(self.scores.copy())
        return self.scores

    # Iniial deal
    def deal_1(self, dealer=""):
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.init_bets()
        self.init_dict(self.wins,0)
        self.init_dict(self.hand_points, 0)
        self.trump_suit = None

        # Reset belote/rebelote states
        self.belote_state = BeloteGame.BeloteState.Not_Allowed
        #self.BeloteAnnounced = BeloteGame.BeloteAnnounced.No
        self.__player_with_belote = None

        if dealer == "":
            self.dealer = self.active_player
        else:
            self.dealer=dealer

        self.active_player = self.next_player(self.dealer)

        # Create a hand with nb_cards for each player
        for player in self.get_playing_players():
            print (player)
            hand = Hand(self.deck, BeloteGame.nb_cards_first_deal[len(self.players)], player)
            self.hands[player] = hand.sort()
            print ("Hand for player ", player, " : ", hand.serialize())

        # Pick up trump card
        self.trump_card = self.deck.deal()
        self.phase = BeloteGame.GamePhase.BET
        return self.hands

    # Distribute 3 cards for each player
    def deal_2(self, dealer=""):
        print("In deal_2")

        nb_cards = BeloteGame.nb_cards_second_deal[len(self.players)]

        # Taker takes the top card then two more
        self.hands[self.taker].add(self.trump_card)
        for i in range(nb_cards-1):
            self.hands[self.taker].add(self.deck.deal())
        self.hands[self.taker].sort()

        # Other players take 3 cards
        for player in self.get_playing_players():
            if player != self.taker:
                for i in range(nb_cards):
                    self.hands[player].add(self.deck.deal())
                self.hands[player].sort()

        return self.hands

    # TODO: change this to be based on score reaching a certain threshold
    def is_game_over(self):
        return False

    def card_played(self, player, card_value):
        winner = CardGame.card_played(self, player, card_value)
        if self.is_hand_completed():
            # Add 10 points to the winnder of the last round
            self.hand_points[winner] += 10

        # Check wheter belote / rebelote card played
        # print ("In Belote.card_played, belote_state is: " + self.belote_state.name)
        if self.belote_state == BeloteGame.BeloteState.Belote_Announced:
            if card_value == Card.get_suit_initial(self.trump_suit) + "12" or \
                        card_value== Card.get_suit_initial(self.trump_suit) + "13":
                self.belote_state = BeloteGame.BeloteState.Belote_Played
                #self.player_with_belote = player
                print ("Player " + player + " played belote card: " + card_value)

        elif self.belote_state == BeloteGame.BeloteState.Rebelote_Announced:
            if card_value == Card.get_suit_initial(self.trump_suit) + "12" or \
                card_value == Card.get_suit_initial(self.trump_suit) + "13":
                print ("Giving belote/rebelote points")
                self.belote_state = BeloteGame.BeloteState.Rebelote_Played
                self.hand_points[player] += BeloteGame.BELOTE_REBELOTE
                #self.player_with_belote = player
                print("Player " + player + " played re-belote card: " + card_value)

        return winner

    def round_ended(self, winner):
        player_cards = self.current_round.cards_played
        points = 0
        for player in player_cards:
            card = str(player_cards[player])
            points = points + self.card_points[card]
        print("Points in round:" + str(points))
        self.hand_points[winner] += points
        #self.__belote_announced = BeloteGame.BeloteAnnounced.No
        return

    def hand_completed(self):
        CardGame.hand_completed(self)
        self.belote_state = BeloteGame.BeloteState.Not_Allowed

    def set_cards_rank_and_value(self):
        suit_char = Card.get_suit_initial(self.trump_suit)
        self.card_points[suit_char+"9"] = 14
        self.card_points[suit_char+"11"] = 20
        self.card_ranks[suit_char + "9"] = 16
        self.card_ranks[suit_char + "11"] = 17
        for player in self.players:
            for card in self.get_hands()[player].cards:
                card.rank = self.card_ranks[str(card)]
                card.points = self.card_points[str(card)]

        for card in self.deck.all_cards:
            card.rank = self.card_ranks[str(card)]
            card.points = self.card_points[str(card)]

    def init_dict(self, a_dict, value):
        for player in self.players:
            a_dict[player] = value

    def init_bets(self):
        self.init_dict(self.bets, "")