"""
tradeCraft language processor
"""

import os
import math
import json
import jinja2
from pathlib import Path
from typing import Any
from ...agent_proxy.base_proxied_game import BaseLanguageProcessor

THIS_PATH = Path(__file__).parent


class BasicTCLanguageProcessor(BaseLanguageProcessor):
    """
    Language Processor for tradeCraft, basic version
    """

    def __init__(self, *args, template_path: str = None, **kwargs):
        """
        Initialize.
        """
        super().__init__(*args, **kwargs)
        self.template_path = (template_path if template_path is not None else
                              THIS_PATH / "prompts" / "basic")
        self.get_templates(self.template_path)
        self.user_name = None

    def get_templates(self, path: str = None):
        """
        """
        path = path if path is not None else THIS_PATH / "prompts" / "basic"
        files = [
            fname for fname in list(os.walk(path))[0][2]
            if fname[-4:] == ".txt"
        ]

        self.prompt_templates = dict(
            (fname[:-4], self.load_prompt_template(path / fname))
            for fname in files)

    def load_prompt_template(self, filename: str) -> str:
        """

        """
        with open(filename, "r", encoding="utf8") as fptr:
            return fptr.read()

    # @BaseLanguageProcessor.log_output_to_db
    def generate_prompt(self, event: str, **kwargs):
        """
        
        """
        prompt = ""
        unread_msgs = kwargs.get("unread_msgs", [])
        read_msgs = kwargs.get("read_msgs", [])

        # prompt += "[The following are unread messages]\n"
        for msg in unread_msgs:
            print("msggggggggggg",msg)
            prompt += self.parse_msg(msg) + "\n"

        if not kwargs.get("show_history", False):
            return prompt

        # prompt += "[The following are overall messages]\n"

        for msg_list in read_msgs:
            for msg in msg_list:
                prompt += self.parse_msg(msg) + "\n"

        return prompt

    def parse_msg(self, packet):
        """
        """
        event, message = packet
        # print("what_type",packet)
        # print("from_source",message)
        match event:
            case "server__private_start_info":
                target = message.get("target")
                # 这里只兼容一个目标，遇到后续多个目标会出现报错
                cnt = 0
                for key in target:
                    item = key
                    num = int(target[key]['d'] / target[key]['n'])
                    cnt += 1
                if cnt > 1:
                    raise NotImplementedError("此功能尚未实现")

                return jinja2.Template(
                    self.prompt_templates["server__private_start_info"]
                ).render(message=message, item=item, num=num)

            case "server__start_proposal":
                proposer = "your" if message[
                    'proposer'] == self.user_name else message[
                        'proposer'] + '\'s'
                return jinja2.Template(
                    self.prompt_templates["server__start_proposal"]).render(
                        proposer=proposer,
                        turn_index=message["turn_index"],
                        max_turn=message["max_turn"])

            case "server__proposal_sent":
                return jinja2.Template(
                    self.prompt_templates["server__proposal_sent"]).render(
                        message=message)

            case "server__proposal":
                proposal = message.get("proposal")

                msg = message.get("message", "")
                return jinja2.Template(
                    self.prompt_templates['server__proposal']).render(
                        proposal=proposal, message=msg)

            case "server__proposal_accepted":
                proposer = 'you' if message['proposal'][
                    'self'] == self.user_name else message['proposal']['self']
                reciever = 'you' if message['proposal'][
                    'partner'] == self.user_name else message['proposal'][
                        'partner']

                return jinja2.Template(
                    self.prompt_templates["server__proposal_accepted"]).render(
                        proposer=proposer, reciever=reciever)

            case "server__proposal_rejected":
                proposer = 'Your' if message[
                    'proposer'] == self.user_name else message[
                        'proposer'] + '\'s'
                return jinja2.Template(
                    self.prompt_templates["server__proposal_rejected"]).render(
                        proposer=proposer)

            case "server__proposal_reply_message":
                proposer = 'you' if message[
                    'from'] == self.user_name else message['from']
                reciever = 'you' if message[
                    'to'] == self.user_name else message['to']

                return jinja2.Template(
                    self.prompt_templates["server__proposal_reply_message"]
                ).render(message=message, proposer=proposer, reciever=reciever)

            case "server__possible_recipes_from_hand":
                return jinja2.Template(
                    self.prompt_templates["server__possible_recipes_from_hand"]
                ).render(message=message,
                         recipe_details=message.get("recipe_details", []))

            case "server__player_craft_done":
                return jinja2.Template(
                    self.prompt_templates["server__player_craft_done"]).render(
                        event=event, message=message)

            case "server__update_all_hands":
                player_list = message["player_list"]
                hands_info = message["hands"]
                # parsed_msg = "## update_all_hands:\n"
                # for player, hand_card in zip(player_list, hands_info):
                #     parsed_msg += jinja2.Template(
                #         self.prompt_templates["server__update_all_hands"]
                #     ).render(player=player, hand_card=hand_card)
                # return parsed_msg
                change_list = [
                    (player, hand_card)
                    for player, hand_card in zip(player_list, hands_info)
                ]

                return jinja2.Template(
                    self.prompt_templates["server__update_all_hands"]).render(
                        change_list=change_list)

            case "server__private_hand_change":
                return jinja2.Template(
                    self.prompt_templates["server__private_hand_change"]
                ).render(message=message)

            case "server__item_info":
                assert isinstance(message, dict)
                if 'node' not in message:
                    # if the item_info request is not properly asked.
                    return jinja2.Template(
                        self.prompt_templates["server__item_info_invalid"]
                    ).render(node_name=message["node_name"])

                tags_dict = {}
                extra_tags = {}

                children = self._parse_recipe_nodes(
                    message['node'].get('children', []), tags_dict, extra_tags)
                parents = self._parse_recipe_nodes(
                    message['node'].get('parents', []), tags_dict, extra_tags)

                if message['amount']['n'] % message['amount']['d'] == 0:
                    amount = str(message['amount']['n'] //
                                 message['amount']['d'])
                else:
                    amount = f"{message['amount']['n']}/{message['amount']['d']}"

                tags_prompt = {}
                for tag, multiplier in tags_dict.items():
                    assert tag in extra_tags
                    for item, amount in extra_tags[tag].items():
                        if tag not in tags_prompt:
                            tags_prompt[tag] = {}
                        assert item not in tags_prompt
                        item = item.split(':')[-1]
                        tags_prompt[tag][item] = self._normalize_amount(
                            self._multiply_fractions(amount, multiplier))

                return jinja2.Template(
                    self.prompt_templates["server__item_info"]).render(
                        item_name=message['node_name'],
                        is_valid=message['is_valid'],
                        amount=amount,
                        children=children,
                        parents=parents,
                        tags_prompt=tags_prompt)
            case "server__proposal_invalid":
                err_msg = message.get("errmsg")

                if err_msg is not None:
                    if "your" in err_msg:
                        err_msg = "Your username is not 'your_username," + f" it should be **{self.user_name}**!"

                    else:
                        err_msg = f"You got your partner's name wrong. {err_msg}"

                reason = message.get("reason", {})
                offer_list = reason.get("offer", {})
                request_list = reason.get("request", {})

                offer_false_list = [
                    key for key in offer_list if not offer_list[key]
                ]
                request_false_list = [
                    key for key in request_list if not request_list[key]
                ]
                print("debug_none_type_message", message)
                print("debug_none_type_offer", offer_false_list)
                print("debug_none_type_re", request_false_list)
                print("debug_none_type_err", err_msg)
                return jinja2.Template(
                    self.prompt_templates["server__proposal_invalid"]).render(
                        message=message,
                        offer_false_list=offer_false_list,
                        request_false_list=request_false_list,
                        err_msg=err_msg or [])

            case "server__craft_recipe_validity":
                return jinja2.Template(
                    self.prompt_templates["server__craft_recipe_validity"]
                ).render(message=message)

            case "server__phase_error":
                return jinja2.Template(
                    self.prompt_templates["server__phase_error"]).render(
                        event=event, message=message)

            case "server__game_over":
                win_state = message.get("win-status", {})
                targets = message.get("targets", [])
                action_queue = message.get("action_queue", [])
                assert len(action_queue) == len(targets)
                winners = {}
                losers = {}
                for player, target in zip(action_queue, targets):
                    if win_state[player]:
                        winners[player] = target
                    else:
                        losers[player] = target

                return jinja2.Template(
                    self.prompt_templates["server__game_over"]).render(
                        message=message, winners=winners, losers=losers)

            case _:
                return jinja2.Template(
                    self.prompt_templates["default"]).render(
                        event=event, message=str(message))

    # @BaseLanguageProcessor.log_input_to_db
    def parse_answer(self, answer: Any, event: str = None, **kwargs) -> dict:
        """
        """
        match event:
            case "player__item_info":
                return {"node_name": answer}

            case "player__check_event_history":
                return jinja2.Template(
                    self.prompt_templates["player__check_event_history"]
                ).render(event=event,
                         message=str(kwargs.get("message", "Empty History")))

            case _:
                return super().parse_answer(answer, event, **kwargs)

    def _parse_hands(self, hands_info: dict) -> str:
        '''
        process the hands_info to the format of 'item*amount, item*amount, ...'
        fixme: json like dict will be better ?
        '''
        parsed_hands = {}
        for key, value in hands_info.items():
            item_name = key[10:]  # Remove 'minecraft:' prefix
            if isinstance(value, dict) and 'n' in value and 'd' in value:
                if value["n"] % value["d"] == 0:
                    amount = value["n"] // value["d"]
                else:
                    amount = {"n": value["n"], "d": value["d"]}
            elif isinstance(value, (int, float)):
                amount = int(value)
            else:
                amount = value  # Keep original value if it's not a number or fraction
            parsed_hands[item_name] = amount
        return json.dumps(parsed_hands)

    def _normalize_amount(self, amount):
        if isinstance(amount, dict):
            if amount['n'] % amount['d'] == 0:
                amount = str(amount['n'] // amount['d'])
            else:
                amount = f"{amount['n']}/{amount['d']}"

        elif isinstance(amount, int):
            amount = str(amount)
        elif isinstance(amount, (list, tuple)):
            if amount[0] % amount[1] == 0:
                amount = str(amount[0] // amount[1])
            else:
                amount = f"{amount[0]}/{amount[1]}"
        return amount

    def _parse_item_and_amount(self, item, amount):
        if item.startswith('minecraft:') or item.startswith('#minecraft:'):
            item = item.split(':')[1]
        amount = self._normalize_amount(amount)
        return item, amount

    def _parse_recipe(self, recipe_info: dict) -> str:
        # {'input': {'minecraft:iron_ingot': [...]}, 'output': {'minecraft:bucket': [...]}}
        recipe_cpy = dict()
        recipe_cpy['input'] = dict()
        recipe_cpy['output'] = dict()

        for io_type in ['input', 'output']:
            for item, amount in recipe_info[io_type].items():
                parsed_item, parsed_amount = self._parse_item_and_amount(
                    item, amount)
                recipe_cpy[io_type][parsed_item] = parsed_amount
        return json.dumps(recipe_cpy)

    def _parse_recipe_nodes(self, recipe_nodes: list, tags_dict: dict,
                            extra_tags: dict) -> str:
        result = []
        for node in recipe_nodes:
            node_name, node_type, recipe_details = self._parse_recipe_node(
                node, tags_dict, extra_tags)
            # result.append(f"{node_name} ({node_type}): {recipe_details}")
            result.append(f"{recipe_details}")
        return result

    def _multiply_fractions(self, amount, multiplier):
        assert isinstance(
            amount, dict
        ) and 'n' in amount and 'd' in amount, f"Amount {amount} is not a valid fraction"
        assert isinstance(
            multiplier, dict
        ) and 'n' in multiplier and 'd' in multiplier, f"Multiplier {multiplier} is not a valid fraction"
        # amount * multiplier
        amount['n'] *= multiplier['n']
        amount['d'] *= multiplier['d']
        gcd = math.gcd(amount['n'], amount['d'])
        amount['n'] //= gcd
        amount['d'] //= gcd
        return amount

    def _parse_recipe_node(self, recipe_node: dict, tags_dict: dict,
                           extra_tags: dict) -> str:

        def process_ingredients(ingredients):
            result = {}
            for ingredient, amount in ingredients:
                if ingredient.startswith('#'):
                    tags_dict[ingredient] = amount
                    _item, _amount = self._parse_item_and_amount(
                        ingredient, amount)
                    result['#' + _item] = _amount
                else:
                    _item, _amount = self._parse_item_and_amount(
                        ingredient, amount)
                    result[_item] = _amount
            return result

        node_name = recipe_node['node_name'].strip('#$')
        node_type = recipe_node['node_type']
        recipe_details = {}
        recipe_details['input'] = {}
        recipe_details['output'] = {}

        if node_type == 'recipe':
            extra_tags.update(recipe_node.get('extra_tags', {}))
            recipe_details['input'] = process_ingredients(
                recipe_node.get('children', []))
            recipe_details['output'] = process_ingredients(
                recipe_node.get('parents', []))
        else:
            print(f"Unprocessed node type: {node_type}")
        return node_name, node_type, json.dumps(recipe_details)

    def game_intro(self, winding_target='default'):
        """
        Return game_intro
        """

        intro_text = self.load_prompt_template(THIS_PATH / "prompts" /
                                               "game_init_bi.txt")

        winning_text = self.load_prompt_template(
            THIS_PATH / "prompts" / "game_goals" / f"{winding_target}.txt")

        # return self.load_prompt_template(THIS_PATH / "prompts" /
        #                                  "game_init.txt")
        return intro_text + '\n' + winning_text
