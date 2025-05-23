import json
import os
from utils_eval import *
from datetime import datetime
from tqdm import tqdm
import json
import re

NEEDLESS_EVENTS = [
    "server__game_start", 
    "server__player_enter_room", 
    "player__ready_to_start", 
    "server__player_ready_to_start", 
    "server__crafting_item_list", 
    "server__item_info", 
    "server__player_leave_room", 
    "server__game_deleted", 
    "server__player_craft_done", 
    "server__proposal", 
    "server__proposal_sent", 
    "server__proposal_rejected", 
    "server__proposal_accepted", 
    "server__proposal_reply_message", 
]


players_dics = {
        'un_vs_coo':
        {
            'gemini_undefine':"Player 1", 
            'gemini_cooperative':"Player 2"
        
        },
        'com_vs_un':
        {
            'gemini_undefine':"Player 1", 
            'gemini_competitive': "Player 2"
        },
        'com_vs_coo':
        {
            'gemini_cooperative':'player 1', 
            'gemini_competitive':'player 2'
            
        }, 
        'coo1_vs_coo2':
        {
        'gemini_cooperative1': 'Player 1', 
        'gemini_cooperative2': 'Player 2'
        },
        'com1_vs_com2':
        {
        'gemini_competitive1': 'Player 1', 
        'gemini_competitive2': 'Player 2'
        },
        'coo1_vs_coo2':
        {
        'gemini_cooperative1': 'Player 1', 
        'gemini_cooperative2': 'Player 2'
        }, 
        'un1_vs_un2':
        {
        'gemini1': 'Player 1', 
        'gemini2': 'Player 2'
        },
        'ge_vs_4o':
        {
        'gemini': 'Player 1 ',
        'gpt-4o': 'Player 2 '
        }, 
        'ge_vs_cl':
        {
        'gemini': 'Player 1',
        'claude': 'Player 2'
        },
        '4o_vs_cl':
        {
        'gpt-4o': 'Player 1 ',
        'claude': 'Player 2 '
        }
    }


