"""
Finite State Machine
"""
import json
from transitions import Machine
import asyncio
import socket
import socketio
from typing import Dict, Tuple
from .utils import print
from .base_proxied_game import (BaseGameDynamics, BaseGameConfig,
                                BASE_GAME_DYNAMICS, BASE_GAME_CONFIG)


class BaseFsm:
    """
    Base Finite State Machine (?) Naive version.
    """

    def __init__(self, proxy, **kwargs):
        """
        Initiate FSM an connections.
        """
        self.proxy = proxy

        # socket io object.
        self.sio = socketio.Client()
        self.asio = socketio.AsyncClient()

        # configs and game dynamics
        self.game_config = kwargs.get("game_config")
        self.game_dynamics = kwargs.get("game_dynamics")
        self.incoming_events = self.game_dynamics.incoming_events
        self.outgoing_events = self.game_dynamics.outgoing_events

        self._base_msg_dict = {}
        self.unread_messages = []
        self.read_messages = []
        self.all_messages = []
        self.info = {}
        self.return_event = {}
        self.return_msg = {}

        self.last_event = "login_success"
        self.states = ["pre_login", "game_start", "game_over"]
        self.fsm = Machine(model=self,
                           states=self.states,
                           transitions=[],
                           prepare_event='prepare_event',
                           initial='pre_login')
        self.fsm.add_transition("startGame", "pre_login", "game_start")
        self.fsm.add_transition("gameOver", "game_start", "game_over")

        self.start_states = self.game_dynamics.start_states
        self.stop_states = self.game_dynamics.stop_states

    async def connect(self):
        if self.game_config.server_addr in ["localhost", "127.0.0.1"]:
            ip = socket.gethostbyname(socket.gethostname())
            # try:
            #     ip = socket.gethostbyname(socket.gethostname())
            # except socket.gaierror:
            #     ip = "127.0.0.1"

        else:
            ip = self.game_dynamics.server_addr
        port = self.game_config.server_port
        self.sio.connect(f"http://{ip}:{port}", wait=True)
        self.register_sio_callbacks()
        print('my sid is', self.sio.sid)
        return self.sio.sid

    def register_sio_callbacks(self):
        """
        Register callbacks.
        """
        for event in self.incoming_events:
            self.sio.on(event, self._waitfor_callback(event))

    def _waitfor_callback(self, back_evt):

        def _callback(back_msg):
            self.unread_messages += [(back_evt, back_msg)]  # this should be~

            if (back_evt == "server__start_proposal"
                    and back_msg.get("proposer", "\"") != self.username):
                return
            self.return_event[back_evt] = back_msg
            self.return_msg[back_evt] = back_msg

        return _callback

    # @classmethod
    def generate_waitfor_methods(self,
                                 event_name: str,
                                 expected_returns: Dict = {}):
        """
        Generate waitfor_xxx methods, used in toolizing actions.
        event_name: `player__xxx`
        """
        name = self.game_dynamics.eventname_to_toolname(event_name)

        async def _inner(self, tool_msg) -> Tuple[Dict, bool]:
            """
            Inner Function
            """
            msg = tool_msg  # json.loads(tool_msg)
            [self.return_event.pop(x, "") for x in expected_returns]
            [self.return_msg.pop(x, "") for x in expected_returns]
            self.emit(event_name, msg)

            # [TODO] The system here is very fragile.
            # in dynamics, two forms are allowed:
            #   key == outgoing event names
            #   val == dictionary | set.
            #           in the case of val == dictionary:
            #                key == incoming events which interrupt the waiting
            #                val == function (message, fsm) => bool.
            #                       Usually lambda *x: condtion.
            match expected_returns:
                case dict(eret):
                    print("case eret==dict", s=2)
                    while not any(x in self.return_event
                                  and f(self.return_event.get(x, {}), self)
                                  for x, f in eret.items()):
                        await asyncio.sleep(0.2)

                case set(eret):
                    print("case eret==set", s=2)
                    while not any(x in self.return_event for x in eret):
                        await asyncio.sleep(0.2)

            [self.return_event.pop(x, "") for x in expected_returns]
            keys = [x for x in expected_returns if x in self.return_event]
            return (dict((key, self.return_msg[key]) for key in keys),
                    any(key in self.stop_states for key in keys))

        setattr(self.__class__, "waitfor_" + name, _inner)

    def emit(self, evt, msg):
        """
        New emit.
        """
        msg.update(self.base_msg_dict)
        self.sio.emit(evt, msg)

    async def pregame(self):
        """
        """

        self.username = self.proxy.game_config["username"]
        self.info["username"] = self.username

        await self.game_dynamics.pregame(self)
        self.game_start()

    def game_start(self):
        """
        Callback of server__game_start.
        It registers the rest of waitfor_methods, since when the self.base_msg_dict is fixed.
        """

        for name, rets in self.game_dynamics.game_dynamics.items():
            self.generate_waitfor_methods(name, rets)

    @property
    def base_msg_dict(self):
        return self._base_msg_dict

    # @staticmethod
    def prepare_event(self):
        print("STATE_TRANSITION:", self.state, s=2)

    async def _prelogin(self):
        """Alias of connect()"""
        return await self.connect()
