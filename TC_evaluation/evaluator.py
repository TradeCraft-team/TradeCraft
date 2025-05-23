import json
import os
import numpy as np
import openai
from utils_eval import *
from rebuild_game import *
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
from tqdm import tqdm
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from argparse import ArgumentParser

from openai import AzureOpenAI


client = openai.Client(
api_key=API_KEY,
base_url=API_BASE
)




def run_heuristic_evaluations(game_info, player_infos: list):
    assert len(player_infos) == 2 , NotImplementedError("Sorry, evaluations of **SINGLE PLAYER** or **MULTI-PLAYERS are unsupported. " \
    "\n Please make sure you pass two [player thoughts record] file(or filepath)")

    if type(game_info) == str:
        game_info = load_json(game_info)

    # Get Game ID
    game_id = game_info[0]['domain'][0]
    player_infos = [load_json(player_info) if isinstance(player_info, str) else player_info for player_info in player_infos]
    player_names = [player_info[0]['player'] for player_info in player_infos]

    record = extract_win_loss(game_info, player_names)

    
    save_path = f"eval_results/double_players/{game_id}/heuristic/"
    check_path(save_path)

    try:
        with open(save_path + "heuristic_results.json", 'w') as f:
            json.dump(record, f)
        print(f"✅")
        print(f"Successfully saved [HEURISTIC] evaluation result of game [{game_id}]")

    except Exception as e:
        print(f"❌!!! ")
        print(f"An error occured when trying to save the [HEURISTIC] evaluation result of game: [{game_id}], plz retry. ")    


def collect_heuristic_results(game_ids: list, considered_players: list):
    heu_reuslts = []
    faild_list = []
    for game_id in game_ids:
        rec_path = f"eval_results/double_players/{game_id}/heuristic/heuristic_results.json"
        try:
            rec = {game_id: load_json(rec_path)}
            heu_reuslts.append(rec)
        except:
            print(f"⚠️: Couldn't find [HEURISTIC] evaluation result of GAME: [{game_id}]")
            faild_list.append({game_id, "Couldn't find the file. "})


    final_result = {}
    for p in considered_players:
        final_result[p] = {
             "reject_proposal": 0,
            "accept_proposal": 0, 
            "win": 0, 
            "loss": 0, 
            "all_win": 0, 
            "all_loss": 0, 
            "turns": 0
            }

    for rec in heu_reuslts:
        eval_res_info = rec.values()[0]
        if set(eval_res_info.keys()) != set(considered_players):
            faild_list.append({game: "Player mismatch error: the players in this game are not in the list of considered players."})

        for p in eval_res_info.keys():
            eval_res_player = eval_res_info[p]
            for key, value in eval_res_player.items():
                final_result[p][key] += value


