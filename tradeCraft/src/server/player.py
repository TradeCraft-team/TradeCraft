"""
Player
"""
import math
from copy import deepcopy
from fractions import Fraction
from .app import (Node, gen_rand_str, process_proposal, process_recipe,
                  process_item_dict, to_fraction, print, lint_to_fullname,
                  lint_to_simplename)
from .config import PLAYER_NAME_LEN
from .handlers import MessageHandler
from . import logger


class Player(MessageHandler):
    """
    Player in a Game or in the waiting room.
    """

    def __init__(self, game, action_id: int = 0, username: str = ""):
        """
        Initialize.
        """
        super().__init__()
        self.game = game
        self.hand = {}
        self.target = {}
        self.current_recipe = {}
        self.action_id = action_id
        self._username = username
        self._generate_token()
        self.is_connected = True

    # basic methods, supporting normal functions.

    def _generate_token(self):
        self.token = gen_rand_str(PLAYER_NAME_LEN)
        self.game.token_to_username[self.token] = self.username
        self.game.event_handler.join_room(self.token)

    def set_username(self, username):
        """
        From frontend's register?
        """
        self._username = username

    @property
    def username(self):
        return self._username

    @staticmethod
    def msg_validator(func):
        """
        Validate messages to avoid attacks
        """

        def wrap(self, msg):
            if (self.game.status.get("waiting_for_connection", True) and
                    self.game.status["ready_status"] == self.game.num_players):
                self._unicast("waiting_for_connection",
                              {"gamename": self.game.gamename})
                return
            if msg.get("token", "") == self.token:
                func(self, msg)

        return wrap

    def unicast(self, event, msg):
        """unicast wrapper."""
        return self._unicast(event, msg)

    def _unicast(self, event: str, msg: dict):
        """
        Send a message to the player represented by self

        messages are sent through a well-defined game via its
        event-handler module.
        """
        self.game.event_handler.emit(event, msg, to=[self.token])

    # rule-related methods

    def is_winner(self) -> bool:
        """
        Check whether hand contains all target with enough amount
        """
        return all(self.check_sufficiency(self.target).values())

    def check_sufficiency(self, items: dict) -> bool:
        """
        Check whether items is a subset of self.hand, with considering amount
        """
        # print(
        #     "BREAK EEEE", self.username, self.hand, self.game.hands,
        #     list([item, self.hand.get(item, 0),
        #           to_fraction(val)] for item, val in items.items()))
        items = lint_to_fullname(items)
        return dict((item, self.hand.get(item, 0) >= to_fraction(val)
                     and to_fraction(val) > 0) for item, val in items.items())

    def fuzzy_check_sufficiency(self, hand, items) -> bool:
        """
        Check sufficiency with considering tags. Result is also fuzzy
        as we did not solve the linear programming problem accurately.

        The use of this functions is just for reference, not strict.
        """
        items = lint_to_fullname(items)
        return all(
            self.count_item_tag(hand, self.game.craft_graph.node_dict.get(
                item)) >= to_fraction(val) and to_fraction(val) > 0
            for item, val in items.items())

    @staticmethod
    def count_item_tag(_resource: dict, _node: Node):
        """Count item/tag amount"""
        if _node is None:
            return 0
        if _node.node_type == "item":
            return _resource.get(_node.node_name, Fraction(0))
        return sum(
            _resource.get(k, 0) * to_fraction(v)
            for k, v in _node._children.items())

    def check_is_integer(self, items: dict) -> bool:
        """
        Check whether the items are of integer amounts.
        """

    def check_proposal_validity(self, proposal):
        """
        Check validity of proposal.
        1. partner exists
        2. self can give offer, use check_sufficiency
        3. partner can give request
        """
        partner_name = proposal.get("partner", "")
        self_name = proposal.get("self", "")
        print(proposal)
        if partner_name not in self.game.players or self_name != self.username:
            return False
        return (self.check_sufficiency(proposal.get("offer", {"_": 1})),
                self.game.players[partner_name].check_sufficiency(
                    proposal.get("request", {"_": 1})))

    def modify_local_hand(self, delta: dict, action="add"):
        """
        action: add or subtract
        delta: {item_name: [numerator, denominator]}
        """
        return self.combine_hand(self.hand, delta, action)

    # handle events, add codes below for events

    @msg_validator
    def on_submit_proposal(self, msg):
        """
        Determine whether porposal is legal and send to Game
        msg = {"token": token,
               "gamename": gamename,
               "proposal":{"self": username,
                           "partner": partner_name,
                           "offer":{},
                           "request":{}},
               "message":""}
        EMPTY offer and request may occur!
        """

        if self.game.status["waiting_for_proposal"] != self.username:
            msg.update({"incoming_event": "player__submit_proposal"})
            self._unicast("phase_error", msg)
            return
        proposal = process_proposal(msg.get("proposal", {}))
        if (p_self := proposal.get("self", None)) != self.username:
            msg.update({"errmsg": f"{p_self} is not your username!"})
            return self._unicast("proposal_invalid", msg)
        if (p_partner := proposal.get("partner",
                                      None)) not in self.game.players:
            msg.update({"errmsg": f"{p_partner} is not in game!"})
            return self._unicast("proposal_invalid", msg)

        validity = self.check_proposal_validity(proposal)
        if all(validity[0].values()) and all(validity[1].values()):
            partner_name = proposal.get("partner", "")
            self.game.broadcast("proposal_sent", {
                "gamename": self.game.gamename,
                "proposer": self.username,
            })
            self.game.players[partner_name].unicast(
                "proposal", {
                    "gamename": self.game.gamename,
                    "proposal": proposal,
                    "message": msg.get("message", "")
                })
            self.game.status["waiting_for_proposal"] = ""
            self.game.status["waiting_for_reply"] = partner_name
            self.game.current_proposal = proposal
        else:
            logger.warn("proposal_invalid", {
                "offer": validity[0],
                "request": validity[1]
            })
            print("validity:", msg, validity, s=1)
            msg.update(
                {"reason": {
                    "offer": validity[0],
                    "request": validity[1]
                }})
            self._unicast("proposal_invalid", msg)
            print("MESSAGE+++", msg, s=1)
        # print(f'on_submit_proposal: {msg}')

    @msg_validator
    def on_approval_or_reject(self, msg):
        """
        Approval / reject message
        msg = {"token":token,
               "gamename": gamename,
               "decision":"accept/reject",
               "message": "some sentences"}
        """
        if self.game.status["waiting_for_reply"] != self.username:
            msg.update({"incoming_event": "player__approval_or_reject"})
            self._unicast("phase_error", msg)
            return
        proposal = self.game.current_proposal
        decision = msg["decision"] in ["accept", "approve"]
        proposer = self.game.players[proposal["self"]]
        # send the replied message privately
        proposer.unicast(
            "proposal_reply_message", {
                "from": self.username,
                "to": proposer.username,
                "message": msg.get("message", "")
            })
        # sending the result publicly.
        if decision:
            self.game.broadcast(
                "proposal_accepted", {
                    "gamename": self.game.gamename,
                    "proposal": {
                        "self": proposal["self"],
                        "partner": proposal["partner"],
                        "offer": proposal["offer"],
                        "request": proposal["request"]
                    }
                })
            # self is receiver (partner), proposer is the giver "self"
            # so "offer" is added to self, and subtracted from proposer
            self.modify_local_hand(proposal["offer"])
            self.modify_local_hand(proposal["request"], "subtract")
            proposer.modify_local_hand(proposal["offer"], "subtract")
            proposer.modify_local_hand(proposal["request"])
            self.sync_hand_to_game()
            proposer.sync_hand_to_game()
            self.game.update_all_hands()
        else:
            self.game.broadcast("proposal_rejected", {
                "gamename": self.game.gamename,
                "proposer": proposer.username
            })
        self.game.status["waiting_for_reply"] = ""
        self.game.status["is_crafting"] = True

    @msg_validator
    def on_quit_game(self, msg):
        """
        Quit game and go back to Hall
        msg = {"token": token,
               "gamename": gamename,}

        Probably, we may add AI takeover mechanism?
        """
        if not self.game.status["is_over"]:
            # More fancy logic about quitting shall be added here!
            self.game.game_over("quit")

        self.game.remove_player(self.username)

    @msg_validator
    def on_craft_recipe_check(self, msg):
        """
        Check recipe validity

        msg = {"token": token,
               "gamename": gamename,
               "recipe": {"input":{}, "output":{}}
              }
        numbers are in list of format [numerator, denominator]
        """
        if not self.game.status.get("is_crafting", False):
            msg.update({"incoming_event": "player__craft_recipe_check"})
            self._unicast("phase_error", msg)
            return
        self.current_recipe = process_recipe(msg.get("recipe", {}))
        recipe_target = self.current_recipe["output"]
        recipe_input = self.current_recipe["input"]

        try:
            recipe_target = list(recipe_target.items())[0]
            print(recipe_input, recipe_target)
            result = self.game.craft_graph.validate_single_step_crafting(
                recipe_target, list(recipe_input.items()))
            code = 0
        except Exception as e:

            logger.exception(e)
            result = False
            code = 1

        code = 0 if result else 1
        if result:

            result_ = self.check_sufficiency(recipe_input)
            if not (result := all(result_.values())):
                logger.warn("Insufficient", result_)
                code = 2

        self._unicast("craft_recipe_validity", {
            "result": result,
            "gamename": self.game.gamename,
            "return_code": code
        })
        logger.info({
            "result": result,
            "gamename": self.game.gamename,
            "return_code": code
        })
        return {
            "result": result,
            "gamename": self.game.gamename,
            "return_code": code
        }

    @msg_validator
    def on_craft_recipe_apply(self, msg):
        """
        Apply a valid check.
        msg = {"token": token,
               "gamename": gamename,}
        """
        if not (self.game.status.get("is_crafting", False)
                and self.current_recipe):
            msg.update({"incoming_event": "player__craft_recipe_apply"})
            self._unicast("phase_error", msg)
            return
        recipe = self.current_recipe
        self.modify_local_hand(recipe["input"], "subtract")
        self.modify_local_hand(recipe["output"])
        self.sync_hand_to_client()
        self.current_recipe = {}

    @msg_validator
    def on_craft_done(self, msg):
        """
        Done with crafting and update the hands.
        msg = {"token": token}
        """
        if not self.game.status.get("is_crafting", False):
            msg.update({"incoming_event": "player__craft_done"})
            self._unicast("phase_error", msg)
            return

        self.game.status["crafting_done_status"] |= 2**self.action_id
        self.game.broadcast("player_craft_done", {
            "username": self.username,
            "gamename": self.game.gamename
        })
        self.discard_noninteger_hand()
        self.sync_hand_to_client()
        if self.game.status[
                "crafting_done_status"] == 2**self.game.num_players - 1:
            self.game.status["is_crafting"] = False
            self.game.status["crafting_done_status"] = 0
            self.game.sync_hand_from_player()
            self.game.update_all_hands()
            self.game.start_proposal()

    @msg_validator
    def on_ready_to_start(self, msg):
        """
        Done with crafting and update the hands.
        msg = {"token": token}
        """
        if self.game.status.get("is_started", True):
            msg.update({"incoming_event": "player__ready_to_start"})
            self._unicast("phase_error", msg)
            return
        print(self.game.status["ready_status"], s=4)
        self.game.status["ready_status"] += 1
        print(self.game.status["ready_status"], s=4)
        self.game.broadcast("player_ready_to_start", {
            "username": self.username,
            "gamename": self.game.gamename
        })
        if self.game.status["ready_status"] == self.game.num_players:
            self.game.start()

    @msg_validator
    def on_game_history_messages(self, msg):
        """
        Request for game history. Used in reconnection, such as
        refreshing browser accidentally or switch from one session / computer
        to another one and want to get all the history information from server.

        This is not an immediate need for game to move on, One may still be able to
        play based on the memory instead of checking the history from time to time.
        """
        history_messages = {
            "broadast": self.game.event_handler.history["@broadcast"],
            "unicast": self.game.event_handler.history[self.username]
        }
        self._unicast("game_history_messages", history_messages)

    def discard_noninteger_hand(self):
        """
        Modify hand to have integer items amounts.
        """
        keys = list(self.hand.keys())
        for key in keys:
            self.hand[key] = to_fraction(math.floor(
                self.hand[key]))  # round to int.
            if self.hand[key] == 0:
                self.hand.pop(key)

    def sync_hand_to_game(self):
        """
        Sync hand to game
        """
        self.game.hands[self.action_id] = deepcopy(self.hand)

    def sync_hand_to_client(self):
        """
        sync hand
        """
        self._unicast("private_hand_change", {
            "token": self.token,
            "gamename": self.game.gamename,
            "hand": self.hand
        })

    @msg_validator
    def on_possible_recipes_from_hand(self, msg):
        """
        Ask what could be crafted directly
        msg = `{gamename: gamename, token: token,
                hand:possibly other's hand?}`
        """
        hand = process_item_dict(msg.get("hand", self.hand))

        def hand_condition(key, val) -> bool:
            return key in hand

        def noitem_condition(node) -> bool:
            return node.node_type == "item" and node.node_name not in hand

        out_graph, _ = self.game.craft_graph.reversed_subgraph(
            hand_condition, ignore_condition=noitem_condition)
        possible_recipes = [
            node for node in out_graph.node_dict.values()
            if node.node_type == "recipe"
            and self.fuzzy_check_sufficiency(hand, node._children)
        ]
        self._unicast(
            "possible_recipes_from_hand", {
                "username":
                self.username,
                "gamename":
                self.game.gamename,
                "hand":
                hand,
                "recipes": [node.node_name for node in possible_recipes],
                "recipe_details": ([
                    self.translate_recipe_node(node)
                    for node in possible_recipes
                ] if not msg.get("is_browser", False) else [])
            })
        return {
            "username":
            self.username,
            "gamename":
            self.game.gamename,
            "hand":
            hand,
            "recipes": [{
                "input": node._children,
                "output": node._parents
            } for node in possible_recipes],
        }

    @staticmethod
    def translate_recipe_node(node):
        """Translate recipe into readable dict."""
        response = {"node_name": node.node_name, "node_type": node.node_type}
        parents = process_item_dict(node._parents)
        children = process_item_dict(node._children)
        response["parents"] = list(parents.items())
        response["children"] = list(children.items())
        response["extra_tags"] = {}
        for key, val in node.children.items():
            if key.node_type == "tag":
                response["extra_tags"][key.node_name] = process_item_dict(
                    key._children)

        return response

    @msg_validator
    def load_items_from_tag(self, msg):
        """
        Deal with request:

        ** crafting_node_nonredirect **

        """
        tag_name = msg.get("tag_name", "")

        node = self.game.craft_graph.node_dict.get(tag_name, "")
        if node == "":
            self._unicast(
                "load_items_from_tag", {
                    "username": self.username,
                    "gamename": self.game.gamename,
                    "tag_name": tag_name,
                    "is_valid": False
                })
            logger.warning("NODENAME NOT VALID")
            return 1
        response = {"username": self.username, "is_valid": True}
        response.update(self.translate_recipe_node(node))
        self._unicast(
            "load_items_from_tag", {
                "username": self.username,
                "gamename": self.game.gamename,
                "tag_name": tag_name,
                "is_valid": True,
                "node": response,
            })

        return 0

    @msg_validator
    def on_crafting_node(self, msg):
        """
        Now only used in items belonging to a tag
        """
        node_name = msg.get("node_name", "")

        node = self.game.craft_graph.node_dict.get(node_name, "")
        if node == "":
            self._unicast(
                "crafting_node", {
                    "username": self.username,
                    "gamename": self.game.gamename,
                    "node_name": node_name,
                    "is_valid": False
                })
            logger.warning("NODENAME NOT VALID")
            return 1
        response = {"username": self.username, "is_valid": True}
        response["node_name"] = node.node_name
        response["node_type"] = node.node_type
        node._children = process_item_dict(node._children)

        breadth = list(node.parents.items())
        response["parents"] = []
        while len(breadth) > 0:
            n, amount = breadth.pop()
            logger.info("BREADTH" + str(n))
            if n.node_type == "recipe":
                response["parents"] += [(n.node_name, to_fraction(amount))]
            elif n.node_type == "tag" and n.node_name[-4:] != "fuel":
                breadth += list(n.parents.items())
            else:
                pass
        response["children"] = list(node._children.items())

        self._unicast(
            "crafting_node", {
                "username": self.username,
                "gamename": self.game.gamename,
                "node_name": node_name,
                "is_valid": True,
                "node": response,
            })

        return 0

    @msg_validator
    def on_crafting_node_nonredirect(self, msg):
        """
        Deal with request:

        ** crafting_node_nonredirect **

        """
        print(
            f'\n=========>>>{msg["node_name"]}\n{msg["token"]}\n{msg["gamename"]}'
        )

        node_name = msg.get("node_name", "")
        direct_result = self._get_item_info(msg)
        if len(direct_result) == 0:
            self._unicast(
                "crafting_node_nonredirect", {
                    "username": self.username,
                    "gamename": self.game.gamename,
                    "node_name": node_name,
                    "is_valid": False
                })
            logger.warning("NODENAME NOT VALID")
            return 1

        response = {"username": self.username, "is_valid": True}
        response.update(direct_result)
        self._unicast(
            "crafting_node_nonredirect", {
                "username": self.username,
                "is_valid": True,
                "node_name": node_name,
                "node": response,
                "amount": to_fraction(msg.get("amount", 1)),
            })

        return 0

    def _get_item_info(self, msg):
        """
        Get item info, as input or output.
        """

        node_name = msg.get("node_name", "")
        node_name = lint_to_fullname(node_name)
        node = self.game.craft_graph.node_dict.get(node_name, "")
        if node == "":
            return {}
        return self.translate_recipe_node(node)

        # response = {}
        # response["node_name"] = node.node_name
        # response["node_type"] = node.node_type
        # response["parents"] = deepcopy(node._parents)
        # response["children"] = deepcopy(node._children)
        # process_item_dict(response["children"])
        # process_item_dict(response["parents"])
        # response["parents"] = list(response["parents"].items())
        # response["children"] = list(response["children"].items())
        # return response

    @msg_validator
    def on_item_info(self, msg):
        """
        Deal with request:

        ** crafting_node_nonredirect **

        msg = {"node_name": item_name, "amount": amount}
        """
        print(f'===>\n{msg.get("node_name")}', s=26)
        reason = ""
        try:
            node_name = msg["node_name"]
        except KeyError:
            reason = "KeyError: `node_name` is required in query."
            logger.warn(reason)
            node_name = ""
        direct_result = self._get_item_info(msg)
        if len(direct_result) == 0:
            self._unicast(
                "item_info", {
                    "username": self.username,
                    "gamename": self.game.gamename,
                    "node_name": node_name,
                    "reason": reason
                    if reason else f"`{node_name}` is not a valid item name.",
                    "is_valid": False
                })
            logger.warning("NODENAME NOT VALID")
            return 1

        response = {"username": self.username, "is_valid": True}
        response.update(direct_result)
        parents = []
        children = []
        for name, amt in response["parents"]:
            res = self._get_item_info({"node_name": name, "amount": amt})
            parents += [res] if res else []
        for name, amt in response["children"]:
            res = self._get_item_info({"node_name": name, "amount": amt})
            children += [res] if res else []

        response["parents"] = parents
        response["children"] = children

        self._unicast(
            "item_info", {
                "username": self.username,
                "is_valid": True,
                "node_name": node_name,
                "node": response,
                "amount": to_fraction(msg.get("amount", 1)),
            })

        return 0

    @msg_validator
    def on_crafting_item_list(self, msg):
        self._unicast(
            "crafting_item_list", {
                "game":
                self.gamename,
                "crafting_item_list": [
                    k for k, v in self.craft_graph.node_dict.items()
                    if v.node_type == "item"
                ]
            })

    @msg_validator
    def on_gym_observation(self, msg):
        self.unicast(
            "gym_observation", {
                "hands": self.game.hands,
                "player_list": [x.username for x in self.game.action_queue],
                "target": self.target
            })


# DUMMY_PLAYER = Player(DUMMY_MESSAGE_HANDLER)
