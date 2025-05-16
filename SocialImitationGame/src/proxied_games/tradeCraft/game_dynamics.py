"""
tradeCraft Game Dynamics
"""
import asyncio
from ...agent_proxy.base_proxied_game import BaseGameDynamics


class BasicTCGameDynamics(BaseGameDynamics):
    """
    """

    def __init__(self, *args, **kwargs):
        """
        Basic GD for tradeCraft

        FSM:
                               ---
                              | 5 |
                              v   |
        pre_login         make_proposal           -------------
           |1               3|   ^               |     11      |
           v        2        v   |4       10     v             |
        game_start ----> idle_watch (8)  <----> start_craft ---
                           6|   ^     |    9
                            v  7|     |
                       accept_reject   -----> game_over
                                         13
        """
        self.hallname = kwargs.get("hallname", "2-player-pool-matching")
        self.is_start = False
        # These are in-game related inputs / outputs / dynamics, etc.
        self._incoming_events = [
            'server__game_start',  # done
            'server__private_start_info',  # done
            'server__start_proposal',  # done
            'server__proposal',  # done
            'server__proposal_sent',  # done
            'server__proposal_invalid',  # done
            'server__proposal_accepted',  # done
            'server__proposal_rejected',  # done
            'server__proposal_reply_message',  # done
            'server__update_all_hands',  # done
            'server__craft_recipe_validity',  # done
            'server__private_hand_change',  # done
            'server__player_craft_done',  # done
            'server__possible_recipes_from_hand',  # done
            'server__phase_error',  # 'server__username_conflict',
            'server__reconnection_history',
            'server__game_over',
            'server__item_info',  # done
            "server__crafting_node_nonredirect",
            "server__gym_observation"
        ]

        self._outgoing_events = [
            "player__ready_to_start",
            "player__submit_proposal",  # 4 / 5
            "player__approval_or_reject",  # 6
            "player__craft_done",  # 9 / 11
            "player__craft_recipe_check",  # 9 / 11
            "player__craft_recipe_apply",  # 12
            "player__quit_game",  # 13
            "player__possible_recipes_from_hand",  # 9 / 11
            "player__gym_observation"
        ]
        self._error_events = ['server__phase_error']

        self._game_dynamics = {
            "player__ready_to_start": {
                "server__proposal": lambda *x: True,
                "server__start_proposal":
                lambda *x: x[0].get("proposer") == x[1].username,
                "server__phase_error": lambda *x: True,
                "server__game_over": lambda *x: True,
            },
            "player__submit_proposal": {
                "server__proposal_invalid",
                "server__proposal_accepted",
                "server__proposal_rejected",
                "server__phase_error",
                "server__game_over",
            },  # 4 / 5
            "player__approval_or_reject": {
                "server__proposal_accepted",
                "server__proposal_rejected",
                "server__phase_error",
                "server__game_over",
            },  # 6
            "player__craft_done": {
                "server__proposal": lambda *x: True,
                "server__start_proposal":
                lambda *x: x[0].get("proposer") == x[1].username,
                "server__phase_error": lambda *x: True,
                "server__game_over": lambda *x: True,
            },  # 9 / 11
            "player__craft_recipe_check": {
                "server__craft_recipe_validity",
                "server__phase_error",
                "server__game_over",
            },  # 9 / 11
            "player__craft_recipe_apply": {
                "server__private_hand_change",
                "server__phase_error",
                "server__game_over",
            },  # 12
            "player__quit_game": {
                "server__player_leave_room",
                "server__phase_error",
                "server__game_over",
            },  # 13
            "player__possible_recipes_from_hand": {
                "server__possible_recipes_from_hand",
                "server__phase_error",
                "server__game_over",
            },  # 9 / 11
            "player__crafting_node_nonredirect": {
                "server__crafting_node_nonredirect",
                "server__game_over",
            },
            "player__item_info": {
                "server__item_info",
                "server__game_over",
            }
        }
        self._hidden_dynamics = {
            # contains tools not given to agent.
            # DO NOT decorate the corresponding methods as tools.
            "player__gym_observation": {"server__gym_observation"},
            "player__gym_action": {"server__gym_action"}
        }

        # used for pause-step mode, Directly reflects the time's stepping on.
        self._active_end_turn = [self.end_this_turn]
        self._next_turn_start = ["server__start_proposal"]
        self.start_states = ["server__game_start"]
        self.stop_states = ["server__game_over"]
        self.entry_tool = ["ready_to_start"]
        self.close_tool = ["quit_game"]

    def eventname_to_toolname(self, event_name):
        """Translate Eventname to Toolname"""
        return event_name[8:]

    def toolname_to_eventname(self, tool_name):
        """Translate Eventname to Toolname"""
        return "player__" + tool_name

    # pregame and the following methods should be defined to handle the
    # nongame procedure though this may cause the entanglement of proxy and
    # game_dynamics, this looks inevitable.
    # May ask @Mr. WhiteBob~
    async def pregame(self, fsm, **kwargs):
        """
        Defines Pregame Behavior
        Returns when it is sure that the game really starts.
        """
        await super().pregame(fsm, **kwargs)

        self.fsm._base_msg_dict["username"] = fsm.username
        self.fsm.sio.emit("login", self.fsm._base_msg_dict)
        self.fsm.sio.on("server__username_conflict",
                        lambda msg: self.fsm.gameOver)
        self.fsm.sio.on("server__session_conflict",
                        lambda msg: self.fsm.gameOver)
        self.fsm.sio.on("server__login_success", self.on_login_success)
        self.fsm.sio.on("server__entry_info", self.on_entry_info)
        self.fsm.sio.on("server__game_start", self.on_game_start)
        self.fsm.sio.on("server__player_enter_room", self.on_player_enter_room)
        while not self.is_start:
            await asyncio.sleep(0.1)

    def on_login_success(self, msg):
        """
        Deal with server__login_success
        """

        self.token = msg["token"]
        self.fsm._base_msg_dict["token"] = self.token
        self.fsm.sio.emit("get_entry_info", {"_token": self.token})

    def enter_hall(self, hall):
        """
        Enter hall
        """
        self.fsm.sio.emit("enter_hall", {
            "_token": self.token,
            "_hallname": hall
        })

    def on_entry_info(self, msg):
        """
        Deal with server__entry_info
        """
        halls = msg["halls"]
        print("Entry_info:", halls)
        self.enter_hall(self.hallname if self.hallname else halls[0][0])

    def on_game_start(self, msg):
        """
        Callback of server__game_start.
        It registers the rest of waitfor_methods,
        since when the self.base_msg_dict is fixed.
        """
        self.fsm._base_msg_dict["gamename"] = msg.get("gamename")

    def on_player_enter_room(self, msg):
        self.fsm._base_msg_dict["gamename"] = msg.get("gamename")
        if msg["playername"] == self.fsm.username and msg["type"] == "Game":
            self.is_start = True

    def end_this_turn(self):
        pass
