"""
Util functions
"""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pyvis.network import Network
if __name__ in ['__main__', "utils"]:
    from node import Node
else:
    from ..node import Node

from .graph_viz_utils import *
# from .int_programming import *  # NOT READY YET

NAME_CATEGORIES = {
    "food": {
        'minecraft:apple', 'minecraft:baked_potato', 'minecraft:beef',
        'minecraft:beetroot', 'minecraft:beetroot_soup', 'minecraft:bread',
        'minecraft:carrot', 'minecraft:chicken', 'minecraft:cod',
        'minecraft:cooked_beef', 'minecraft:cooked_chicken',
        'minecraft:cooked_cod', 'minecraft:cooked_mutton',
        'minecraft:cooked_porkchop', 'minecraft:cooked_rabbit',
        'minecraft:cooked_salmon', 'minecraft:cookie', 'minecraft:dried_kelp',
        'minecraft:dried_kelp_block', 'minecraft:glistering_melon_slice',
        'minecraft:golden_apple', 'minecraft:honey_bottle', 'minecraft:melon',
        'minecraft:melon_slice', 'minecraft:mushroom_stew', 'minecraft:mutton',
        'minecraft:porkchop', 'minecraft:potato', 'minecraft:pumpkin_pie',
        'minecraft:rabbit', 'minecraft:salmon'
    },
    "transportation": {
        'minecraft:acacia_boat', 'minecraft:acacia_chest_boat',
        'minecraft:activator_rail', 'minecraft:birch_boat',
        'minecraft:birch_chest_boat', 'minecraft:cherry_boat',
        'minecraft:cherry_chest_boat', 'minecraft:chest_minecart',
        'minecraft:dark_oak_boat', 'minecraft:dark_oak_chest_boat',
        'minecraft:detector_rail', 'minecraft:furnace_minecart',
        'minecraft:hopper_minecart', 'minecraft:jungle_boat',
        'minecraft:jungle_chest_boat', 'minecraft:mangrove_boat',
        'minecraft:mangrove_chest_boat', 'minecraft:minecart',
        'minecraft:oak_boat', 'minecraft:oak_chest_boat',
        'minecraft:powered_rail', 'minecraft:rail', 'minecraft:redstone_torch',
        'minecraft:spruce_boat', 'minecraft:tnt_minecart'
    },
    "building_blocks": {}
}


def id_set_conditioner(id_set) -> callable:
    """
    Use id set to filter the ids
    Parameters
    ----------
    id_set: either a string (exact name) or set of names
    """
    if isinstance(id_set, str):
        id_set = {id_set}

    def inner(key: str, val: Node) -> bool:
        nonlocal id_set
        return key in id_set

    return inner


def id_conditioner(_id: str) -> callable:
    assert isinstance(_id, str)

    def inner(key: str, val: Node) -> bool:
        nonlocal _id
        return _id in key

    return inner


def postfixes_conditioner(_ids: list) -> callable:

    def inner(key: str, val: Node) -> bool:
        nonlocal _ids
        print(key, [key[-len(_id):] for _id in _ids])
        return any(key[-len(_id):] == _id for _id in _ids)

    return inner


def name_category_conditioner(cat: str) -> callable:
    return id_set_conditioner(NAME_CATEGORIES[cat])


def init_pyviz_graph():
    net = Network(height="1500px",
                  width="100%",
                  directed=True,
                  bgcolor="#222222",
                  font_color="white")

    # print(misc_nx_graph.nodes)

    options = {
        "nodes": {
            "borderWidth": 0,
            "borderWidthSelected": 7,
            "font": {
                "size": 12,
            },
            "shape": "image",
            "size": 48,
            "brokenImage": "../item_icons/recipe.png"
        },
        "edges": {
            "color": {
                "inherit": True
            },
            "smooth": False
        },
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -100,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
                "enabled": True,
                "iterations": 1000
            }
        }
    }
    net.options = options
    return net