def extract_win_loss(rec_game, players = ['gemini_competitive', 'gemini_cooperative'], max_turns = 15):
    error_mode = ('claude' in players and 'gpt-4o' in players)
    if error_mode: print(f"⚠️: Now running with error mode.")

    # rec_game = load_json(path_game)
    final_rec = {
    players[0]: {
        'invalid_behavior': 0,
        'reject_proposal': 0,     # 主动拒绝别人的次数
        'accept_proposal': 0      # 主动接受别人的次数
    },
    players[1]: {
        'invalid_behavior': 0,
        'reject_proposal': 0,
        'accept_proposal': 0
    }
}

    turns = 0
    for item in rec_game:
        event = item['event']
        msg = json.loads(item['msg'])

        if turns > max_turns and event != "server__game_over":continue
        if 'invalid' in event or 'err' in event:
            p_rec_name = msg['username'].lower()
            if error_mode: 
                if 'claude' in p_rec_name:
                    p_rec_name = 'claude'
                elif 'gpt' in p_rec_name:
                    p_rec_name = 'gpt-4o'
                else:
                    raise ValueError
            final_rec[p_rec_name]['invalid_behavior'] += 1
            
        if event == 'player__approval_or_reject':
            p_rec_name = msg['username'].lower()
            if error_mode: 
                if 'claude' in p_rec_name:
                    p_rec_name = 'claude'
                else:
                    p_rec_name = 'gpt-4o'
            if msg['decision'].lower() == 'accept': final_rec[p_rec_name]['accept_proposal'] += 1
            elif msg['decision'].lower() == 'reject': final_rec[p_rec_name]['reject_proposal'] += 1
            else: print(f"something wrong!!! - {msg}")
            
        if event == 'player__craft_recipe_check':
            p_rec_name = msg['username'].lower()
            if error_mode: 
                if 'claude' in p_rec_name:
                    p_rec_name = 'claude'
                else:
                    p_rec_name = 'gpt-4o'
            # print(f"P_rec_Name is {p_rec_name}, final_rec keys: {final_rec.keys()}")
            result = msg.get('result', False)
            if not result:
                final_rec[p_rec_name]['invalid_behavior'] += 1

        if event == 'server__start_proposal':
            turns += 1

        if event == 'server__game_over':
            actor_pool = msg['action_queue']
            win_status_pool = msg['win-status']
            
            if error_mode:
                win_status_pool_new = {}
                for key, status in win_status_pool.items():
                    if 'claude' in key:
                        win_status_pool_new['claude']  = status
                    elif 'gpt-4o' in key.lower():
                        win_status_pool_new['gpt-4o'] = status

                win_status_pool = win_status_pool_new
                actor_pool = ['claude', 'gpt-4o']

            for actor in actor_pool:
                final_rec[actor.lower()]['win'] = 1 if win_status_pool[actor] else 0
                final_rec[actor.lower()]['loss'] = 1 if not win_status_pool[actor] else 0
                values = list(win_status_pool.values())
                final_rec[actor.lower()]['all_win'] = 1 if all(values) else 0
                final_rec[actor.lower()]['all_loss'] = 1 if not any(values) else 0
                final_rec[actor.lower()]['turns'] = turns
        else:
            continue

    return final_rec
    

def heuristic_evaluation(player_pool = ['gemini_competitive', 'gemini_cooperative'], game = "com_vs_coo"):
    heuristic_list = []
    all_loaded = robust_group_game_files(folder_path=f"data/{game}")
    print(f"loading files from: data/{game}")
    for item in tqdm(all_loaded):
        names = list(item)
        final_dic = extract_win_loss(load_json(names[0]), players=player_pool)
        heuristic_list.append(final_dic)
   
    result = merge_final_dic_list(heuristic_list)
    for player in result.keys():
        result[player]['invalid_behavior']/=result[player]['turns']
        sum_proposal = result[player]['reject_proposal'] + result[player]['accept_proposal']
        result[player]['reject_proposal']/=sum_proposal
        result[player]['accept_proposal']/=sum_proposal
        result[player]['win'] -= result[player]['all_win']
        result[player]['loss'] -= result[player]['all_loss']
    return result


def LLM_based_eval(item: str, model = MODEL, game_log = None, game = "tradecraft"):
    system_prompt_path = f"prompts/evaluation_items/{item}.md"
    
    game_rule_prompt_path = f"prompts/game_rules/{game}_intro.md"

    assert item in LLM_evaluation_item_list, ValueError("Unsupported item for evaluation")
   
    with open(game_rule_prompt_path, "r") as f: 
        intro = f.read()
    params = {'intro': intro, "game_log": game_log,}
    prompt = load_prompt_template(system_prompt_path, params)

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={'type': "json_object"},
    )
    response = completion.choices[0].message.content


    return response



def get_heuristic_for_character(result_dic):
    character_reuslts = {}
    for game, item in result_dic.items():
        for player, info in item.items():
            if player not in character_reuslts.keys():
                character_reuslts[player] = info
            else:
                for heu_name, heu_value in info.items():
                    character_reuslts[player][heu_name] += heu_value

    for heu in character_reuslts['gemini_undefine']:
        character_reuslts['gemini_undefine'][heu] += (character_reuslts['gemini2'][heu] + character_reuslts['gemini1'][heu])

    character_reuslts.pop("gemini2")
    character_reuslts.pop("gemini1")

    for heu in character_reuslts['gemini_cooperative']:
        character_reuslts['gemini_cooperative'][heu] += (character_reuslts['gemini_cooperative1'][heu] + character_reuslts['gemini_cooperative2'][heu])


    character_reuslts.pop("gemini_cooperative1")
    character_reuslts.pop("gemini_cooperative2")

    for heu in character_reuslts['gemini_competitive']:
        character_reuslts['gemini_competitive'][heu] += (character_reuslts['gemini_competitive1'][heu] + character_reuslts['gemini_competitive2'][heu])

    character_reuslts.pop("gemini_competitive1")
    character_reuslts.pop("gemini_competitive2")

    character_reuslts['Gemini-Cooperative'] = character_reuslts.pop('gemini_cooperative')
    character_reuslts['Gemini-Competitive'] = character_reuslts.pop('gemini_competitive')
    character_reuslts['Gemini-Unprimed'] = character_reuslts.pop('gemini_undefine')

    for player, item in character_reuslts.items():
        if 'turns' in heu:
            item[heu]/=20
        else:
            item[heu]/=2

    

    return character_reuslts
                


