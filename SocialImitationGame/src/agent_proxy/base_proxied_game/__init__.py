"""
Base Classes for Proxied Games
"""

from .game_dynamics import BaseGameDynamics
from .language_processor import BaseLanguageProcessor
from .game_config import BaseGameConfig

BASE_LANGUAGE_PROCESSOR = BaseLanguageProcessor()
BASE_GAME_CONFIG = BaseGameConfig()
BASE_GAME_DYNAMICS = BaseGameDynamics()
