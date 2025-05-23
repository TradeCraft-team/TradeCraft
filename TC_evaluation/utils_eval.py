import json
import os
import re
from jinja2 import Template


REGION = "eastus"
MODEL = "gemini-1.5-pro"
API_KEY = "AIzaSyCU6jpjLx1LE2YbunDku4Y4Is0j7Ae5WmY"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"


# API_BASE = "https://api.tonggpt.mybigai.ac.cn/proxy"
ENDPOINT = f"{API_BASE}/{REGION}"


player_dics = {
        'un_vs_coo':
        {
           'player 1': 'gemini_undefine', 
           'player 2': 'gemini_cooperative' 
        },

        'com_vs_un':
        {
            'player 1': 'gemini_undefine', 
           'player 2': 'gemini_competitive' 
        },
        'com_vs_coo':
        {
            'player 1': 'gemini_cooperative', 
           'player 2': 'gemini_competitive' 
        }, 
        'coo1_vs_coo2':
        {
            'player 1': 'gemini_cooperative1', 
            'player 2': 'gemini_cooperative2'
        }, 
        'com1_vs_com2':
        {
            'player 1': 'gemini_competitive1', 
            'player 2': 'gemini_competitive2'
        }, 
        'un1_vs_un2':
        {
            'player 1': "gemini1", 
            'player 2': "gemini2"
        },
        'ge_vs_4o':
        {
            'player 1': "gemini", 
            'player 2': 'gpt-4o'
        },
        'ge_vs_cl':
        {
            'player 1': 'gemini', 
            'player 2': 'claude'
        }, 
        '4o_vs_cl':
        {
            'player 1': 'gpt-4o', 
            'player 2': 'claude'
        }, 
    }


color_map = {
            
    "gpt-4o": "#2ca02c",       # 蓝灰
        "claude": "#d62728",
    "gemini": "#1f77b4",       # 浅蓝

    "GPT-4o": "#2ca02c",       # 蓝灰
    # 基础三类
    "gemini_undefine": "#1f77b4",        # 蓝
    "gemini_cooperative": "#2ca02c",     # 绿
    "gemini_competitive": "#d62728",     # 红

    "gemini_cooperative1": "#27af95",    # 青绿色
    "gemini_cooperative2": "#5a8b65",    # 深绿色

    "gemini_competitive1": "#ff7f0e",    # 橙色
    "gemini_competitive2": "#c84b31",    # 深红棕色

    "gemini1": "#4f81bd",       # 浅蓝
    "gemini2": "#6baed6",       # 蓝灰

    }



LLM_evaluation_item_list = [
    "Cooperation",
    "Goal_alignment",
    "Strategic_Planning",
    "Intention_Concealment",
    "Persuasion",
    "Information_Utilization",
    "Adaptability",
    "Self_Interested_Behavior"
]


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


def parse_crafts(craft_dic, mode='default'):
    sentence = "["
    for key, value in craft_dic.items():
        if mode == "proposal" or mode == 'recipe_check':
            num = value
        else:
            if value['n'] >= value['d']:
                num = value['n'] // value['d']
                
            else:
                num =  f"{value['n']}/{value['d']}"
        sentence += f"{key} * {num}, "

    return sentence + "]"



def find_winners(rec_path, game, player_game):
    rec_file = load_json(rec_path)
    winners = []
    for item in rec_file:
        if item['event'] != 'server__game_over':continue

        msg = json.loads(item['msg'])
        actors = msg['action_queue']
        win_status = msg['win-status']
        for actor in actors:
            if win_status[actor]:
                winners.append(player_game[actor])

    return winners


def load_all_recs(game_list = ['com_vs_coo', 'un_vs_coo', 'com_vs_un']):
    rec_games = {}
    for game in game_list:
        rec_games[game] = {}
        raw_rec_folder = f"data/{game}"
        print(f"length of files for game {game} is {len(os.listdir(raw_rec_folder))}")
        for fname in os.listdir(raw_rec_folder):
            path = os.path.join(raw_rec_folder, fname)
            pattern = (
                r'TradeCraft\.Duo_([a-zA-Z0-9\-]+)'              # game_id
            )
            match = re.match(pattern, fname)
            if not match:
                print(f"❌ Unmatched: {fname}")
                continue

            game_id = match.groups()[0]
            key = f"{game_id}"
            if key not in rec_games[game].keys():
                rec_games[game][key] = {'path':[path]}
            else:
                rec_games[game][key]['path'].append(path)
    

    # 保留每个 key 对应 path list 中最短的那个路径
    for game in rec_games:
        for key in rec_games[game]:
            path_list = rec_games[game][key]['path']
            shortest = min(path_list, key=lambda x: len(x))
            rec_games[game][key]['path'] = shortest  # 替换为单个字符串

    return rec_games
            


