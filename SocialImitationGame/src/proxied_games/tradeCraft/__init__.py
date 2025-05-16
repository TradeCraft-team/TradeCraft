"""
FSM:
                               ---
                              | 5 |
                              v   |
        pre_login         make_proposal           -------------
           |1               3|   ^               |     11      |
           v        2        v   |4       10     v             |
        game_start ----> idle_watch (8)  <----> start_craft ---
                           6|   ^     |    9
                            v  7|     |
                       accept_reject   -----> game_over
                                         13
"""
from .game_config import BasicTCGameConfig
from .game_dynamics import BasicTCGameDynamics
from .language_processor import BasicTCLanguageProcessor

BASIC_TC_GAME_CONFIG = BasicTCGameConfig()
BASIC_TC_GAME_DYNAMICS = BasicTCGameDynamics()
BASIC_TC_LANGUAGE_PROCESSOR = BasicTCLanguageProcessor()
