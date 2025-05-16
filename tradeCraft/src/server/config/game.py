"""
Configs about game and player.

[TODO] MOVE the problem part into craft_rules/rule_sets. Make it customizable!
"""
import random
import importlib
from copy import deepcopy
from typing import Literal
from ...craft_rules import config

pr_args = config.pr_args
CRAFT_RULE_CHOICE = pr_args["craft_rule_choice"]
CRAFT_RULE_PREFIX = pr_args["craft_rule_prefix"] + ":"
CRAFT_RULE_LENGTH = len(CRAFT_RULE_PREFIX)

GAME_NAME_LEN = 20
PLAYER_NAME_LEN = 24
DEFAULT_MAX_TURN = 15

# Define all game-config types here.
# This determines how many Halls will be created.
GAME_RULES = {
    "2-player-pool-matching": {
        "init_game_pool_size":
        1,
        "num_players":
        200,
        "game_config": {
            "num_players": 2,
            "player_assignment": "matching",
            "problem_type": "1p_v_1p",
            "player_order": "sequential",
            "problem_config": {
                "reload_conf_per_game": True
            },
        },
        "description":
        "This is a hall for 1v1 TradeCraft games. Players are randomly paired to play against each other."
    },
    "3-player-pool-matching": {
        "init_game_pool_size":
        1,
        "num_players":
        200,
        "game_config": {
            "num_players": 3,
            "player_assignment": "matching",
            "problem_type": "1p_v_1p_v_1p",
            "problem_config": {
                "reload_conf_per_game": True
            },
        },
        "description":
        "This is a hall for 3-player TradeCraft games. Players are randomly assigned to play against each other."
    },
    "1-player-test": {
        "init_game_pool_size":
        1,
        "num_players":
        200,
        "game_config": {
            "num_players": 1,
            "player_assignment": "matching",
            "problem_type": "1p",
            "problem_config": {
                "reload_conf_per_game": False
            },
        },
        "description":
        "This is a hall for 1-player TradeCraft games. Just for test."
    },
}

GAME_SETTINGS_1P_V_1P = [{
    "hands": [{
        "minecraft:cobblestone": 6,
        "minecraft:iron_ingot": 3,
        'minecraft:flint': 2
    }, {
        "minecraft:redstone": 1,
        "minecraft:oak_planks": 4,
        'minecraft:stick': 4
    }],
    "targets": [{
        'minecraft:redstone_torch': 1
    }, {
        'minecraft:flint_and_steel': 1
    }]
}, {
    "hands": [{
        "minecraft:iron_ore": 5,
        "minecraft:cherry_planks": 1
    }, {
        "minecraft:oak_planks": 1,
        "minecraft:coal": 1
    }],
    "targets": [{
        'minecraft:iron_hoe': 1
    }, {
        'minecraft:iron_sword': 1
    }]
}, {
    "hands": [
        {
            'minecraft:redstone': 1,
            'minecraft:iron_hoe': 10,
            'minecraft:iron_helmet': 8,
            'minecraft:stick': 1,
            'minecraft:leather': 3
        },
        {
            'minecraft:oak_log': 5,
            'minecraft:iron_ingot': 4,
            'minecraft:nether_quartz_ore': 1,
            'minecraft:sugar_cane': 9
        },
    ],
    "targets": [{
        'minecraft:activator_rail': 1
    }, {
        'minecraft:lectern': 1
    }]
}, {
    "hands": [{
        'minecraft:cherry_planks': 1,
        'minecraft:coal': 1,
        'minecraft:iron_ingot': 1,
        'minecraft:raw_copper': 1,
        'minecraft:cobblestone': 1
    }, {
        'minecraft:oak_planks': 1,
        'minecraft:raw_iron': 5,
        'minecraft:cobblestone': 1,
        'minecraft:raw_copper': 2
    }],
    "targets": [{
        'minecraft:stone_pressure_plate': 1
    }, {
        'minecraft:shears': 1
    }]
}]
hands = [{
    'minecraft:cherry_planks': 1,
    'minecraft:coal': 1,
    'minecraft:iron_ingot': 1,
    'minecraft:raw_copper': 1,
    'minecraft:cobblestone': 1
}, {
    'minecraft:oak_planks': 1,
    'minecraft:raw_iron': 5,
    'minecraft:cobblestone': 1,
    'minecraft:raw_copper': 2
}]
for tgt_x in [
        'minecraft:bucket', 'minecraft:chain', 'minecraft:shears',
        'minecraft:lightning_rod'
]:
    for tgt_y in [
            'minecraft:stone_shovel', 'minecraft:lever', 'minecraft:torch'
    ]:
        GAME_SETTINGS_1P_V_1P += [{
            "hands": deepcopy(hands),
            "targets": [{
                tgt_x: 1
            }, {
                tgt_y: 1
            }]
        }]
