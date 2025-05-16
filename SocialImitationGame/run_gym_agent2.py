"""
"""
import asyncio
import gymnasium
from dotenv import load_dotenv, find_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.tools.render import render_text_description
from src.SIG_instances.GymAgentNoSIG import GymAgent
from src.agent_proxy import *
from src.agent_proxy.utils import print
from src.proxied_games.tradeCraft import *
import os
import random
from typing import Literal, Optional
from langchain_openai import AzureChatOpenAI, ChatOpenAI
class LLMFactory:
    """
    AzureOpenAI:
        gpt-35-turbo-0125
        gpt-4o-mini-2024-07-18
        gpt-4-turbo-2024-04-09
        gpt-4o-2024-08-06
    """
    def __new__(
        cls,
        model: str = 'gpt-4o-2024-08-06',
        provider: Literal['azure_openai', 'openai'] = 'azure_openai',
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        temperature: float = 0.,
        **kwargs
    ):
        if provider == 'azure_openai':
            # http://infra.pages.mybigai.ac.cn/tonggpt/
            region_mapping = {
                'gpt-35-turbo-0125': ['canadaeast', 'northcentralus', 'southcentralus'],
                'gpt-4o-mini-2024-07-18': ['eastus'],
                'gpt-4-turbo-2024-04-09': ['eastus2', 'swedencentral'],
                # gpt4v
                'gpt-4-turbo-2024-04-09': ['eastus2', 'swedencentral'],
                # 'gpt-4o-2024-08-06': ['eastus', 'eastus2', 'northcentralus', 'southcentralus', 
                #                       'swedencentral', 'westus', 'westus3'],
                # 'gpt-4o-2024-08-06': ['eastus'],
                'gpt-4o-2024-08-06': ['northcentralus'],
            }
            if model in region_mapping:
                region = random.choice(region_mapping[model])
            else:
                region = os.environ['BIGAI_REGION']

            return AzureChatOpenAI(
                model=model,
                temperature=temperature,
                # api_key=api_key or os.environ['BIGAI_OAI_API_KEY'],
                api_key="",
                # api_version=api_version or os.environ['BIGAI_API_VERSION'],
                api_version="2025-03-01-preview",
                # azure_endpoint=azure_endpoint or f"{os.environ['BIGAI_API_BASE']}/{region}",
                azure_endpoint="https://api.tonggpt.mybigai.ac.cn/proxy/eastus2",
                streaming=False,
                **kwargs
            )
        elif provider == 'openai':
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
                streaming=False,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

def prep_llm():
    model = 'gpt-4-turbo-2024-04-09'
    llm = LLMFactory(model=model, provider='azure_openai')
    return llm


async def run():
    """
    The 'Standard' gymnasium environment workflow.
    """
    env = gymnasium.make("sig/AsyncProxyTooled-v0",
                         addr="localhost",
                         port=5000,
                         game_dynamics=BASIC_TC_GAME_DYNAMICS,
                         language_processor=BASIC_TC_LANGUAGE_PROCESSOR,
                         docs=BASIC_TC_GAME_CONFIG.tool_docs)
    intro = BASIC_TC_LANGUAGE_PROCESSOR.game_intro()

    cnt = -1
    print(env)
    print(cnt := cnt + 1, s=1)
    # print(render_text_description(env.tools))

    agent = GymAgent(env, llm=prep_llm(),port=8192,intro=intro)
    obs, info = await env.reset()

    terminated = False
    truncated = False
    print(info["translated"])
    while not (terminated or truncated):

        print(cnt := cnt + 1, s=1)
        action = await agent.generate_action(info)
        if action is None:
            terminated = True
            continue
        print(action, s=23)
        obs, _, terminated, truncated, info = await env.step(action)
        print(info["translated"])


if __name__ == '__main__':
    assert load_dotenv(
        find_dotenv(filename='.env', raise_error_if_not_found=True))
    asyncio.run(run())
