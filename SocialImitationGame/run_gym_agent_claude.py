"""
"""
import asyncio
import gymnasium
from llm_factory import LLMFactory
from dotenv import load_dotenv, find_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.tools.render import render_text_description
from src.SIG_instances.GymAgentNoSIG import GymAgent
from src.SIG_instances.GymAgentNoSIG.single_agent_claude import GymAgent_claude

from src.agent_proxy import *
from src.agent_proxy.utils import print
from src.proxied_games.tradeCraft import *
import os

def prep_llm():
    model = 'claude-3-7-sonnet-20250219'
    llm = LLMFactory(model=model, provider='claude')
    return llm

import time

BASIC_TC_GAME_CONFIG.username = f"claude-player{int(time.time())}"
# BASIC_TC_GAME_CONFIG.username = "claude"
async def run():
    """
    The 'Standard' gymnasium environment workflow.
    """
    env = gymnasium.make("sig/AsyncProxyTooled-v0",
                         addr="localhost",
                         port=5000,
                         game_dynamics=BASIC_TC_GAME_DYNAMICS,
                         language_processor=BASIC_TC_LANGUAGE_PROCESSOR,
                         docs=BASIC_TC_GAME_CONFIG.tool_docs,
                        game_config=BASIC_TC_GAME_CONFIG)
    # intro = BASIC_TC_LANGUAGE_PROCESSOR.game_intro()
    intro = BASIC_TC_LANGUAGE_PROCESSOR.game_intro(winding_target='competitive')

    # intro = BASIC_TC_LANGUAGE_PROCESSOR.
    
    cnt = -1
    print(env)
    print(cnt := cnt + 1, s=1)
    # print(render_text_description(env.tools))
    game_id="claude_vs_4o"
    agent = GymAgent_claude(env, llm=prep_llm(),game_id=game_id,port=8191,intro=intro)
    obs, info = await env.reset()

    terminated = False
    truncated = False
    while not (terminated or truncated):

        print(cnt := cnt + 1, s=1)
        action = await agent.generate_action(info)
        if action is None:
            terminated = True
            continue
        print(action, s=23)
        obs, _, terminated, truncated, info = await env.step(action)


if __name__ == '__main__':
    assert load_dotenv(
        find_dotenv(filename='.env', raise_error_if_not_found=True))
    asyncio.run(run())