def find_all_winners(game_list = ['com_vs_coo', 'un_vs_coo', 'com_vs_un'], player_dics = None):
    rec_games_paths = load_all_recs(game_list)
    for game in game_list:
        print(F"🤖: Found {len(rec_games_paths[game])} files for game type: {game}")
        for match_id, match_info in rec_games_paths[game].items():
            winners = find_winners(match_info['path'], game, player_dics[game])
            rec_games_paths[game][match_id]['winners'] = winners

    return rec_games_paths

import numpy as np


def cal_win_score_item(item, rec_game_paths):
    final_scores_winners = []
    final_scores_losers = []
    for game in rec_game_paths:
        item_eval_result_path = f"evaluation_results/paper_experiments/model_based_ana/{game}/{item}"
        files = [fname for fname in os.listdir(item_eval_result_path) if fname.endswith('.json')]

        for match_id, match_info in rec_game_paths[game].items():
            for file in files:
                if match_id in file:
                    rec_data = load_json(os.path.join(item_eval_result_path, file))
                    winners = match_info['winners']
                    for id, turn_eval in enumerate(rec_data):
                        if id > 12 or type(turn_eval) == str: continue
                        for key, evaluations in turn_eval.items():
                            # print(f"🤖: {turn_eval}")
                            for entry in evaluations:
                                user = entry["user"]
                                score = entry["score"]
                                if user.lower() in winners:
                                    final_scores_winners.append(float(score))
                                else:
                                    final_scores_losers.append(float(score))
                    continue
    return {"Winners": np.mean(final_scores_winners), "Losers": np.mean(final_scores_losers)}


def winners_all_items(game_list = ['com_vs_coo', 'un_vs_coo', 'com_vs_un', 'coo1_vs_coo2', 'com1_vs_com2', 'un1_vs_un2'], item_list = LLM_evaluation_item_list):
    player_dics = {
        'un_vs_coo': {
            'gemini_undefine': 'player 1',
            'gemini_cooperative': 'player 2'
        },
        'com_vs_un': {
            'gemini_undefine': 'player 1',
            'gemini_competitive': 'player 2'
        },
        'com_vs_coo': {
            'gemini_cooperative': 'player 1',
            'gemini_competitive': 'player 2'
        },
        'coo1_vs_coo2':{
            'gemini_cooperative1': 'player 1',
            'gemini_cooperative2': 'player 2',
        }, 
        'com1_vs_com2':{
            'gemini_competitive1': 'player 1',
            'gemini_competitive2': 'player 2',
        }, 
        'un1_vs_un2':
        {
            'gemini1': "player 1", 
            'gemini2': "player 2"
        }
        
        }
    final_result_winners = {}
    final_result_losers = {}
    rec_game_paths = find_all_winners(game_list, player_dics)
    for item in item_list: 
        res_dic = cal_win_score_item(item, rec_game_paths)
        # print(f"Winner: {res_dic['Winners']}")
        final_result_winners[item] = res_dic['Winners']
        final_result_losers[item] = res_dic['Losers']
    return final_result_winners, final_result_losers





def is_time_sorted(json_list):
    """
    判断json中每个item的'time'字段是否按升序排列（格式为"%Y%m%d-%H%M%S-%f"）
    """
    time_format = "%Y%m%d-%H%M%S-%f"
    try:
        time_list = [datetime.strptime(item['time'], time_format) for item in json_list]
        return all(earlier <= later for earlier, later in zip(time_list, time_list[1:]))
    except Exception as e:
        print(f"⚠️ 时间解析失败: {e}")
        return False

def pretty_print_game_records(records, max_items=None):
    """
    优雅地展示游戏记录列表中的每个字典项。

    参数:
        records: List[Dict]，包含游戏记录的列表
        max_items: 可选，最多展示前几个记录（用于避免输出过多）
    """
    from pprint import pprint

    for i, item in enumerate(records):
        if max_items is not None and i >= max_items:
            print(f"... 共 {len(records)} 条记录，仅展示前 {max_items} 条。")
            break
        print(f"\n🔹 Record #{i+1}")
        print("-" * 40)
        for key in sorted(item.keys()):
            print(f"{key:<10}: {item[key]}")
    print("\n✅ 展示完毕")


