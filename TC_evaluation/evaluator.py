import json
import os
import numpy as np
import openai
from utils_eval import *
from rebuild_game import *

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

openai.default_headers = {"x-foo": "true"}
from openai import AzureOpenAI

REGION = "eastus"
MODEL = "gpt-4o-2024-08-06"

API_BASE = "https://api.tonggpt.mybigai.ac.cn/proxy"
ENDPOINT = f"{API_BASE}/{REGION}"


client = AzureOpenAI(
    api_key=API_KEY,
    api_version="2025-03-01-preview",
    azure_endpoint=ENDPOINT,
)


LLM_evaluation_item_list = [
    "cooperative_behaviour",
    "mis_leading",
    "planing_ability",
    "communication_effectiveness",
    "competitive_behaviour",
    "intention_concealment",
    "adaptability",
    "word_behaviour_consistency"

]


#####
def LLM_based_eval(item: str, model = 'gpt-4o-2024-08-06', max_tokens = 100, username = "Alice", basic_info_dic = None, game_turns_info = None, game = "tradecraft"):
    system_prompt_path = f"prompts/evaluation_items/{item}.md"
    
    game_rule_prompt_path = f"prompts/game_rules/{game}_intro.md"

    assert item in LLM_evaluation_item_list, ValueError("Unsupported item for evaluation")
    assert username in basic_info_dic, ValueError("No such username in the basic_info_dic")

    if game_turns_info is None:
        raise ValueError("No game_turns_info is provided")
    if basic_info_dic is None:
        raise ValueError("No basic_info_dic is provided")
    
    # Load system prompt for specific evaluation item
    with open(system_prompt_path, "r") as file:
        system_prompt = file.read()

    system_prompt += "For a comprehensive evaluation, now we offer you the game rules:\n"

    with open(game_rule_prompt_path, "r") as file:
        game_rules_info = file.read()
    system_prompt += game_rules_info

    # Get game recording infos
    message = from_recordings_to_prompt(game_turns_info, basic_info_dic= basic_info_dic)

    # Generate prompt
    prompt = f"{message}\n The Agent you should evaluate is {username}, go"
    
    # Get completion
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return completion.choices[0].message.content




""""

Basic Checks:
(1) Game results
(2) Game rounds
(3) Behavior validity

"""

Hardcoded_evaluation_item_list = [
    "game_results",
    "game_rounds",
    "behavior_validity"
]


def Hardcoded_based_eval(item: str, username = "Alice", basic_info_dic = None, game_turns_info = None):
    assert item in Hardcoded_evaluation_item_list, ValueError("Unsupported item for evaluation")
    if item == "game_results":
        win = "win" if basic_info_dic[username]['win-status'] else "lose"
        return f"Game results of {username}: {win}"

    elif item == "game_rounds":
        return f"{len(game_turns_info)}"
       
    elif item == "behavior_validity":
        return "Behavior validity is not implemented yet"


def evaluation(username: str, file_path = "data/recordings/TradeCraft.Duo_oAijwPqw.json", save_path = "evaluation_results"):
    result_dic = {}
    game_turns_info, basic_info_dic = rebuild_game_info(file_path)

    for item in LLM_evaluation_item_list:
        print(f"============Checking:{item}============")
        result = LLM_based_eval(item=item, username=username, basic_info_dic=basic_info_dic, game_turns_info=game_turns_info)
        result_dic[item] = result
        print(result)


    for item in Hardcoded_evaluation_item_list:
        print(f"============Checking:{item}============")
        result = Hardcoded_based_eval(item=item, username=username, basic_info_dic=basic_info_dic, game_turns_info=game_turns_info)
        result_dic[item] = result
        print(result)
    
    # Save results
    check_path(f"{save_path}/{username}")

    with open(f"{save_path}/{username}/evaluation_results.json", "w") as f:
        json.dump(result_dic, f)

    print("Congratulation! Evaluation finished")
    return result_dic


