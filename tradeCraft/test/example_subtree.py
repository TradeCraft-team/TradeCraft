"""
Example of subtree
[NOTE] MOVE to test
"""
import os
import sys

sys.path.append("..")

from src.craft_rules.process import preprocessing
from src.craft_rules.graph import Graph, ICON_PREFIX, PROCESS_ICON_KEY
from src.craft_rules.node import Node
from src.craft_rules.utils import *

from pyvis.network import Network

FULL_GRAPH = None


def filter_cond_misc(key: str, val: Node) -> bool:

    return val.attributes["category"] == "food"


def filter_cond_dye(key: str, val: Node) -> bool:

    return val.attributes["group"] == "yellow_dye"


def filter_cond_boat(key: str, val: Node) -> bool:
    return "boat" in key


def filter_cond_chest(key: str, val: Node) -> bool:
    return "chest" in key


def filter_redstone(key: str, val: Node) -> bool:
    return "redstone" in key


def main(cond=filter_cond_misc,
         ignore_condition=lambda *x: False,
         reverse_condition=None):
    global FULL_GRAPH
    FULL_GRAPH = preprocessing()
    small_graph, _ = FULL_GRAPH.reversed_subgraph(reverse_condition)
    misc_graph = small_graph.subgraph(cond, ignore_condition=ignore_condition)
    misc_nx = misc_graph.to_networkx()
    return misc_nx, misc_graph


if __name__ == '__main__':
    hands = {
        "minecraft:iron_ore": 7,
        "minecraft:oak_log": 2,
        # "minecraft:stick": 4,
        "minecraft:cobblestone": 2,
        "minecraft:redstone_block": 3,
        "minecraft:coal": 1
    }

    def start_condition(key, val) -> bool:
        return key in hands

    # misc_nx_graph = main(filter_cond_misc)
    misc_nx_graph, misc_graph = main(  # name_category_conditioner("food"),
        # misc_nx_graph = main(name_category_conditioner("transportation"),
        id_set_conditioner([
            "minecraft:shield", "minecraft:detector_rail",
            "minecraft:oak_planks", "minecraft:coal"
        ]),
        ignore_condition=postfixes_conditioner([
            "fuel",
            "coal",
            "from_smelting",
            "nugget",
            "from_blasting",
        ]),
        reverse_condition=start_condition)

    # Create a new interactive network graph
    net = Network(height="1500px",
                  width="100%",
                  directed=True,
                  bgcolor="#fff",
                  font_color="#000")

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
    exist_nodes = []
    for key, val in misc_graph.node_dict.items():
        exist_nodes += [key]
        net.add_node(key,
                     label=key,
                     shape="image",
                     image=os.path.join(ICON_PREFIX, PROCESS_ICON_KEY(key)))

    for key, val in misc_graph.node_dict.items():
        for parent, value in val._parents.items():
            if val.node_type in ["tag", "recipe"]:
                v = value[1] / value[0]
            else:
                v = value[0] / value[1]
            net.add_edge(key, parent, value=v)

    fuel = FULL_GRAPH.node_dict["#minecraft:fuel"]
    for child, value in fuel._children.items():

        if child in exist_nodes:
            net.add_edge(child, "#minecraft:fuel", value=value[0] / value[1])

    # net.add_edge("minecraft:coal", "#minecraft:fuel", value=1)

    # net.from_nx(misc_nx_graph)
    net.show("subgraph_new.html", notebook=False)
