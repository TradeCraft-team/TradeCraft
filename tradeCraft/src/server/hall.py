"""
Deals with non-game activities.

class Hall(Game) aims at organizing players in the room
into games.

class MainEntry(Hall) is the root room where players
with first connection to the server goes here.

"""
from flask import session
from fractions import Fraction
from .game import Game
from .player import Player
from .app import PLAYERS, HALLS, GAMES, logger, print
from .config import GAME_RULES


class Hall(Game):
    """
    Hall may represent a game mode, which register all
    players who wants to play this mode, and at the same time
    define their opponents in some specific way.

    e.g. 3-player random-matching game can be hosted in a Hall
         (looks like ladder games in StarCraft, DoTA, etc.),
         2-player seated game (Like QQ Card Games) can be hosted
         in another Hall.
    """

    def __init__(self, **kwargs):
        """
        """
        super(Hall, self).__init__(**kwargs)
        self.unassigned_players = self.players  # dict
        self.observers = self.players  # In a Hall, observer and player are the same.
        self.description = kwargs.get("description", "NO DESCRIPTIONS.")
        self.ingame_players = {}
        self.ongoing_games = {}
        self.available_games = {}
        # a Hall contains game with the same game_config
        self.game_config = kwargs.get("game_config", {"num_players": 2})
        self.games = []
        # self.roster = {"unassigned": []}
        for _ in range(kwargs.get("init_game_pool_size", 0)):
            game = self._new_game()
            self.games.append(game)
            # self.roster.update(game.roster)

    def general_info(self):
        """
        Return the status and rule info of the hall
        """
        print(self.available_games)
        return {
            "ongoing_games":
            len(self.ongoing_games),
            "ingame_players":
            len(self.ingame_players),
            "ingame_players_roster":
            list(self.ingame_players.keys()) +
            list(self.unassigned_players.keys()),
            "available_players":
            len(self.unassigned_players),
            "players_on_wait":
            sum(len(x.players) for x in self.available_games.values()),
            "available_games":
            len(self.available_games)
        }

    def detailed_info(self):
        """
        Return detailed info.
        """
        return [(gamename, len(game.players))
                for gamename, game in self.available_games]

    def on_get_detailed_info(self, msg):
        """
        """
        if (token := msg.get("token", "")) not in self.token_to_username:
            return
        player = self.players[self.token_to_username[token]]
        player.unicast(
            "hall_detailed_info", {
                "hallname": self.gamename,
                "onging_games": self.onging_games.keys(),
                "available_games": self.available_games.keys()
            })

    def _new_game(self, _class=Game, global_collection=GAMES, **kwargs):
        """
        Add a new Game
        """
        game = _class(parent=self, **self.game_config, **kwargs)
        self.available_games[game.gamename] = game
        global_collection[game.gamename] = game
        logger.info("Game '%s' is created.", game.gamename)
        return game

    def _get_next_available_game(self):
        """
        Get next available game, create one if not exists.
        """
        if len(self.available_games) > 0:
            return sorted(self.available_games.values(),
                          key=lambda x: len(x.players),
                          reverse=True)[0]
        return self._new_game()

    def add_player(self, player, player_type="player") -> int:
        """
        Remove from ingame_players if in it.
        """
        self.ingame_players.pop(player.username, None)
        rv = super().add_player(player, player_type)
        self._assign_all_players()

    def _assign_player(self, username: str, game: Game) -> int:
        """
        If assign a player to some Game, then turn the player to
        ingame player, otherwise just remove.
        """
        player = self.players[username]
        ret = super()._assign_player(username, game)
        if game.prefix == "game__":  # Check if game is an instance of Game (instead of any subclasses)
            self.ingame_players[username] = player
            # When a game is full, start.
            # [TODO] May tell the player to vote whether start? (think DOTA matching)
            # We need all players send  "player__ready_to_start" to start.
            #         on frontend, it is sent automatically, for `agent_proxy`, this should be binded
            #         to an automatic starting tool-using.
            # if game.num_players == len(game.players):
            #     game.start()

        return ret

    def _assign_all_players(self):
        """
        Assign all players in the "unassigned" into games / halls
        """
        while len(self.players) > 0:
            username = list(self.players.keys())[0]
            game = self._get_next_available_game()
            print(self.prefix, s=2)
            logger.info(game)
            self._assign_player(username, game)

    def get_games(self) -> list:
        return list(self.available_games.keys())

    def enter_game(self, username, game_name):
        player = self.players.get(username)
        if player and game_name in self.games:
            game = self.games[game_name]
            game.add_player(player)
            return True
        return False

    def remove_player_(self, username):
        if username in self.players:
            del self.players[username]

    # Callbacks of events: with function name `on_xxx` and deals with event `hall__xxx`

    def on_enter_game(self, msg):
        """
        Used in both Hall to enter game
        and in MainEntry to enter a Hall.
        """
        username = msg.get("username", "")
        if username not in self.players:
            return
        game_name = msg.get("game_name", "")
        if game_name not in self.available_games:
            self.players[username].unicast(
                "error", {"info": f"{game_name} does not exist!"})
        self._assign_player(username, self.available_games[game_name])