def extract_all_thoughts(text, as_string=True):
    """
    提取文本中所有 Thought: 段落（忽略 Final Output: 之后的部分），不包含后续 Action 或 Observation 内容。
    返回字符串或列表形式。
    """
    # Step 1: 去掉 Final Output 后的内容
    text = re.split(r'\bFinal Output:', text)[0]

    # Step 2: 匹配所有 Thought: 到下一个标签（非贪婪匹配）
    raw_matches = re.findall(r'Thought:\s*(.*?)(?=\n(?:[A-Z][a-z_]+:|##|[*]{2}|$))', text, flags=re.DOTALL)

    # Step 3: 清理每段内容（去除嵌入的 Action/Observation/JSON 行）
    clean_thoughts = []
    for raw in raw_matches:
        lines = raw.strip().splitlines()
        filtered = [line.strip() for line in lines if not re.match(r'^(##|Action|Observation|{)', line)]
        clean = " ".join(filtered).strip()
        if clean:
            clean_thoughts.append(clean)

    if as_string:
        return "\n".join(f"- {t}" for t in clean_thoughts)
    return clean_thoughts

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




import os
import json
from collections import defaultdict
import tiktoken


from collections import defaultdict

def merge_final_dic_list(dic_list):
    merged = defaultdict(lambda: defaultdict(int))

    for dic in dic_list:
        for player, stats in dic.items():
            for key, value in stats.items():
                merged[player][key] += value

    # 可选：转回普通 dict
    return {player: dict(stats) for player, stats in merged.items()}



def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))





import os
import re
from collections import defaultdict

import os
import re
from collections import defaultdict
import os
import re
from collections import defaultdict

def robust_group_game_files(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    grouped = defaultdict(list)

    for f in files:
        path = os.path.join(folder_path, f)
        pattern = (
            r'TradeCraft\.Duo_([a-zA-Z0-9\-]+)'              # game_id
       
        )

        match = re.match(pattern, f)
        if not match:
            print(f"❌ Unmatched: {f}")
            continue

        # game_id, stage, side = match.groups()
        game_id = match.groups()
        key = f"{game_id}"
        grouped[key].append(os.path.join(folder_path, f))

    all_loaded = []
    for key, file_list in grouped.items():
        if len(file_list) != 3:
            print(f"⚠️ Skipping incomplete group {key} (found {len(file_list)} files)")
            continue

        # 找到路径最短的那个文件作为 game log
        game_file = min(file_list, key=lambda x: len(x))
        others = [f for f in file_list if f != game_file]
        all_loaded.append((game_file, others[0], others[1]))

    print(f"✅ Loaded {len(all_loaded)} complete game sets.")
    return all_loaded


def load_prompt_template(template_path, variables={}):
    with open(template_path, 'r') as f:
        template = Template(f.read())
    return template.render(variables)




import matplotlib.pyplot as plt
import numpy as np
import os

def plot_radar_from_dict(data_dicts, title="Radar Chart", save_path=None, color="#1f77b4", ylim = (0, 0.4)):
    """
    给定一个包含8个key-value的字典，绘制一张雷达图。
    
    参数：
    - data_dict: dict[str, float]，长度为8的字典
    - title: 图标题
    - save_path: 若指定路径则保存图像
    - color: 雷达图颜色
    """
    plt.style.use('ggplot')
    assert len(data_dicts[0]) == 8, "data_dict 必须包含8个指标"
    # 初始化图
    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(polar=True))
    for data_dict in data_dicts:
        labels = [key.replace("_", "\n") for key in data_dict.keys()]
        values = list(data_dict.values())
        
        # 闭合雷达图
        values += values[:1]
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]

        ax.plot(angles, values, linewidth=2, color = color)
        ax.fill(angles, values, alpha=0.25, color = color)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=18)



    # 标签对齐
    for label, angle in zip(ax.get_xticklabels(), angles):
        label.set_rotation(np.degrees(angle))
        label.set_verticalalignment('center')
        label.set_horizontalalignment('center')

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=2,
              prop={'size': 18})  # 控制图例字体大小


    ax.set_ylim(ylim)
    ax.set_yticks(np.arange(0.5, 1.01, 0.2))
    ax.xaxis.grid(True, color='gray', linestyle='dashed', linewidth=0.5)
    ax.yaxis.grid(True, color='gray', linestyle='dashed', linewidth=0.5)
    ax.grid(color='gray')
    plt.tight_layout()
    plt.show()
    plt.savefig(f"figs/{title}.png", dpi=300, transparent=True)
    plt.close()


def winner_loser():
    res_dic_winner, res_dic_loser = winners_all_items()

    plot_radar_from_dict([res_dic_winner], title="Evaluation-Winners", color='blue')
    plot_radar_from_dict([res_dic_loser], title="Evaluation-Losers", color='red')
    
    residual_dic = {}
    for key in res_dic_winner.keys():
        residual_dic[key] = np.abs(res_dic_winner[key] - res_dic_loser[key])/res_dic_loser[key]
    plot_radar_from_dict([residual_dic], title="Evaluation-Delta", color='green')



def extract_game_name(log_id: str) -> str:
    match = re.search(r'\.([^.]+?)_', log_id)
    if match:
        return match.group(1)
    else:
        return None  