# Helper function to convert your result into a structured format
def process_results_for_report(result_dic):
    structured_data = []

    for item, result in result_dic.items():
        try:
            result = eval(result)
        except:
            result = result
        if isinstance(result, dict):  # Handling cooperative_behaviour, planning, etc.
            for behavior, details in result.items():
                print(f"Behavior: {behavior}, Details: {details}")
                structured_data.append({
                    "Category": item,
                    "Behavior": details['Behavior'],
                    "Reason": details['Reason']
                })
        else:  # Handling hardcoded items like game_results, rounds, etc.
            structured_data.append({
                "Category": item,
                "Behavior": result,
                "Reason": ""
            })
    
    return structured_data



# Function to generate radar chart
def generate_behavior_radar_chart(username, result_dic, save_path="evaluation_results"):
    save_path = f"{save_path}/{username}/behavior_radar_chart.png"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 确保路径存在
    behavior_counts = {}
    total_rounds = eval(result_dic['game_rounds'])
    
    for item, result in result_dic.items():
        try:
            result = eval(result)
            if type(result) != dict:
                continue
        except:
            continue

        item = item.split("_")
        name = ''
        for part in item:
            name += part.capitalize() + ' '
            
        behavior_counts[name.strip()] = len(result) / total_rounds

    # Prepare data for radar chart
    categories = list(behavior_counts.keys())
    values = list(behavior_counts.values())
    values += values[:1]  # Close the circle by repeating the first value

    # Radar chart setup
    num_vars = len(categories)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Close the circle

    # Plot
    plt.figure(figsize=(8, 8))
    plt.style.use("ggplot")
    ax = plt.subplot(111, polar=True)
    ax.fill(angles, values, color="skyblue", alpha=0.4)
    ax.plot(angles, values, color="skyblue", linewidth=2)
    ax.set_yticks(np.linspace(0, 1, 5))
    ax.set_yticklabels([f"{round(y, 2)}" for y in np.linspace(0, 1, 5)], fontsize=10)
    
    # Add category labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12)

    # Title and save
    plt.title("Normalized Behavior Distribution by Category", size=15, pad=20)
    plt.savefig(save_path)
    plt.close()  # Close the figure to avoid display issues
    save_path = save_path.split("/")[-1]
    return save_path  # 返回保存的路径


# Save the report as a Markdown file
def save_report_as_markdown(username, structured_data, radar_chart_path, save_path="evaluation_results"):
    save_path = f"{save_path}/{username}/evaluation_report.md"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 确保路径存在

    current_category = structured_data[0]['Category']
    with open(save_path, "w") as f:
        # 添加 Markdown 文件头
        f.write(f"# Evaluation Report for {username}\n\n")
        f.write(f"![Behavior Radar Chart]({radar_chart_path})\n\n")  # 嵌入 Radar 图路径

        for entry in structured_data:
            if entry['Category'] != current_category:
                f.write("="*60) 
                f.write("\n\n")
                current_category = entry['Category']
            f.write(f"### {entry['Category']}\n")
            f.write(f"**Behavior**: {entry['Behavior']}\n\n")
            f.write(f"**Reason**: {entry['Reason']}\n\n")

    print(f"Markdown report saved as {save_path}")


def generate_evaluation_report(username, result_dic):
    # Process the results into a clean format
    structured_data = process_results_for_report(result_dic)
    
    # Generate radar chart and get its path
    radar_chart_path = generate_behavior_radar_chart(username, result_dic)
    
    # Save the report as a Markdown file with embedded Radar Chart
    save_report_as_markdown(username, structured_data, radar_chart_path)





if __name__ == "__main__":
    file_path = "data/recordings/TradeCraft.Duo_z96OKr4U.json"
    result_dic = None
    username = "GPT-4o"

    result_dic = evaluation(username=username, file_path=file_path, save_path="evaluation_results")
    
    path = f"evaluation_results/{username}/evaluation_results.json"
    with open(path, "r") as f:
        result_dic = json.load(f)
    generate_evaluation_report(username, result_dic)