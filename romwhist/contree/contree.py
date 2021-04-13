import copy
import logging
from romwhist.belote.belote import BeloteGame
from romwhist.contree.contree_state import ContreeState
from romwhist.contree.announce import Announce
from romwhist.contree.announce import ContreStatus


class ContreeGame(BeloteGame):

    all_bet_points = [80, 90, 100, 110, 120, 130, 140, 150, "Capot"]

    def __init__(self, game_creator="", id=0):
        BeloteGame.__init__(self, game_creator, id)
        BeloteGame.nb_cards_first_deal = {1: 8, 2: 8, 3: 8, 4: 8}
        self.current_bet = None
        self.contree_status = ContreStatus.NORMAL
        self.init_bets()

    def get_state(self):
        state = ContreeState(self.id)
        self.populate_state(state)
        state.contree_status = self.contree_status
        for player in self.players:
            state.bets[player] = str(self.bets[player])

        return state

    def set_state(self, state):
        BeloteGame.set_state(self,state)
        self.contree_status = state.contree_status
        for player in self.players:
            self.bets[player] = Announce.from_str(state.bets[player])

    def place_bet(self, player, bet):
        logging.info("Player " + player + " bet: " + str(bet))
        self.bets[player] = bet

        if bet.suit == "Pass":
            logging.info("Player passed")
            # Ask next player
            next_player = self.next_player(player)
            next_player_to_bet = self.next_player_to_bet(player)
            logging.info("Next player to bet %s ", next_player_to_bet)
            if next_player_to_bet is None:
                if self.bets[next_player].suit == "Pass":
                    self.init_bets()
                    self.phase = BeloteGame.GamePhase.DEAL
                    self.dealer = self.next_player_to_deal()
                else:
                    self.phase = BeloteGame.GamePhase.PLAY
                    self.active_player = self.next_player(self.dealer)
                    self.trump_suit =  self.current_bet.suit
                    self.set_cards_rank_and_value()

                return

        if bet.points == BeloteGame.TOTAL_POINTS or self.next_player_to_bet(player) is None:
            # Move to PLAY phase
            self.phase = BeloteGame.GamePhase.PLAY
            self.trump_suit = bet.suit
            self.taker = player
            self.set_cards_rank_and_value()
            self.active_player = self.next_player(self.dealer)
            self.current_bet = bet

        else:
            self.active_player = self.next_player(player)

            if self.current_bet is None or bet > self.current_bet:
                self.current_bet = bet
                self.trump_suit = bet.suit
            elif bet.suit != "Pass":
                logging.error("Invalid Bet: %s", bet)

        return

    # Return None if all players have bet
    def next_player_to_bet(self, player):
        logging.debug("Computing next player to bet after: " + player)
        next_player = self.next_player(player)
        # If three other players than nplayers have passed and next_player has a bet
        # then move on to the play phase
        # If next player has passed and three other players have passed, then return None
        # If next_player has not bet then they are the next player to bet
        if self.bets[next_player] is None:
            return next_player

        # players = []
        # players.append(player)
        player2 = self.next_player(player)
        for i in range(1, len(self.players) - 1):
            #players.append(self.next_player(players[i - 1]))
            if self.bets[player2].suit != "Pass":
                return next_player
            player2 = self.next_player(player2)

        return None

    def get_allowed_bets(self, player):
        allowed_bets = []
        if self.phase == self.GamePhase.BET:
            if self.current_bet is None:
                allowed_bets = copy.deepcopy(ContreeGame.all_bet_points)
            else:
                for bet in ContreeGame.all_bet_points:
                    if bet != "Capot":
                        if bet > self.current_bet.points:
                            allowed_bets.append(bet)
                allowed_bets.append("Capot")

        logging.debug("allowed bets:" + str(allowed_bets))
        return allowed_bets

    def deal(self, dealer=""):
        return self.deal_cards(int(self.deck_size / len(self.players)), dealer)

    def deal_2(self):
        return

    def add_player(self, player):
        BeloteGame.add_player(self, player)
        if player in self.players:
            self.init_bets()
        else:
            self.bets[player] = Announce("", "")


    def init_bets(self):
        for player in self.players:
            self.bets[player] = Announce("", 0)


    def update_scores(self):
        # Check each player points
        # If 2 or 3 players, player that took need to have more points that other players to win
        # if 4 players, player that took and partner need to have more points than other players
        nb_players = len(self.players)
        players = []
        players.append(self.taker)
        player_points = []
        player_points.append(self.hand_points[self.taker])
        self.__hand_winner = []

        for i in range(1, nb_players):
            players.append(self.next_player(players[i - 1]))
            player_points.append(self.hand_points[players[i]])

        for i in range(nb_players):
            if self.belote_state == BeloteGame.BeloteState.Rebelote_Played and \
                    self.player_with_belote == players[i]:
                logging.info("In update_scores, adding belote / rebelote points to " + players[i])
                player_points[i] += BeloteGame.BELOTE_REBELOTE
                self.hand_points[players[i]] = player_points[i]

        # TODO: remove test (always 4 players) and add support for contree / surcontree
        if nb_players == 4:
            logging.debug("Bet points: %s", self.bets[players[0]].points)
            if self.player_with_belote is not None:
                # set score of partner of player who may have gotten
                # the belote points to be the same
                partner = self.next_player(self.next_player(self.player_with_belote))
                self.scores[partner] = self.scores[self.player_with_belote]

            if player_points[0] + player_points[2] >= self.bets[players[0]].points:
                self.scores[players[0]] += player_points[0] + player_points[2]
                self.scores[players[2]] = self.scores[players[0]]
                self.scores[players[1]] += player_points[1] + player_points[3]
                self.scores[players[3]] = self.scores[players[1]]
                self._hand_winner.append(players[0])
                self._hand_winner.append(players[2])

            else:
                self.scores[players[1]] += BeloteGame.TOTAL_POINTS
                self.scores[players[3]] = self.scores[players[1]]
                self._hand_winner.append(players[1])
                self._hand_winner.append(players[3])

            # Capot
            points_capot = BeloteGame.BONUS_CAPOT - BeloteGame.DIX_DE_DER
            if self.wins[players[1]] + self.wins[players[3]] == 0:
                self.scores[players[0]] += points_capot
                self.scores[players[2]] = self.scores[players[0]]
            elif self.wins[players[0]] + self.wins[players[2]] == 0:
                self.scores[players[1]] += points_capot
                self.scores[players[3]] = self.scores[players[1]]

        logging.debug("Player points: %s", player_points)
        self.scoresheet.append(self.scores.copy())
        return self.scores
