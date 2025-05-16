"""
    Game loader.
    Loads all games from the game folder.
"""
import os
import json
from pathlib import Path

FILE = Path(__file__).parent
GAME_ROOT = FILE / "TC_GAMES"


def expand_and_construct(path: Path) -> dict:
    """
    Expand path and construct dict
    """

    return {x.name: {} for x in path.iterdir()}


def load_games(path: Path) -> list:
    """
    Load json-games directly in `path`.
    """
    ret = []
    for child in path.iterdir():
        if not child.is_file():
            continue
        if not child.name[-5:] == ".json":
            continue
        with open(child, "r", encoding="utf8") as fptr:
            games = json.load(fptr)
        match games:
            case dict() as game:
                ret.append(game)
            case list() as games:
                ret += games
            case _:
                pass

    return ret


ALL_PROBLEMS = expand_and_construct(GAME_ROOT)
for key in ALL_PROBLEMS:
    ALL_PROBLEMS[key] = expand_and_construct(GAME_ROOT / key)
    for k in ALL_PROBLEMS[key]:
        ALL_PROBLEMS[key][k] = load_games(GAME_ROOT / key / k)

print(ALL_PROBLEMS)