class MainEntry(Hall):
    """
    Main entry of all clients as they connect to server.

    Assign Player instance to each connection.
    Roster
    """

    def __init__(self, **kwargs):
        """
        """
        kwargs["prefix"] = ""
        super(MainEntry, self).__init__(**kwargs)
        print("init MainEntry instance", s=3)
        # self.roster = {"unassigned": []}
        self.halls = self.available_games
        self.__create_halls()

    def __create_halls(self):
        """
        Create Halls when the server starts to run.
        """
        for rule_name, rule in GAME_RULES.items():
            self.game_config = rule
            hall = self._new_game(Hall, HALLS, gamename=rule_name)
        print(self.halls, HALLS, s=4)

    def add_player(self, player, player_type="player") -> int:
        """
        Remove from ingame_players if in it.
        """
        self.ingame_players.pop(player.username, None)
        rv = super(Hall, self).add_player(player, player_type)

    # Design a login-connect-chooseHall logic

    def on_connect_to_server(self, msg):
        self.event_handler.emit("test_response", "TEST")
        print("halls:", HALLS, "games:", GAMES, "players:", PLAYERS, s=5)

    def on_connect(self, msg):
        """
        Deals with `connect` event
        """
        logger.info("Player")
        print(session, s=1)
        username = session.get("username", "")
        if username:
            self.event_handler.emit("server__restored_proof_requested", {})

        # self.event_handler.emit("test_response", "TEST")
        # logger.info(session)
        # if (username := session.get("username", "")) in PLAYERS:
        #     token = PLAYERS[username].token
        #     status = self.players[token].status

        #     pass  # emit necessary info to that player.
        # elif username != "":
        #     print("USERNAME:", username)
        #     player = Player(self, username=username)
        #     PLAYERS[username] = player
        #     self.players[player.token] = player
        # else:
        #     self.event_handler.emit("please_register", "Plz provide username")

    def on_restored_proof(self, msg):
        """
        After reconnected, client should prove they are the one they were before.
        If passed the check, one can restore the game directly.
        """
        session_username = session.get("username", "")
        username = msg.get("_username", "")
        token = msg.get("_token", "")
        if username and (username in PLAYERS):
            if (session_username == username
                    and (player := PLAYERS[username]).token == token):
                session["in_use"] = True
                player.is_connected = True
                # if player.game.status.get("is_over", True):
                #     player.game = player.game.parent.parent
                player.game.add_player(player)
                self.event_handler.emit(
                    "game_restored", {
                        "gamename": player.game.gamename,
                        "gametype": player.game.__class__.__name__
                    })
                return

        self.event_handler.emit(
            "restored_proof_invalid",
            {"message": "username / token check failed. Please login."})

    def on_login(self, msg):
        """
        Login callback

        -----------------------
        [TODO] disconnect and reconnection dynamics:
        ON_DISCONNECT: game->pause
                       if no people in game, game ends

        ON_CONNECT:
                  case 1: same machine: ask restore-game-or-not
                          [1] if restore: check token, then game->restore
                  case 2: refreshed should goto login (automatically.)
                  case 3: on another machine.
                          [2,3] unicast necessary info, and game->restore
                                login_success with reconnected code.
                                client should ask for history if so.

        disconnect should not lead to the lost of any status info. unless
        when reconnected, it is found that the session has no token.

        -----------------------------
        Logic:

        1. This session is running another player
           -> session_conflict, status_code: 3
        2. This username is in use and running on other session
           -> username_conflict, status_code: 2
        3. This username is in state of disconnection and waiting for reconnection
           -> login_success, status_code: 1
        4. Session is free and username is not in use.
           -> login_success, status_ccde: 0
        """

        # check if the session is occupied by other existing player.
        # Case 1: session.username exists and active
        uname_session = session.get("username", "_")
        print(session, s=1)
        if (player_session := PLAYERS.get(uname_session, {})):
            if player_session.is_connected and session.get("in_use", False):
                self.event_handler.emit(
                    "session_conflict", {
                        "status_code": 3,
                        "message":
                        f"Your session is in use by {uname_session}."
                    })
                return
        # Case 2-4: session is not in use.
        username = msg["username"]
        # Case 2: New username, register
        if username not in PLAYERS:
            player = Player(self, username=username)
            self.add_player(player)
            PLAYERS[username] = player
            player._unicast(
                "login_success", {
                    "status_code": 0,
                    "message": "Login successful.",
                    "username": username,
                    "token": player.token
                })
            session["username"] = username
            session["in_use"] = True
        # Case 3: old username and the username is in use by another session:
        elif PLAYERS[username].is_connected:
            self.event_handler.emit(
                "username_conflict", {
                    "status_code":
                    2,
                    "message":
                    f"The username \"{username}\" is being used by another player!"
                })
        # Emit login success and waiting for pairing message
        # Case 4: reconnection. assign a new token and rejoin game if exists.
        else:
            player = PLAYERS[username]
            player.is_connected = True
            player._generate_token()
            self.event_handler.emit(
                "login_success", {
                    "message": "Reconnect successful, loading status.",
                    "status_code": 1,
                    "username": username,
                    "token": player.token
                })
            print("RECONNECTION",
                  self.ongoing_games,
                  player.game.gamename,
                  s=6)
            session["username"] = username
            session["in_use"] = True
            if (player.game.prefix == "game__"
                    and player.game.gamename in self.ongoing_games):
                # self._assign_player(username, player.game)
                player.game.token_to_username[player.token] = player.username

                # [TODO 0821] send necessary state messages as stated in docstring.
                # player.unicast(
                #     "reconnection_history", {
                #         "broadast":
                #         player.game.event_handler.history["@broadcast"],
                #         "unicast": player.game.event_handler.history[username]
                #     })
            else:
                self.add_player(player)

        # [TODO] VERSION 1. Now entry -> Hall and Hall -> Game happens automatically
        # VERSION 2. May make players choose Hall / Games to add.
        # self._assign_all_players()

    def on_disconnect(self, msg):
        print("DISCONNECT, SESSION", session, s=24)
        username = session.get("username", "")
        if username:
            session["in_use"] = False
            player = PLAYERS[username]
            player.game.disconnect_player(username)
            player.is_connected = False

    def on_test(self, msg):
        msg.update({"number": Fraction(113, 355)})
        self.event_handler.emit("test_response", msg)

    def on_test_status(self, msg):
        self.event_handler.emit(
            "test_status", {
                "games": str(GAMES),
                "halls": str(HALLS),
                "players": str(PLAYERS),
                "back": str(eval(msg.get("script", "1+2"))),
            })

    def on_get_hall_info(self, msg):
        """
        """
        if not (username := self.token_to_username.get(msg.get("_token", ""),
                                                       "")):
            return
        if (hallname := msg.get("_hallname", "")) not in HALLS:
            return

        hall = HALLS[hallname]
        self.players[username].unicast(
            "hall_info", {
                "hallname":
                hallname,
                "general_info": [
                    hallname, "Description" + hall.description,
                    hall.general_info()
                ]
            })

    def on_get_entry_info(self, msg):
        """
        Tells the current hall list.
        """
        if (token := msg.get("_token", "")) not in self.token_to_username:
            print(token, self.token_to_username)
            pass
        hall_info = [(hallname, "Description:" + hall.description,
                      hall.general_info()) for hallname, hall in HALLS.items()]
        self.event_handler.emit("entry_info", {"halls": hall_info}, to=[token])

    def on_enter_hall(self, msg):
        """
        Enter a hall.
        """
        if (token := msg.get("_token", "")) not in self.token_to_username:
            print(token, self.token_to_username)
            pass

        hallname = msg.get("_hallname", "")
        if hallname not in HALLS:
            self.event_handler.emit("failed_enter_hall", {
                "reason": "NO SUCH HALLS.",
                **msg
            })
        else:
            self._assign_player(self.token_to_username[token], HALLS[hallname])

    def __del__(self):
        pass
