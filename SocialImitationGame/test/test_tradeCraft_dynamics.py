"""
"""
import sys
sys.path.append("..")

import asyncio
from typing import Dict
from src.agent_proxy.proxy import Proxy, ToolProxy
from src.agent_proxy.utils import print, gen_rand_str, logger, logging
from src.proxied_games.tradeCraft import (BasicTCGameConfig,
                                            BasicTCGameDynamics,
                                            BasicTCLanguageProcessor,
                                            BASIC_TC_GAME_DYNAMICS,
                                            BASIC_TC_LANGUAGE_PROCESSOR)

TC_GAME_CONFIG = BasicTCGameConfig(addr="localhost", port=5000)

async def main():
    p = Proxy("localhost", 5000,
          game_dynamics=BASIC_TC_GAME_DYNAMICS,
          game_config=TC_GAME_CONFIG,
          language_processor=BASIC_TC_LANGUAGE_PROCESSOR)

    await p.run()

    await asyncio.sleep(10)



if __name__ == '__main__':
    asyncio.run(main())
