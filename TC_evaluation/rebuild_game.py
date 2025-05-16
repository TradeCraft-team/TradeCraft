import json
import os
from utils_eval import *



def rebuild_game_info(file_path = "data/recordings/TradeCraft.gongying1.json"):
    json_record = load_json(file_path)
    basic_info_dic = extract_basic_info_dic(json_record)

    game_turns_info = {}
    turns = 0
    flag_unsolved_proposal = None
    flag_unsolved_validity = None

    for key in json_record:
        event = key['event']
        if event == "player__submit_proposal":
            turns += 1
            if turns not in game_turns_info:
                game_turns_info[turns] = []

            # record proposal info
            description = f"{key['msg']['proposal']['self']} submit a proposal to {key['msg']['proposal']['partner']}, request {parse_crafts(key['msg']['proposal']['request'])}, offer {parse_crafts(key['msg']['proposal']['offer'])} together with a text message: {key['msg']['message']}"
            actor = key['msg']['proposal']['self']
            event = "player__submit_proposal"
            recordings = {'description': description, 'actor': actor, 'event': event, 'current_hand': basic_info_dic[actor]['current_hand']}
            game_turns_info[turns].append(recordings)
            flag_unsolved_proposal = key['msg']['proposal']

        
        elif event == "player__approval_or_reject":
            # record approval or reject info
            if not flag_unsolved_proposal:
                raise ValueError("No proposal to approve or reject")
            else:
                proposer = flag_unsolved_proposal['self']
                recepter = flag_unsolved_proposal['partner']
                decision = key['msg']['decision']
                text_message = key['msg']['message']

                description = f"{recepter} decided to {decision} the proposal from {proposer} with a text message: {text_message}"
                actor = recepter
                event = "player__approval_or_reject"
                recordings = {'description': description, 'actor': actor, 'event': event, 'current_hand': basic_info_dic[actor]['current_hand']}
                game_turns_info[turns].append(recordings)
                flag_unsolved_proposal = None
                              
        elif event == "server__craft_recipe_validity":
            flag_unsolved_validity = key['msg']['result']

        elif event == "player__craft_done":
            username = from_domain_to_username(basic_info_dic, key['domain'])
            recordings = {'description': f"{username} has finished crafting", 'actor': username, 'event': event, 'current_hand': basic_info_dic[username]['current_hand']}
            game_turns_info[turns].append(recordings)

        elif event == "player__craft_recipe_check":
            # record craft recipe check info
            if flag_unsolved_validity is None:
                raise ValueError("No recipe validity check")
            else:
                actor = get_username_from_domain(basic_info_dic, key['domain'])
                description = f"{actor} check the validity of the recipe: Input {parse_crafts(key['msg']['recipe']['input'])}, Output {parse_crafts(key['msg']['recipe']['output'])}, the recipe is {'valid' if flag_unsolved_validity else 'invalid'}"
                if flag_unsolved_validity:
                    last_description =  f"{actor} apply the recipe: Input {parse_crafts(key['msg']['recipe']['input'])}, Output {parse_crafts(key['msg']['recipe']['output'])}"
                    last_actor = actor

                event = "player__craft_recipe_check"
                recordings = {'description': description, 'actor': actor, 'event': event, 'current_hand': basic_info_dic[actor]['current_hand']}
                game_turns_info[turns].append(recordings)
                       
        elif event == "player__craft_recipe_apply":
            actor = get_username_from_domain(basic_info_dic, key['domain'])
            if last_actor == actor:
                description = last_description
                print("test",description)
                event = "player__craft_recipe_apply"
                recordings = {'description': description, 'actor': actor, 'event': event, 'current_hand': basic_info_dic[actor]['current_hand']}
                game_turns_info[turns].append(recordings)
   
        elif event == "server__private_hand_change":
            username = from_domain_to_username(basic_info_dic, key['domain'])
            basic_info_dic[username]['current_hand'] = parse_crafts(key['msg']['hand'])


        elif event == "server__update_all_hands": 
            player_list, hands = key['msg']['player_list'], key['msg']['hands']
            for player, hand in zip(player_list, hands):
                hand_parsed = parse_crafts(hand)
                basic_info_dic[player]['current_hand'] = hand_parsed

        elif event == "server__game_over":
            turns = "Game Over"
            game_turns_info[turns] = []
            for user in key['msg']['win-status']:
                result = "win" if basic_info_dic[user]['win-status'] else "lose"
                recordings = {
                    "description": f"Game over, I {result}",
                    "actor": user,
                    "event": "server__game_over",
                    "current_hand": basic_info_dic[user]['current_hand']
                }
                game_turns_info[turns].append(recordings)

    return game_turns_info, basic_info_dic


def extract_basic_info_dic(json_record):
    info_dic = {}

    initial_info = False
    for key in json_record:
        key['msg'] = json.loads(key['msg'])
        # Load Targets
        if key['event'] == "server__private_start_info":
            info_dic[key['msg']['username']]['target'] = key['msg']['target']
            info_dic[key['msg']['username']]['domain'] = key['domain']

           
        # Load Initial Hand
        elif key['event'] == "server__game_start":
            initial_info = True
        elif key['event'] == "server__update_all_hands":
            if initial_info:
                for player, hand in zip(key['msg']['player_list'], key['msg']['hands']):
                    hand_parsed = parse_crafts(hand)
                    if player not in info_dic:
                        info_dic[player] = {'initial_hand': hand_parsed, 'current_hand': hand_parsed}
                    else:
                        info_dic[player]['initial_hand'] = hand_parsed
                        info_dic[player]['current_hand'] = hand_parsed
                initial_info = False
        elif key['event'] == "server__game_over":
            for user in key['msg']['win-status']:
                info_dic[user]['win-status'] = key['msg']['win-status'][user]

    return info_dic
            
 


if __name__ == "__main__":
    game_turns_info, basic_info_dic = rebuild_game_info()
    for user in basic_info_dic:
        print(f"User: {user}")
        print(f"Initial Hand: {basic_info_dic[user]['initial_hand']}")
      
    print('\n')
    for turn in game_turns_info:
        print(f"=====================Round {turn}=====================")
        for record in game_turns_info[turn]:
            print(f"[{record['actor']}]: {record['description']}")
            print(f"({record['actor']}) Current Hand: {record['current_hand']}")