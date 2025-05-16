"""
Handlers: EventHandler and MessageHandler
"""
import pickle
import json
import os
from datetime import datetime as dt
from abc import ABC
from typing import final

from flask_socketio import join_room, leave_room, emit
from .config import GAME_NAME_LEN, LOG_FORMAT
from .app import socketio, GAMES, Fraction, app, gen_rand_str
from . import logger
from .dbhandler import dbs, IS_CONN


class EventHandler:
    """
    EventHandler deals with socketio activities in Game level

    The DB level logging goes from here.

    PlayerMatcher is a subclass of Game.
    """

    def __init__(self, game):
        """
        """
        self.game = game
        self._index = -1
        self.cache_log = (game.prefix == "game__")
        self.players = self.game.players
        self.history = dict((x, []) for x in self.players)
        self.history["@broadcast"] = []
        self.history["@none"] = []
        self.saved = False

        if not os.path.exists("logs"):
            os.mkdir("logs")

        if self.cache_log:
            self.db_collection = dbs["TradeCraft"][f"Duo_{self.game.gamename}"]
            self.log_fptr_b = open(
                "logs/" + dt.now().strftime("%Y%m%d_%H%M%S") + ".pkl", "wb")
            self.log_fptr_w = open(
                "logs/" + dt.now().strftime("%Y%m%d_%H%M%S") + ".json", "w")

    @property
    def index(self):
        """
        Maybe use timestamp instead of index,
        to prevent reconnected users from getting extra information
        via knowing number of messages sent to others.
        """
        self._index += 1
        return self._index

    def log(self, to: list, event, msg):
        pass  # [TODO] DATABASE
        if self.cache_log:
            if IS_CONN:
                self.db_collection.insert_one({
                    "domain":
                    to,
                    "event":
                    event,
                    "msg":
                    app.json.dumps(msg),
                    "time":
                    dt.now().strftime("%Y%m%d-%H%M%S-%f")
                })
            for name in to:
                match name:
                    case "@none":
                        self.history[name] += [(event, msg, self.index)]
                    case self.game.gamename:
                        self.history["@broadcast"] += [(event, msg, self.index)
                                                       ]
                    case _:
                        if event != "server__reconnection_histroy":
                            print(name)
                            username = self.game.token_to_username.get(
                                name, "@none")
                            if username in self.history:
                                self.history[username] += [(event, msg,
                                                            self.index)]
                            else:
                                self.history[username] = [(event, msg,
                                                           self.index)]

    def handle(self, event, msg):
        """
        Handle an event with message msg
        """
        self.log([msg.get("token", "@none")], event, msg)
        if event[:8] != "player__":
            self.game.handle(event, msg)
        elif "token" in msg:
            print("EVENTHANDLER:", msg, msg["token"],
                  self.game.token_to_username)
            username = self.game.token_to_username.get(msg["token"], "")
            rv = -1
            if (player := self.players.get(username,
                                           {})) and event[:8] == "player__":
                rv = player.handle(event, msg)
                print("HANDLE_END:", username, rv)
        else:
            print("ERROR: token not valid", event, msg, s=-1)

    def emit(self, event, msg, to=None, **kwargs):
        """
        Redefine the emit from raw socketio
        """
        event = "server__" + event
        self.log(to, event, msg)
        if to is None:
            emit(event, msg, **kwargs)  # callback=dbhandler.~?
        else:
            for receiver in to:
                # to = to  # + [self.game.observer_room]
                emit(event, msg, to=receiver,
                     **kwargs)  # callback=dbhandler.~?

    def join_room(self, room):
        """
        wrap the join_room
        """
        join_room(room)

    def leave_room(self, room):
        """
        wrap the leave_room
        """
        leave_room(room)

    def __del__(self):
        """
        BEFORE deleting, save all history.

        DO NOT USE THIS if DATABASE is set.
        """
        if not self.saved:
            self.save_log(LOG_FORMAT)
        print("LOG_FORMAT: ", LOG_FORMAT)
        self.log_fptr_b.close()
        self.log_fptr_w.close()

    def save_log(self, _format="json"):
        print("Game Saved")
        match _format.lower():
            case "pickle":
                pickle.dump(self.history, self.log_fptr_b)
            case "json":
                self.log_fptr_w.write(app.json.dumps(self.history, indent=4))

        self.saved = True


class MessageHandler(ABC):
    """
    Defines an easy way to make handling messages simple

   `self.handle(event, msg)` is equivalent to
    eval(f"self._{event[self.prefix_len:]}").(msg).
    E.g. if `Game` inherits this class, then
    `game.handle("game__start", msg)` works via
    `game._start(msg)`.
    Therefore, once `Game._start()` is defined, `game__start`
    is automatically processed by it.


    - methods like `self.__abc` is internal (with extra auto name-change).

    - methods like `self.on_event` are used to deal with events in format
      prefix+"eventname". prefix by default is `classname__`
    - normal methods (like self.handle) are left for normal developments

    """

    def __init__(self, **kwargs):
        """
        Initialize
        """
        self.prefix = kwargs.get("prefix",
                                 self.__class__.__name__.lower() + "__")
        self.prefix_len = len(self.prefix)

    def __event_validation(self, event: str):
        if (self.prefix == event[:self.prefix_len]
                and event[self.prefix_len] != "_"):
            return True
        return False

    def handle(self, event: str, msg: dict):
        """
        Flexible handle entry, by default using the final internal method.
        """
        self.__handle(event, msg)

    @final
    def __handle(self, event: str, msg: dict):
        """
        The internal handle function
        """
        logger.info("EVENT:  %s", event)
        if self.__event_validation(event):
            try:
                r = getattr(self, f"on_{event[self.prefix_len:]}")(msg)
                return r
            except AttributeError as err:
                print(err)
                logger.info("Event `%s` has no defined handlers!", event)
                return 1
        logger.info("Event `%s` is invalid! %s", event, self.prefix)
        return 2

    def register_handler(self, event: str, handler: callable):
        """
        Deals with dynamic handler register
        """
        setattr(self, f"on_{event}", handler)

    @staticmethod
    def combine_hand(base, delta, action="add"):
        """
        Combine hand: delta added to / subtracted from base.
        [NOTE] MUST check befor combine, to avoid NEGATIVE VALUES!
        """

        factor = (Fraction(1) if action == "add" else Fraction(-1))
        for key, val in delta.items():
            base[key] = base.get(key, 0) + val * factor
            if base[key] == 0:
                base.pop(key)
        return base


# DUMMY_MESSAGE_HANDLER = MessageHandler()  # as game.
# DUMMY_MESSAGE_HANDLER.players = {}
# DUMMY_MESSAGE_HANDLER.event_handler = EventHandler(DUMMY_MESSAGE_HANDLER)