def get_heuristic_for_models(result_dic):
    character_reuslts = {}
    for game, item in result_dic.items():
        for player, info in item.items():
            if player not in character_reuslts.keys():
                character_reuslts[player] = info
            else:
                for heu_name, heu_value in info.items():
                    character_reuslts[player][heu_name] += heu_value

    for player, item in character_reuslts.items():
        for heu in item.keys():
            if 'turns' in heu:
                item[heu]/=20
            else:
                item[heu]/=2

    return character_reuslts
                

def evaluate_single_file(fname, log_path, save_path, item, max_retries=3):
    if not fname.endswith(".md"):
        return None, False
    
    out_name = fname.replace(".md", f".{item}.json")
    out_path = os.path.join(save_path, out_name)

    if os.path.exists(out_path):
        print(f"⏩ Skipping {fname} — already evaluated.")
        return None, True
   
    fpath = os.path.join(log_path, fname)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️ Read error ({fname}): {e}")
        return None, False

    result_str = None
    for attempt in range(1, max_retries + 1):
        try:
            result_str = LLM_based_eval(item=item, game_log=content)
            break
        except Exception as e:
            print(f"❌ Eval failed ({fname}) [Attempt {attempt}]: {e}")
            time.sleep(2 ** attempt)  # 指数退避

    if result_str is None:
        return None, False

    try:
        parsed = json.loads(result_str)
    except Exception as e:
        print(f"⚠️ JSON parse error ({fname}): {e}")
        parsed = {"raw": result_str}

    try:
        with open(out_path, "w", encoding="utf-8") as fout:
            json.dump(parsed, fout, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Save failed ({fname}): {e}")
        return None, False

    return {fname: parsed}, True


def evaluation_for_one_item(item, log_path, base_save_path):
    save_path = os.path.join(base_save_path, item)
    os.makedirs(save_path, exist_ok=True)

    files = [f for f in os.listdir(log_path) if f.endswith(".md")]


    results = []
    failed_files = []

    for fname in tqdm(files, desc=f"[{item}]"):
        try:
            result, success = evaluate_single_file(fname, log_path, save_path, item)
            if success:
                results.append(result)
            else:
                failed_files.append(fname)
        except Exception as e:
            print(f"❌ Unexpected error in {fname}: {e}")
            failed_files.append(fname)

    return {item: results}, {item: failed_files}


def evaluate_all_items_parallel(
    item_list,
    log_path,
    base_save_path,
    max_workers_item=8
):
    all_failures = defaultdict(list)

    if not os.path.exists(log_path):
        print(f"An error occured while evaluating the game, no [game log markdown was found]\n Fix this by first: \n clear the path: evaluation_results/paper_experiments/rebuild/ \nthen run: \n python rebuild_game.py")
        return False

    def wrap(item):
        return evaluation_for_one_item(item, log_path, base_save_path)

    with ThreadPoolExecutor(max_workers=max_workers_item) as executor:
        futures = {executor.submit(wrap, item): item for item in item_list}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result, failed = future.result()
                # all_results[item] = result[item]
                all_failures[item] = failed[item]
            except Exception as e:
                print(f"❌ Top-level failure on item {item}: {e}")
                all_failures[item] = ["ALL_FAILED"]

    for item, failed_files in all_failures.items():
        if not failed_files:
            continue
        print(f"🔁 Retrying {len(failed_files)} failed files for item {item}...")
        save_path = os.path.join(base_save_path, item)
        for fname in failed_files:
            result, success = evaluate_single_file(fname, log_path, save_path, item)
           

    return True



def plot_radar_from_items(item_list, base_folder="parse", players_dic=None, game='com_vs_un', color_map=None):
    plt.style.use('ggplot')
    scores_by_player = defaultdict(lambda: [0.0] * len(item_list))
    print(f"Scores by players: {scores_by_player}")
    display_names = {}
    base_folder = f"{base_folder}{game}"
    for idx, item in enumerate(item_list):
        item_scores = aggregate_scores(base_folder, item)
        for player, score in item_scores.items():
            scores_by_player[player][idx] = score
            if players_dic and player.lower() in players_dic:
                display_names[player] = players_dic[player.lower()]
            else:
                display_names[player] = player

    labels = [item.replace('_', '\n') for item in item_list]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(polar=True))

    for player, scores in scores_by_player.items():
        values = scores + scores[:1]
        color = color_map.get(players_dic[player.lower()])
        ax.plot(angles, values, label=display_names[player], color=color)
        ax.fill(angles, values, alpha=0.25, color=color)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=18)

    for label, angle in zip(ax.get_xticklabels(), angles):
        label.set_rotation(np.degrees(angle))
        label.set_verticalalignment('center')
        label.set_horizontalalignment('center')

    ax.set_ylim(0.3, 0.95)
    ax.set_yticks(np.arange(0.5, 1.01, 0.2))  # stick 间距为 0.2
    ax.xaxis.grid(True, color='gray', linestyle='dashed', linewidth=0.5)
    ax.yaxis.grid(True, color='gray', linestyle='dashed', linewidth=0.5)


    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=2,
              prop={'size': 18})  # 控制图例字体大小
    plt.tight_layout()
    os.makedirs("figs", exist_ok=True)
    plt.savefig(f"figs/radar_result_{game}.png", transparent=True, dpi=300)
    plt.show()