def compute_md_token_stats(folder_path, model="gpt-4"):
    token_stats = []  # 存储 (filename, token_count)

    for fname in os.listdir(folder_path):
        if not fname.endswith(".md"):
            continue

        fpath = os.path.join(folder_path, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = count_tokens(content, model=model)
            token_stats.append((fname, tokens))
        except Exception as e:
            print(f"⚠️ Failed to read {fname}: {e}")

    if not token_stats:
        print("❌ No .md files found.")
        return

    total_files = len(token_stats)
    total_tokens = sum(t for _, t in token_stats)
    avg_tokens = total_tokens / total_files

    max_file, max_tokens = max(token_stats, key=lambda x: x[1])
    min_file, min_tokens = min(token_stats, key=lambda x: x[1])

    print(f"\n✅ Processed {total_files} .md files (model = {model})")
    print(f"📊 Average token count: {avg_tokens:.2f}")
    print(f"🔺 Max token count: {max_tokens} in file `{max_file}`")
    print(f"🔻 Min token count: {min_tokens} in file `{min_file}`")

    return {
        "avg_tokens": avg_tokens,
        "max_tokens": max_tokens,
        "max_file": max_file,
        "min_tokens": min_tokens,
        "min_file": min_file,
        "all_stats": token_stats,
    }


def match_case(word, template):
    """根据 template 的大小写格式转换 word"""
    if template.isupper():
        return word.upper()
    elif template.islower():
        return word.lower()
    elif template[0].isupper():
        return word.capitalize()
    else:
        return word



def parse_item_info(dic, basic_info_dic=None):
    """
    根据 event 类型解析单条记录的语义信息。
    
    参数：
        dic: 单条记录字典，含有 'event'、'msg'、'domain' 等字段
        basic_info_dic: 可选，记录玩家当前手牌，若未传则 current_hand 返回为 None

    返回：
        一个 dict，包含 description, actor, event, current_hand 字段
    """
    event = dic['event']
    msg = json.loads(dic['msg'])
    domain = dic.get('domain', None)
    
    # 默认 current_hand 为 None，除非传入 basic_info_dic
    def get_hand(actor):
        return basic_info_dic[actor]['current_hand'] if basic_info_dic else None

    if event == "player__submit_proposal":
        actor = msg['proposal']['self']
        partner = msg['proposal']['partner']
        request = parse_crafts(msg['proposal']['request'], mode="proposal")
        offer = parse_crafts(msg['proposal']['offer'], mode="proposal")
        message = msg['message']
        description = f"{actor} submit a proposal to {partner}, request {request}, offer {offer} together with a text message: {message}"
        return {'description': description, 'actor': actor, 'event': event, 'current_hand': get_hand(actor)}

    elif event == "player__approval_or_reject":
        recepter = msg.get('username', '?')  # fallback
        decision = msg['decision']
        message = msg['message']
        description = f"{recepter} decided to {decision} the proposal with a text message: {message}"
        return {'description': description, 'actor': recepter, 'event': event, 'current_hand': get_hand(recepter)}

    elif event == "player__craft_done":
        actor = msg['username']
        description = f"{actor} has finished crafting"
        return {'description': description, 'actor': actor, 'event': event, 'current_hand': get_hand(actor)}

    elif event == "player__craft_recipe_check":
        actor = msg['username']
        try:
            recipe_in = parse_crafts(msg['recipe']['input'], mode = "recipe_check")
            recipe_out = parse_crafts(msg['recipe']['output'], mode = "recipe_check")
        except:
            recipe_in = f"[Nothing]"
            recipe_out = f"[Nothing]"
        validity = msg.get('result', None)  # fallback true
        description = f"{actor} check the validity of the recipe: Input {recipe_in}, Output {recipe_out}, the recipe is {'valid' if validity else 'invalid'}"
        return {'description': description, 'actor': actor, 'event': event, 'current_hand': get_hand(actor)}

    elif event == "server__private_hand_change":
        hands = parse_crafts(msg['hand'])            
        description = f"Currently, his/her hand crafts change to: {hands}"
        return {'description': description, 'actor': "", 'event': event, 'current_hand': ""}


    elif event == "player__craft_recipe_apply":
        actor = msg['username']
        description = f"{actor} apply the recipe he/she has checked before."
        return {'description': description, 'actor': actor, 'event': event, 'current_hand': get_hand(actor)}

    elif event == "server__game_over":
        actor_pool = msg['action_queue']
        targets_pool = msg['targets']
        win_status_pool = msg['win-status']
        description = f"Game over, the results is: \n"
        for actor, target in zip(actor_pool, targets_pool):
            description += f"**{actor}** [{'win' if win_status_pool[actor]  else 'lose'}] the game, his/her private target is: {parse_crafts(target)}. \n"

        return {'description': description, 'actor': actor, 'event': event, 'current_hand': get_hand(actor)}

    # 处理 server__private_start_info 事件
    elif event == "server__private_start_info":
        def get_hand(actor):
            return basic_info_dic[actor]['current_hand'] if basic_info_dic else None
        username = msg.get("username", "?")
        target = msg.get("target", {})
        if isinstance(target, dict):
            target_str = parse_crafts(target)  # 使用已有的 parse_crafts 函数格式化
        else:
            target_str = str(target)

        description = f"{username} enters the game with a private target: {target_str}"
        return {
            'description': description,
            'actor': username,
            'event': event,
            'current_hand': get_hand(username),
        }
    elif event == "player__possible_recipes_from_hand":
        actor = msg['username']
        description = f"{actor} is checking the posssible recipes from his/her hand crafts."
        return {
            'description': description,
            'actor': actor,
            'event': event,
            'current_hand': "",
        }
    elif event == "server__craft_recipe_validity":
        result = msg.get('result')
        return_code = msg.get('return_code')
        
        if result:
            extra_info = "Great! Your recipe is **correct and feasible**!"
        elif return_code == 1:
            extra_info = (
                "Sorry, there seems to be an issue with your recipe. Please check:\n"
                "1. The recipe follows Minecraft game rules.\n"
                "2. You have the required crafts in the necessary quantities.\n\n"
                "You should use the `possible_recipes_from_hand` tool to see all available recipes at this stage."
            )
        elif return_code == 2:
            extra_info = (
                "Sorry, your recipe follows the rules, but it’s still unfeasible with your current crafts.\n"
                "You should use the `possible_recipes_from_hand` tool to see all available recipes at this stage."
            )
        else:
            extra_info = "The server did not provide a detailed explanation."

        description = (
            f"Server shows that the recipe is **{'valid' if result else 'invalid'}** attached with a detailed explanation:\n"
            f"{extra_info}"
        )

        return {
            'description': description,
            'actor': None,
            'event': event,
            'current_hand': "",
        }
    elif event == 'server__proposal_invalid':
        # print(msg.keys())
        actor = msg['username']
        description = f"{actor}'s proposal is INVALID according to the game rule."
        
        return {
            'description': description,
            'actor': None,
            'event': event,
            'current_hand': "",
        }


    elif event == 'player__item_info':
        # print(msg)
        actor = msg.get("username", '?')
        craft = msg.get("node_name", '?')
        description = f"{actor} checked the item info of craft: **{craft[10:]}**. "
        return {
            'description': description, 
            'actor': actor,
            'event': event,
            'current_hand': None,
        }

    elif event == "server__update_all_hands":
        players = msg.get("player_list", [])
        hands = msg.get("hands", [])
        if len(players) != len(hands):
            description = "Mismatched hand info"
        else:
            descriptions = []
            for player, hand_raw in zip(players, hands):
                hand_str = parse_crafts(hand_raw)
                descriptions.append(f"{player} hand: {hand_str}")
            description = "Server updated all hands:\n" + "\n".join(descriptions)
        
        return {
            'description': description,
            'actor': "server",
            'event': event,
            'current_hand': None,
            'item': dic
        }

    elif event == "server__possible_recipes_from_hand":
        recipes = msg['recipes']
        actor = msg['username']
        description = f"Server shows the possible recipes of {actor} with his/her current hand crafts are: \n"
        for recipe in recipes:
            description += f"   - {recipe[1:].replace('_', ' ')}"
            description += '\n'
        return {
            'description': description,
            'actor': "server",
            'event': event,
            'current_hand': None,
            'item': dic
        }


    else:
        return {
            'description': f"[UNHANDLED] Event: {event}",
            'actor': None,
            'event': event,
            'current_hand': None,
            'item': dic
        }


def rebuild_game(path_game, path_p1, path_p2, log_path="evaluation_results/paper_exps", game_name = None):
    rec_game = load_json(path_game)
    rec_p1 = load_json(path_p1)
    rec_p2 = load_json(path_p2)

    if game_name is not None:
        log_path += f'/{game_name}'
    check_path(log_path)
    game_file = path_game.split('/')[-1]
    log_path += '/' + game_file.replace('.json', '-log.md')

    merged_records = rec_game + rec_p1 + rec_p2
    merged_records.sort(key=lambda x: x.get('time', float('inf')))

    output_lines = []
    turn = 0
    
    gpt_name = ""
    claude_name = ""


    for item_dic in merged_records:
        event = item_dic.get('event', None)
        if event == 'server__player_ready_to_start':
            msg = json.loads(item_dic['msg'])
            if game_name == '4o_vs_cl':
                if 'gpt' in msg['username'].lower():
                    gpt_name = msg['username']
                elif 'claude' in msg['username']:
                    claude_name = msg['username']

        if turn > 12 and event != "server__game_over":
            continue
        # 🧠 Agent Thought
        if event is None:
            player = item_dic.get('player', '?')
            role = item_dic.get('role', None)
            if role is None or role == 'planner':
                continue

            msg = item_dic.get('msg', {})
            msg = json.loads(msg)
            if 'text' in msg:
                continue

            thoughts = extract_all_thoughts(msg['content'])
            if thoughts.strip() == "":
                continue
            
            header = f"\n### 🧠 `{player}` THINKS:"
          
            if game_name == '4o_vs_cl':
                header=header.replace(claude_name, 'claude')
                header=header.replace(gpt_name, 'GPT-4o')
                thoughts = thoughts.replace(claude_name, 'claude')
                thoughts = thoughts.replace(gpt_name, 'GPT-4o')

            output_lines.append(header)
            output_lines.append(thoughts)
            continue
        
        if event in NEEDLESS_EVENTS or (turn != 1 and event == 'server__update_all_hands'):
            continue

        # 🎮 Turn Start
        if event == "server__start_proposal":
            turn += 1
            header = f"\n\n## 🌀 Turn {turn} start!\n{'-'*40}"
            # print(header)
            output_lines.append(header)
            continue


        info = parse_item_info(item_dic)
        desc = info['description'].strip()
    
        if game_name == '4o_vs_cl':
            desc = desc.replace(claude_name, 'claude')
            desc = desc.replace(gpt_name, 'GPT-4o')
    
        # ⚙️ 玩家 Action（非 server 开头，且含 player）
        if "server" in event:
            header = f"\n### 🖥 Server Event: `{event}`"
            if event == 'server__game_over':
                print(f"Game over!")
                output_lines.append(header)
                output_lines.append(desc + "\n")    
                break
            
        elif "player" in event:
            header = f"\n### ⚙️ Player Event: `{event}`"

        # 兜底（未知行为）
        else:
            header = f"\n### ❓ Unknown Event: `{event}`"

        output_lines.append(header)
        output_lines.append(desc + "\n")

    # 写入日志
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("# 📝 TradeCraft Game Log\n")
        f.write("\n".join(output_lines))
    print(f"\n✅ Game log saved to {log_path}")


def replace_usernames_in_markdown(folder_path, player_dic):
    """
    替换 markdown 文件中所有玩家名，支持大小写匹配并保留格式。
    """
    for fname in os.listdir(folder_path):
        if not fname.endswith(".md"):
            continue

        fpath = os.path.join(folder_path, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️ 无法读取 {fname}: {e}")
            continue

        for old_name, new_name in player_dic.items():
            # 替换时保留原大小写结构
            pattern = re.compile(rf"\b({re.escape(old_name)})\b", re.IGNORECASE)
            content = pattern.sub(lambda m: match_case(new_name, m.group(1)), content)

        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            # print(f"✅ 替换完成并保存: {fname}")
        except Exception as e:
            print(f"❌ 写入失败 {fname}: {e}")



if __name__ == "__main__":

    from argparse import ArgumentParser


    args = ArgumentParser()
    args.add_argument('--exp_name', '-N', default='SP', help='Rebuild Game Info for Model-Based Evaluation, model groups in [SP, Model], default [SP]')
    args.add_argument("--rebuild_path", '-RP', default='evaluation_results/paper_experiments_same/rebuild', help='Folder path of the rebuild game info.')

    
    args = args.parse_args()
    character_game_list = ['un_vs_coo', 'com_vs_un', 'com_vs_coo', 'coo1_vs_coo2', 'com1_vs_com2', 'un1_vs_un2']
    model_game_list = ['4o_vs_cl', 'ge_vs_4o', 'ge_vs_cl']

    if args.exp_name == 'SP':
        game_list = character_game_list
    elif args.exp_name == 'Model':
        game_list = model_game_list
    else:
        raise NotImplementedError(f"The Exp-Name: {args.exp_name} is unsupported, choose from [SP, Model]")
    
    for game in game_list:
        all_loaded = robust_group_game_files(folder_path=f"data/{game}")
        for names in all_loaded:
            print('-'*20)
            for name in names:
                print(name)
        for item in tqdm(all_loaded):
            names = list(item)
            print(f"Find {len(names)} files.")
            print(f"Names: {names}")
            rebuild_game(names[0], names[1], names[2], log_path=f"{args.rebuild_path}", game_name=game)
            
        replace_usernames_in_markdown(f"{args.rebuild_path}/{game}", player_dic=players_dics[game])
    