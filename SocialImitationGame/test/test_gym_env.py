"""
Test Gymnasium Env construct
"""
import sys
import random
import gymnasium

sys.path.append("..")
from src.agent_proxy import SyncProxyEnv, TooledProxyEnv
from src.proxied_games.tradeCraft import (BASIC_TC_GAME_CONFIG as conf,
                                          BASIC_TC_GAME_DYNAMICS as dyn,
                                          BASIC_TC_LANGUAGE_PROCESSOR as lang)


def main():

    env = gymnasium.make(
        "sig/ProxyTooled-v0",
        # "sig/ProxyLLM-v0",
        addr="localhost",
        port=5000,
        game_dynamics=dyn,
        language_processor=lang)

    observation, info = env.reset()
    terminated = False
    truncated = False

    actions = [
        ("item_info", "stick"),
        ("item_info", "coal"),
        ("possible_recipes_from_hand", {
            "messages": {
                "username": "abc"
            }
        }),
    ]

    while not (terminated or truncated):
        print(observation, info)
        action = env.action_space.sample()
        i = random.randint(0, 3)
        action = actions[i]
        observation, reward, terminated, truncated, info = env.step(action)


if __name__ == '__main__':
    main()
