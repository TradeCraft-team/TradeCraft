"""
Find leaf node spectrum
"""
import sys
import numpy as np
from fractions import Fraction

sys.path.append("../")
from ..craft_rules import (Graph, Node, preprocessing, multiplication,
                           reduction, base_graph)
from ..craft_rules.utils import init_pyviz_graph

BASE_GRAPH = base_graph(prefix="../craft_rules/")
INV_ITEMS = dict(
    (x, ii) for ii, x in enumerate(sorted(BASE_GRAPH.node_dict.keys())))
# print(INV_ITEMS)


def random_leaf_spec(node_name: str,
                     graph: Graph = BASE_GRAPH,
                     inv_items: dict = INV_ITEMS,
                     seed: int = 1729) -> np.ndarray:
    """
    Calculate leaf spec of a given node.
    """

    np.random.seed(seed)
    ret = np.zeros([len(inv_items)], dtype=Fraction)
    direction_record = np.zeros([len(inv_items)] * 2, dtype=int)
    target = graph[node_name]
    ret[inv_items[node_name]] = 1

    def temp_cond(key, val):
        return key == node_name

    subgraph = graph.subgraph(temp_cond)
    if target.node_type == "repcipe":
        extra = list(target.parents.keys())
    else:
        extra = []

    front = [node_name]
    while len(front) > 0:
        cur = front.pop(0)
        if graph[cur].node_type == "recipe":  # AND node
            out = list(graph[cur]._parents.keys())[0]
            temp = 1
            for item, cnt in graph[cur]._children.items():
                temp *= direction_record[inv_items[item], inv_items[out]]
            if temp:
                continue
            tmp_amount = ret[inv_items[cur]]
            print("===", cur, tmp_amount)
            ret[inv_items[cur]] = 0
            for item, cnt in graph[cur]._children.items():
                direction_record[inv_items[out], inv_items[item]] = 1
                ret[inv_items[item]] += tmp_amount * Fraction(*cnt)
                print(item, ret[inv_items[item]])
                front += [item]
        else:  # OR node
            if len(list(graph[cur]._children.keys())) == 0:
                continue
            parsed_or = np.random.choice(list(graph[cur]._children.keys()))
            tmp_amount = ret[inv_items[cur]]
            print("===", cur, tmp_amount)
            ratio = Fraction(*(graph[cur]._children[parsed_or]))
            ret[inv_items[parsed_or]] += tmp_amount * ratio
            print(parsed_or, ret[inv_items[parsed_or]])
            ret[inv_items[cur]] = 0
            front += [parsed_or]

    return ret


def node_entropy_initializer(feature, node, roster, graph):
    """
    """
    feature[roster[node.node_name]] = 0.
    return feature


def node_dummy_top_down(*data):
    return data[0]


def node_indicator_bottom_up(feature, node, roster, graph):
    feature[roster[node.node_name]] = 1
    return feature


def node_entropy_top_down(feature, node, roster, graph):
    """
    beta is the reciprocal of temporature
    """
    if len(node._children) == 0:
        return 0.
    beta = 1.
    temp = dict(
        (k, np.exp(-beta * v[0] / v[1])) for k, v in node._children.items())
    partition = sum(temp.values())
    # print(node.node_name, temp, partition)
    base = 0.
    entropy = 0.
    for k, v in node._children.items():
        temp[k] /= partition
        entropy += v[0] / v[1] * beta * temp[k]
        base += feature[roster[k]] * temp[k]

    feature[roster[node.node_name]] = np.log(partition) + entropy + base

    return feature


def breadth_manager_full(breadth, node, graph):
    """
    """
    for k, v in node.children.items():
        if not k.node_name in graph.node_dict:
            breadth += [k.node_name]
            graph.copy_node_skeleton(node)

            # print(len(graph.node_dict))
    return breadth


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


def reversed_subgraph(hands):

    def hand_condition(key, val) -> bool:
        return key in hands

    out_graph, feature = BASE_GRAPH.reversed_subgraph(hand_condition)
    return out_graph, feature


def main():

    # Example 1
    hands = {
        "minecraft:raw_iron": 7,
        "minecraft:oak_log": 2,
        # "minecraft:stick": 4,
        "minecraft:cobblestone": 2,
        "minecraft:redstone_block": 3,
        "minecraft:coal": 1
    }

    out_graph, _ = reversed_subgraph(hands)

    net = init_pyviz_graph()
    out_graph.draw_with_pyvis(net)
    net.show("problem1.html", notebook=False)


if __name__ == '__main__':
    # print(result:=random_leaf_spec("minecraft:iron_pickaxe", seed=1087))
    # for k, v in INV_ITEMS.items():
    #     if result[v] != 0:
    #         print(k, result[v])

    item = "minecraft:iron_ingot"

    # for node in BASE_GRAPH[item].children:
    #     print(node)

    # [TODO] CHECK correctedness!!!
    # ret = BASE_GRAPH.validate_single_step_crafting_LP(
    #     ["minecraft:stick", 4], [["minecraft:oak_planks", 2]])
    # print(ret)

    result = BASE_GRAPH.traverse_vectorize(id_conditioner("planks"),
                                           breadth_manager_full, [1],
                                           node_entropy_initializer,
                                           node_entropy_top_down,
                                           node_entropy_top_down)
    print([
        result[1][BASE_GRAPH.inv_key_dict[x]] for x in BASE_GRAPH.node_dict
        if "planks" in x
    ])

    print("=" * 80)
    import json
    with open("./temp_data/recipe_out.json", "r", encoding="utf8") as fp:
        recipes = json.load(fp)

    # GENERATING the second problem's crafting descents.
    # Example 2
    hands = {
        "minecraft:oak_planks": 1,
        "#minecraft:fuel": 1,
        "minecraft:iron_ore": 5,
        "minecraft:cherry_planks": 1
    }

    hands = {
        "minecraft:oak_planks": 1,
        "#minecraft:fuel": 1,
        "minecraft:iron_ore": 5,
        "minecraft:cherry_planks": 1
    }

    # Example 1
    hands1 = {
        "minecraft:raw_iron": 7,
        "minecraft:oak_log": 2,
        # "minecraft:stick": 4,
        "minecraft:cobblestone": 2,
        "minecraft:redstone_block": 3,
        "minecraft:coal": 1
    }

    out_graph, _ = reversed_subgraph(hands)

    net = init_pyviz_graph()
    BASE_GRAPH.draw_with_pyvis(net)
    net.show("problem1.html", notebook=False)
    exit()

    for k, node in out_graph.node_dict.items():
        if node.node_type == "recipe":
            print(node)

    # Tried on the first example
    hands = {
        "minecraft:redstone": 1,
        "minecraft:oak_planks": 4,
        "minecraft:stick": 4,
        "minecraft:cobblestone": 6,
        "minecraft:iron_ingot": 3,
        "minecraft:flint": 2
    }

    related_recipe = []
    for key, val in BASE_GRAPH.node_dict.items():
        if val.node_type != "recipe":
            continue
        skip = False
        for k, v in val._children.items():
            if k[0] != "#" and k not in hands:
                skip = True
                break
            elif len([x for x in BASE_GRAPH[k]._children if x in hands]) == 0:
                skip = True
                break

        if not skip:
            related_recipe += [x for x in recipes if x["recipe_name"] == key]

    with open("./temp_data/recipe_related.json", "w", encoding="utf8") as fp:
        fp.write(json.dumps(related_recipe, indent=4))

    print([x["recipe_name"] for x in related_recipe])