def plot_radar_from_models(item_list, base_folder="parse", players_dic=None, color_map=None, game_list = []):

    plt.style.use('ggplot')
    scores_by_player = defaultdict(lambda: [0.0] * len(item_list))
    display_names = {}
    for game in game_list:
        folder = f"{base_folder}_{game}"

        for idx, item in enumerate(item_list):
            item_scores = aggregate_scores(folder, item)
            for player, score in item_scores.items():
                player_name = player_dics[game][player.lower()]
                scores_by_player[player_name][idx] += score/2
                if players_dic and player.lower() in players_dic[game]:
                    display_names[player_name] = player_name
             
    print(f"display game: {display_names}")

    for player, scores in scores_by_player.items():
        print(f"Scores: {scores}")
        score_dic = {}
        for key, value in zip(item_list, scores):
            score_dic[key] = value
        plot_radar_from_dict([score_dic], title=f"{player}", color=color_map[player], ylim=(0.3, 0.85))


def aggregate_scores(parse_folder, item = "Adaptability"):
    player_scores = defaultdict(list)
    parse_folder = os.path.join(parse_folder, item)
    for fname in os.listdir(parse_folder):
    
        if not fname.endswith('.json') or 'Duo_Yd3DsoC4' in fname:
            continue
        fpath = os.path.join(parse_folder, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load {fname}: {e}")
            continue

        for id, turn in enumerate(data):
            if id >=12: continue
            
            try:
                for turn_key, evaluations in turn.items():
                    if turn_key.strip().lower() == "turn 13":
                        break
                    for entry in evaluations:
                        user = entry["user"].lower()
                        score = entry["score"]
                        player_scores[user].append(float(score))
            except:
                print(f"Error occurs at f: {fname}")
                continue

    average_scores = {
        player: round(sum(scores) / len(scores), 4) if scores else 0.0
        for player, scores in player_scores.items()
    }

    return average_scores


def plot_character_behavior_bar_split(character_result: dict, color_map=None):
    plt.style.use('ggplot')
    metrics = ['invalid_behavior', 'reject_proposal', 'turns']
    metric_labels = ['Invalid Behavior', 'Reject Proposal', 'Average Game Turn']

    if color_map is not None:
        colors = list(color_map.values())
    else:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    os.makedirs("figs", exist_ok=True)

    for m_idx, metric in enumerate(metrics):
        fig, ax = plt.subplots(figsize=(3, 5))

        character_names = list(character_result.keys())
        scores = [character_result[c][metric] for c in character_names]
        x = np.arange(len(character_names))*0.4

        for i, (name, score) in enumerate(zip(character_names, scores)):
            label = (name[0].upper() + name[1:]).replace('-', '\n') if 'gpt' not in name else 'GPT-4o'
            ax.bar(x[i], score, width=0.4, color=colors[i % len(colors)],
                   edgecolor='black', linewidth=1.5, label=label, alpha=0.4)

        ax.set_ylabel(metric_labels[m_idx], fontsize=22)

        ax.set_xticklabels([]) 
        ax.tick_params(axis='y', labelsize=20)  

        names = [(name[0].upper() + name[1:]).replace('-', '\n') if 'gpt' not in name else 'GPT-4o' for name in character_names]

        ax.set_ylim(0, max(scores) * 1.2)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.legend(fontsize=9, loc="upper right")
 
        plt.tight_layout()
        plt.show()
        plt.savefig(f"figs/characters_{metric}.png", dpi=300, transparent=False)
        plt.close()




if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument("--exp_name", '-N', default='Heu_Model', help="Experiment Name, in [Heu_SP, Heu_Model, Model_SP, Model_Model, winners].")
    args.add_argument("--mb_fp", '-MP', default='evaluation_results/paper_experiments_same/model_based_ana', help="Folder path of the model-based evaluation results.")
    args.add_argument("--rebuild_path", '-RP', default='evaluation_results/paper_experiments_same/rebuild', help='Folder path of the rebuild game info.')
    args.add_argument("--threads", default=8)

    args = args.parse_args()
    heu_res = {}
    character_game_list = ['un_vs_coo', 'com_vs_un', 'com_vs_coo', 'coo1_vs_coo2', 'com1_vs_com2', 'un1_vs_un2']
    model_game_list = ['4o_vs_cl', 'ge_vs_4o', 'ge_vs_cl']
    if args.exp_name ==  'Heu_SP':
        for game in character_game_list:
            players_dic = player_dics[game]
            heu_res[game] = heuristic_evaluation(player_pool=list(players_dic.values()), game = game)
            print(f"---------Game: {game}-----------")
            for player, value in heu_res[game].items():
                print(f"~~~~{player}~~~~")
                for item, item_v in value.items():
                    print(f"{item} = {item_v}")


        character_result = get_heuristic_for_character(heu_res)
        plot_character_behavior_bar_split(character_result=character_result, color_map=color_map)


    elif args.exp_name == 'Heu_Model':
        for game in model_game_list:
            players_dic = player_dics[game]
            heu_res[game] = heuristic_evaluation(player_pool=list(players_dic.values()), game = game)
            print(f"---------Game: {game}-----------")
            for player, value in heu_res[game].items():
                print(f"~~~~{player}~~~~")
                for item, item_v in value.items():
                    print(f"{item} = {item_v}")
        model_results = get_heuristic_for_models(heu_res)
        plot_character_behavior_bar_split(character_result=model_results, color_map=color_map)


    elif args.exp_name == 'Model_SP':
        for game in character_game_list:
            print(f"---------{game}-----------")
            players_dic = player_dics[game]
            success = evaluate_all_items_parallel(
            item_list=LLM_evaluation_item_list,
            log_path=f"{args.rebuild_path}/{game}/", 
            base_save_path=f"{args.mb_fp}/{game}", 
            max_workers_item=args.threads
            )
    
            if success:
                plot_radar_from_items(
                item_list=LLM_evaluation_item_list, 
                base_folder=f"{args.mb_fp}/", 
                players_dic=players_dic, 
                game=game, 
                color_map=color_map
            )
            
            

    elif args.exp_name == 'Model_Model':
        for game in model_game_list:    
            print(f"---------{game}-----------")
            players_dic = player_dics[game]
            success = evaluate_all_items_parallel(
                item_list=LLM_evaluation_item_list,
                log_path=f"{args.rebuild_path}/{game}/", 
                base_save_path=f"{args.mb_fp}/{game}", 
                max_workers_item=args.threads
                )
    
            if success:
                plot_radar_from_items(
                    item_list=LLM_evaluation_item_list, 
                    base_folder=f"{args.mb_fp}/", 
                    players_dic=players_dic, 
                    game=game, 
                    color_map=color_map
                )
                
    elif args.exp_name == 'winners':
        winner_loser()
 
    else:
        print(f"❌: Wrong Experiment Name, plz try -N in [Heu_SP, Heu_Model, Model_SP, Model_Model, winners]")

