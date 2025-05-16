"""
Game
"""

import random
from copy import deepcopy
from .app import (logger, FULL_GRAPH, Graph, Node, pr_args, gen_rand_str,
                  process_item_dict, element_conditioner, print)
from .player import Player
from .config import GAME_NAME_LEN, PROBLEM_SAMPLER, DEFAULT_MAX_TURN

from .handlers import EventHandler, MessageHandler


class Game(MessageHandler):
    """
    Game. The actions of Players are all tested for validity / honesty.
    """

    def __init__(self, num_players: int = 2, **kwargs):
        """
        """
        # SET different rules using FSM module
        # self.game_fsm = kwargs.get("game_rule", None)
        super().__init__(**kwargs)
        logger.info("INITIALIZER: %s", self.__class__)
        self.game_token = gen_rand_str(GAME_NAME_LEN)
        self.token_to_username = {}
        self.gamename = kwargs.get("gamename", self.game_token[-8:])
        self.obs_name = self.gamename + "_obs"
        self.num_players = num_players
        self.full_flag = 2**num_players - 1
        self.status = {
            "is_started": False,
            "is_over": False,
            "is_game_on": False,
            "proposer_id": -1,
            "ready_status": 0,
            "crafting_done_status": 0,
            "is_crafting": False,
            "waiting_for_reply": "",
            "waiting_for_proposal": "",
            "waiting_for_connection": True,
            "turn_index": 0,
            "max_turn": -1,
        }
        self.current_proposal = {}
        self.craft_graph = {}
        self.players = {}  # {username: Player(self, i)} for i in num_players
        self.lost_players = {}  # temporarily disconnected players
        self.player_list = []
        self.observers = {}  # left blank for now
        self.action_queue = [None] * self.num_players
        self.hands = {}
        # self.action_order = {}
        # self.event_handler = EventHandler(self)
        self.event_handler = kwargs.get("event_handler", EventHandler(self))
        self.parent = kwargs.get("parent", {})  # change it?
        self.problem_type = kwargs.get("problem_type", "1p_v_1p")
        self.full_kwargs = kwargs

    def __repr__(self):
        return f"{self.__class__}: {self.gamename}\nPlayers: {self.players}\nStatus: {self.status}"

    def __if_change_proposer(self):
        """
        [TODO] Now following rule that each player propose once then next.
        """

        return True

    def __next_proposer(self):
        """
        This is called only when a game is loaded.
        """

        self.status["proposer_id"] = (self.status["proposer_id"] +
                                      1) % self.num_players

    def broadcast(self, event, msg):
        return self._broadcast(event, msg)

    def _broadcast(self, event: str, msg: dict):
        """
        Broadcast to all.
        """
        self.event_handler.emit(event, msg, to=[self.gamename])

    def add_player(self, player, player_type="player") -> int:
        """
        Game version of "add_player", settle an incoming player
        """
        if player_type == "player":
            if len(self.players) < self.num_players:
                # The following two can be affected by
                #   quitting games before start. move to start.
                # player.action_id = len(self.players)
                # self.action_queue += [player]
                self.players[player.username] = player
                if self.status["is_started"] and len(
                        self.players) == self.num_players:
                    self.status["waiting_for_connection"] = False

                self.token_to_username[player.token] = player.username
                player.game = self
                print("GAME: ",
                      player.game.gamename,
                      "Player:",
                      player.username,
                      player.token,
                      s=1)
                self.event_handler.join_room(self.gamename)
                self.player_list += [player.username]
                self.broadcast(
                    "player_enter_room", {
                        "type": self.__class__.__name__,
                        "gamename": self.gamename,
                        "playername": player.username,
                        "player_list": self.player_list,
                        "craft_rule_choice": pr_args["craft_rule_choice"],
                        "craft_rule_prefix": pr_args["craft_rule_prefix"],
                    })
                return 0
            else:
                return 1
        if player_type == "observer":
            self.observers[player.username] = player
            self.event_handler.join_room(self.obs_name)
            return 0

    def remove_player(self, username: str) -> int:
        """
        Remove should be an active quitting activity which cannot be
        reconnected.
        """
        self._assign_player(username, self.parent.parent)
        self.parent.ingame_players.pop(username, None)
        return self.disconnect_player(username)

    def disconnect_player(self, username: str) -> int:
        """
        When a player lost connections.

        1. We keep the game PAUSED until all players are lost.
        2. lost players are stored in self.lost_players
        3. when the game ends because of losting all players
           the game is removed and all lost players are assigned
           to entry, if they are not in other games right now.
        """
        # [TODO] If gpt takeover is added, add corresponding logic

        if self.status["is_started"] and len(self.players) == self.num_players:
            self.status["waiting_for_connection"] = True
            self.status["ready_status"] -= 1
            # [Question:] should there be any change in self.status["ready_status"]?
        else:
            self.player_list.remove(username)

        print(self.players, self.prefix, s=11)
        lost_player = self.players.pop(username, None)
        self._broadcast(
            "player_leave_room", {
                "gamename": self.gamename,
                "playername": username,
                "player_list": list(self.players.keys())
            })
        if lost_player is not None:
            self.lost_players[username] = lost_player
        if len(self.players) == 0 and self.prefix == "game__":
            # [TODO] Think about what if there are observers.
            self._broadcast("game_deleted", {"hall": self.parent.gamename})
            for playername, player in self.lost_players.items():
                if player.game.gamename == self.gamename:
                    self._assign_player(playername, self.parent.parent)
            if self.status["is_game_on"] or self.status["is_over"]:
                self.parent.ongoing_games.pop(self.gamename)
            else:
                self.parent.available_games.pop(self.gamename)

    def _assign_player(self, username: str, game) -> int:
        """
        Move a player by token to some other game.
        """
        # if self.status.get("is_game_on", False):
        #     return 1
        print(
            f"ASSIGN {self.gamename}.{username} to {game.gamename}: {self.players.keys()}",
            s=10)
        if username not in self.players:
            return 2
        self.event_handler.leave_room(self.gamename)
        player = self.players.pop(username)
        player.game = game
        self.token_to_username.pop(player.token)
        return game.add_player(player)

    def _load_game(self):
        problem = PROBLEM_SAMPLER(self.problem_type,
                                  **self.full_kwargs.get("problem_config", {}))
        self.hands = list(map(process_item_dict, problem["hands"]))
        self.targets = list(map(process_item_dict, problem["targets"]))
        self.status["max_turn"] = problem.get("max_turn", DEFAULT_MAX_TURN)
        resources = {}
        for hand in self.hands:
            self.combine_hand(resources, hand)

        resource_cond = element_conditioner(resources)
        if self.num_players == 1:
            self.craft_graph = FULL_GRAPH
        else:
            self.craft_graph, _ = FULL_GRAPH.reversed_subgraph(resource_cond)
        # print("___LOAD___", self.hands, self.action_queue)

        self.update_all_hands()
        for i, player in enumerate(self.action_queue):
            player.hand = deepcopy(self.hands[i])
            player.target = deepcopy(self.targets[i])
            player.unicast(
                "private_start_info", {
                    "gamename": self.gamename,
                    "index": i,
                    "username": player.username,
                    "target": player.target
                })

    def start(self):
        """
        Start game!

        1. Load hands and targets
        2. broadcast game-start together with necessary information:
           - player_name, player_id, hands.
        3. send to players to unicast the targets to each player.

        call start_proposal()
        """
        logger.info("Game '%s' starts.", self.gamename)
        self.status.update({
            "proposer_id": -1,
            "is_started": True,
            "is_over": False,
            "is_game_on": True,
            "crafting_done_status": 0,
            "waiting_for_connection": False
        })
        match self.full_kwargs.get("player_order", "sequential"):
            case "sequential":
                players = [
                    self.players[x] for x in self.player_list
                    if x in self.players
                ]
            case "random":
                players = random.sample(list(self.players.values()),
                                        self.num_players)
            case _:
                players = random.sample(list(self.players.values()),
                                        self.num_players)

        for i, player in enumerate(players):
            self.action_queue[i] = player
            player.action_id = i

        self.parent.available_games.pop(self.gamename)
        self.parent.ongoing_games[self.gamename] = self
        self._broadcast(
            "game_start", {
                "gamename": self.gamename,
                "player_list": [x.username for x in self.action_queue]
            })
        self._load_game()
        self.send_crafting_item_list()
        self.start_proposal()

    def update_all_hands(self):
        """
        Sync hands to everyone.
        """

        self._broadcast(
            "update_all_hands", {
                "gamename": self.gamename,
                "hands": self.hands,
                "player_list": [x.username for x in self.action_queue]
            })

    def sync_hand_from_player(self):
        """
        Read private hand updates from each player.
        """
        for ii, player in enumerate(self.action_queue):
            self.hands[ii] = deepcopy(player.hand)

    def start_proposal(self):
        """
        Broadcast start proposal to game

        after this, move to "send proposal" action after receiving a proposal.
        """

        if any(p.is_winner() for p in self.players.values()):
            self.game_over()
        if self.__if_change_proposer():
            self.__next_proposer()

        self.status["turn_index"] += 1
        # We define a turn as one proposal cycle.

        if self.status["turn_index"] > self.status["max_turn"]:
            # gameover
            self.game_over("Exceed max turn")

        self.status["waiting_for_proposal"] = self.action_queue[
            self.status["proposer_id"]].username
        self._broadcast(
            "start_proposal", {
                "turn_index": self.status["turn_index"],
                "max_turn": self.status["max_turn"],
                "gamename": self.gamename,
                "proposer": self.status["waiting_for_proposal"]
            })
        logger.info(self.status)

    def send_message(self, event, public, private, target_username):
        """
        Send private from a to b, and broadast public.

        [NOTE] NOT IN USE

        """
        self._broadcast(event, public)
        self.players[target_username]._unicast(event, private)

    def game_over(self, reason="win"):
        """
        Game over logic
        Maybe, some more statistical info sent to clients?
        """
        self.status["is_over"] = True
        self._broadcast(
            "game_over", {
                "gamename":
                self.gamename,
                "reason":
                reason,
                "targets":
                self.targets,
                "win-status":
                dict((x, p.is_winner()) for x, p in self.players.items()),
                "action_queue": [p._username for p in self.action_queue]
            })
        for player_name in list(self.players.keys()):
            self.remove_player(player_name)
        self.event_handler.save_log("json")

    def send_crafting_item_list(self):
        """
        Deal with request:

        ** crafting_item_list **
        """
        # pong back, no need to specify room
        self._broadcast(
            "crafting_item_list", {
                "game":
                self.gamename,
                "crafting_item_list": [
                    k for k, v in self.craft_graph.node_dict.items()
                    if v.node_type == "item"
                ]
            })

    # def __del__(self):
    #     self.parent.players.update(self.players)
    #     self.parent.players.update(self.observers)
    #     GAMES.pop(self.gamename)

    # handle events, add codes below for events


class GameWithChatroom(Game):
    """
    NOT IMPLEMENTED!
    """