GAME_SETTINGS_1P_V_1P_V_1P = [{
    "hands": [{
        "minecraft:spruce_planks": 1,
        "minecraft:coal": 2,
        "minecraft:cobblestone": 1,
        "minecraft:redstone": 2,
    }, {
        "minecraft:crimson_planks": 1,
        "minecraft:iron_ingot": 1,
        "minecraft:raw_copper": 2,
        "minecraft:cobblestone": 2,
    }, {
        "minecraft:oak_planks": 1,
        "minecraft:raw_iron": 3,
        "minecraft:raw_copper": 1,
        "minecraft:feather": 1,
    }],
    "targets": [
        {
            "minecraft:lightning_rod": 1
        },
        {
            "minecraft:compass": 1
        },
        {
            "minecraft:stone_axe": 1
        },
    ]
}]
GAME_PROBLEMS = {
    "1p_v_1p": GAME_SETTINGS_1P_V_1P,
    "1p_v_1p_v_1p": GAME_SETTINGS_1P_V_1P_V_1P
}

LALCHEMY_SETTINGS_1P_V_1P = [{
    "hands": [{
        "lalchemy2:air": 5,
        "lalchemy2:earth": 10
    }, {
        "lalchemy2:water": 6,
        "lalchemy2:fire": 8
    }],
    "targets": [{
        "lalchemy2:wall": 1
    }, {
        "lalchemy2:mist": 1
    }]
}, {
    "hands": [{
        "lalchemy2:light": 2,
        "lalchemy2:air": 1,
        "lalchemy2:atmosphere": 1,
        "lalchemy2:cloud": 1,
    }, {
        "lalchemy2:time": 1,
        "lalchemy2:bacteria": 1,
        "lalchemy2:day": 1,
        "lalchemy2:continent": 2,
    }],
    "targets": [{
        "lalchemy2:sun": 1
    }, {
        "lalchemy2:moon": 1
    }]
}]
LALCHEMY_SETTINGS_1P_V_1P_V_1P = [{
    "hands": [{
        "lalchemy2:air": 9,
        "lalchemy2:mist": 6
    }, {
        "lalchemy2:stone": 6,
        "lalchemy2:earth": 12
    }, {
        "lalchemy2:water": 15,
        "lalchemy2:fire": 8
    }],
    "targets": [{
        "lalchemy2:house": 1
    }, {
        "lalchemy2:steam": 1
    }, {
        "lalchemy2:metal": 1
    }]
}]

LALCHEMY_SETTINGS_1P = [{
    "hands": [{
        "lalchemy2:air": 1000,
        "lalchemy2:earth": 1000,
        "lalchemy2:water": 1000,
        "lalchemy2:fire": 1000,
    }],
    "targets": [{
        "lalchemy2:human": 1,
    }]
}]

LALCHEMY_PROBLEMS = {
    "1p_v_1p": LALCHEMY_SETTINGS_1P_V_1P,
    "1p_v_1p_v_1p": GAME_SETTINGS_1P_V_1P_V_1P,
    "1p": LALCHEMY_SETTINGS_1P
}

from ...craft_rules import game_loader
from ...craft_rules.game_loader import ALL_PROBLEMS

GAME_PROBLEMS.update(ALL_PROBLEMS[CRAFT_RULE_CHOICE])


def PROBLEM_SAMPLER_OLD(problem_type):
    if CRAFT_RULE_CHOICE == "littleAlchemy2":
        return LALCHEMY_PROBLEMS[problem_type][0]

    index = random.randint(0, len(GAME_PROBLEMS[problem_type]) - 1)
    return GAME_PROBLEMS[problem_type][index]


GLOBAL_INDEX = {
    _rule: {
        _type: -1
        for _type in ALL_PROBLEMS[_rule]
    }
    for _rule in ALL_PROBLEMS
}


def PROBLEM_SAMPLER(problem_type: str,
                    sample_mode: Literal["rand", "seq"] = "seq",
                    **kwargs):
    """
    Problem sampler

    Parameters
    ----------
    sample_mode: "rand" or "seq".
                 "seq" will choose games sequentially,
                 "rand" will choose games randomly.
    kwargs: may load temp control lively from `settings.yaml`
            which overwrites the sample_mode parameter.
    """

    global GLOBAL_INDEX, pr_args, ALL_PROBLEMS

    if kwargs.get("reload_conf_per_game", False):
        pr_args = importlib.reload(config).pr_args
        print("\n\n\n", pr_args, "\n\n\n\n")
    if pr_args["reload_games_per_game"]:
        ALL_PROBLEMS = importlib.reload(game_loader).ALL_PROBLEMS

    problems = ALL_PROBLEMS[pr_args["craft_rule_choice"]][problem_type]

    if (prob_index := int(pr_args.get("use_game_id", "-1"))) >= 0:
        print("PROBLEM_INDEX:", prob_index)
        return problems[min(prob_index, len(problems) - 1)]

    if sample_mode == "seq":
        GLOBAL_INDEX[CRAFT_RULE_CHOICE][problem_type] += 1
        index = GLOBAL_INDEX[CRAFT_RULE_CHOICE][problem_type]
    else:
        index = random.randint(0, len(problems) - 1)
    return problems[index]
