from gymnasium.envs.registration import register
from .gym_env import env_db_logger

from .proxy import *
from .gym_env_wrapper import (
    SyncProxyEnv,
    AsyncTooledProxyEnv,
    # SyncTooledProxyEnv,
)

register(id="sig/ProxyLLM-v0",
         entry_point=SyncProxyEnv,
         order_enforce=False,
         disable_env_checker=True)
register(id="sig/AsyncProxyTooled-v0",
         entry_point=AsyncTooledProxyEnv,
         order_enforce=False,
         disable_env_checker=True)
# register(id="sig/SyncProxyTooled-v0", entry_point=SyncTooledProxyEnv)
