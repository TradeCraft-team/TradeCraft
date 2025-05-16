import json
import os



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


def parse_crafts(craft_dic):
    sentence = "["

    for key, value in craft_dic.items():
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