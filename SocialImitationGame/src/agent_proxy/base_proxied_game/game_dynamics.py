"""
Base Game Dynamics
"""

from abc import ABC, abstractmethod


class BaseGameDynamics(ABC):
    """
    Game Dynamics designed for each game.

    Defines all possible websocket events, possible agent-irrelevant behaviors
    like logging-in to the game, etc.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize.

        _game_dynamics = {outgoing_event:{
                              possible_incoming_event: state_change_to,
                              possible_incoming_event: state_change_to}}

        _hidden_dynamics: similar to _game_dynamics, for hidden query
                          (e.g. gymnasium) use only.
        """
        self._incoming_events = []
        self._outgoing_events = []
        self._game_dynamics = {}
        self._hidden_dynamics = {}

        # NOT IN USE NOW.

        # used for pause-step mode, Directly reflects the time's stepping on.
        self._active_end_turn = []
        self._passive_turn_start = self._passive_end_of_turn = []
        self.start_states = ["start"]
        self.stop_states = ["stop"]
        self.entry_tool = []

    @property
    def incoming_events(self):
        """
        Property: incoming_events
        """
        return self._incoming_events

    @property
    def outgoing_events(self):
        """
        Property: outgoing_events
        """
        return self._outgoing_events

    @property
    def game_dynamics(self):
        """
        Property: game_dynamics
        """
        return self._game_dynamics

    @property
    def error_events(self):
        """
        Property: game_dynamics
        """
        return self._error_events

    # @abstractmethod
    # def irrelevant_behaviors(self)
    # trigger, ..., whatever.

    async def pregame(self, fsm, **kwargs):
        self.fsm = fsm
