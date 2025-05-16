import json
import os
import math
from fractions import Fraction



def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def check_path(target_path):
    if not os.path.exists(target_path):
        os.makedirs(target_path)



def get_target(message, username):
    for msg in message:
        if msg['event'] == "server__private_start_info":
            if msg['msg']['username'] == username:
                return msg['msg']['target']
    return None

def to_fraction(p: list | dict | int | Fraction | str):
    """
    from pair to fraction
    len(p)==2
    """
    match p:
        case [int(n), int(d)]:
            return Fraction(n, d)
        case [float(n), float(d)] | [float(n), int(d)] | [int(n), float(d)]:
            return Fraction(n).limit_denominator(10000) / Fraction(
                d).limit_denominator(10000)
        case {"n": n, "d": d}:
            return Fraction(n, d)
        case int(s):
            return Fraction(s)
        case float(s):
            return Fraction(s).limit_denominator(10000)
        case str(s):
            try:
                num = [float(x.strip()) for x in s.split("/")]
                num = num[:2] if len(num) >= 2 else num[0]
                return to_fraction(num)
            except Exception as e:
                print(e)
            return -1
        case _:
            return p

def parse_crafts(craft_dic):
    sentence = "["

    for key, value in craft_dic.items():
        if isinstance(value, int):
            value = {"n": value, "d": 1}
        
        if value['n'] >= value['d']:
            num = value['n'] // value['d']
            
        else:
            num =  f"{value['n']}/{value['d']}"
        sentence += f"{num} * {key[10:]}, "
    

    return sentence[:-2] + "]"


def get_username_from_domain(dict, domain):
    for username in dict:
        if dict[username]['domain'] == domain:
            return username
    raise ValueError("No such domain in the dict")



def from_domain_to_username(basic_info_dic, domain):
    for username in basic_info_dic:
        if basic_info_dic[username]['domain'] == domain:
            return username
    raise ValueError("No such user in the dict")


def from_recordings_to_prompt(game_turns_info, basic_info_dic):
    prompts = "Now you will see the recordings of the game:\n"
    for turn in game_turns_info:
        prompts += f"=====================Round {turn}=====================\n"
        for record in game_turns_info[turn]:
            prompts += f"  [{record['actor']}]\n his/her current hand crafts are {record['current_hand']}, decide to take {record['description']}\n"
    return prompts


def get_total_steps(game_turns_info, username):
    steps = 0
    for turn in game_turns_info:
        for record in game_turns_info[turn]:
            if record['actor'] == username:
                steps += 1
    return steps