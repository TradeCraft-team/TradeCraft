# -*- coding: utf-8 -*-
"""
Extracting necessary info
from raw recipe files from Minecraft Java 1.20
Raw data are stored in folder `./recipes`


"""
import json
import os
import pickle
import math
import networkx as nx
import sys
from fractions import Fraction
from pathlib import Path

if __name__ == '__main__' or __name__ == "process":
    from node import Node
    from node import multiplication as mul
    from node import reduction as red
    from graph import Graph, SRC_PATH
    from config import pr_args
else:
    from .node import Node
    from .node import multiplication as mul
    from .node import reduction as red
    from .graph import Graph, SRC_PATH
    from .config import pr_args

DATA_DIR = SRC_PATH.joinpath(pr_args["craft_rule_base_path"],
                             pr_args["craft_rule_choice"], "recipes/")

OUT_NAME = SRC_PATH / "temp_data" / "data.pkl"
TAG_DIR = SRC_PATH.joinpath(pr_args["craft_rule_base_path"],
                            pr_args["craft_rule_choice"], "tags/")

CRAFT_RULE_PREFIX = pr_args["craft_rule_prefix"] + ":"
CRAFT_RULE_LENGTH = len(CRAFT_RULE_PREFIX)
USEFUL_RECIPE_TYPES = [
    f"{CRAFT_RULE_PREFIX}stonecutting", f"{CRAFT_RULE_PREFIX}crafting_shaped",
    f"{CRAFT_RULE_PREFIX}smelting", f"{CRAFT_RULE_PREFIX}crafting_shapeless",
    f"{CRAFT_RULE_PREFIX}blasting", f"{CRAFT_RULE_PREFIX}campfire_cooking",
    f"{CRAFT_RULE_PREFIX}smoking", f"{CRAFT_RULE_PREFIX}smithing_transform"
]
USEFUL_TAGS = [
    # 'fluids',
    # 'entity_types',
    # 'mineable',
    'instrument',
]
TAG_ALIASES = {}


def process_single_item_tag(val) -> str:
    """
        ONE item for sure
        "xxx" / {"item":"xxx"} / {"tag": "xxx"}
        -> {"value": "xxx"}
        """

    ret = val.get(
        "item",
        val if isinstance(val, str) else "#" + val.get("tag", "_ERROR_"))
    if ret == "#_ERROR_":
        print("ERROR in loading", val)
    # if ret[0] == "#":
    #     print("tag:", ret, "is parsed.")
    return ret


def process_homogeneous_item_tag(lst) -> list:
    """
        "xxx" / {"xx":"xxx"} / ["xxx"] / [{"xx":"xxx"}, "xxx"]
        """
    if isinstance(lst, (list, tuple)):
        return [process_single_item_tag(item) for item in lst]
    return [process_single_item_tag(lst)]


def process_general_list(lst) -> list:
    R"""
        "xxx" / {"xx":"xxx"} / ["xxx"] / [{"xx":"xxx"}, "xxx"]
        / {"count":c, [homog]} / [{"count":c, [homog]}]


        Returns
        -------
        [{"count":count,
          "value": [equivalent-item/tag-1, equivalent-item/tag-2]}, ...]
        """
    if not isinstance(lst, (list, tuple)):
        tmp = [lst]
    else:
        tmp = lst

    # if not any(("count" in x) for x in lst):
    temp_list = [{
        "count": (1, 1) if not isinstance(x, dict) else (x.get("count", 1), 1),
        "value":
        process_homogeneous_item_tag(x)
    } for x in tmp]
    out_list = []
    out_item_names = set([tuple(sorted(x["value"])) for x in temp_list])
    for name in out_item_names:
        amt = sum([
            Fraction(*x["count"]) for x in temp_list
            if tuple(sorted(x["value"])) == name
        ])
        out_list += [{
            "count": (amt.numerator, amt.denominator),
            "value": name
        }]

    return out_list


def load_recipes(prefix: str = DATA_DIR) -> list:
    """
    Parameters
    ----------
    prefix : crafting_goal directory


    Returns
    -------
    out : list of all dict objects
    """
    print(prefix)
    recipe_fnames = list(os.walk(prefix))[0][2]
    out = []
    for fname in recipe_fnames:
        with open(Path(prefix) / fname, "r", encoding="utf8") as fptr:
            outitem = json.load(fptr)
            outitem["recipe_name"] = fname[:-5]
            if outitem["type"] not in USEFUL_RECIPE_TYPES:
                continue
            out += [outitem]

    # types = list(set(x["type"] for x in out))
    # print(types, "\n")
    # i = 4
    # print(
    #     types[i],
    #     set(tuple(x.keys()) for x in out
    #         if x["type"] == f"{CRAFT_RULE_PREFIX}blasting"))
    # print()

    # print(
    #     set((x.get("category", "NULL"), tuple(x.keys())) for x in out
    #         if "ingredient" not in x))
    # print()
    # print(set((x["type"]) for x in out if "group" in x))
    # print([x for x in out if x["type"] == f"{CRAFT_RULE_PREFIX}smithing_transform"])
    return out


def load_tags(prefix: str = TAG_DIR, domain=None) -> dict:
    """
    Recursively load tags:

    Returns
    -------
    dictionary as (name_of_tag, [{"value":item/tag, "count":count},...])
    """

    dir_struct = list(os.walk(prefix))
    if not os.path.exists(os.path.join(prefix, "_temp_tags")):
        os.mkdir(os.path.join(prefix, "_temp_tags"))
    unsolven = {}
    for folder in dir_struct:
        if domain and not any(x in folder[0] for x in domain):
            continue
        prefix_loc = folder[0]
        for filename in folder[2]:
            with open(prefix_loc + "/" + filename, "r",
                      encoding="utf8") as fptr:
                val = json.load(fptr)["values"]

            val = [{
                "count": 1,
                "value": x
            } if isinstance(x, str) else x for x in val]
            val = [{
                "value": x["value"],
                "count": (x["count"], 1)
            } for x in val]
            unsolven[f"#{CRAFT_RULE_PREFIX}" + filename[:-5]] = val

            # if "logs" in filename:
            #     print(filename, val)
    # print(unsolven)
    return unsolven


def solve_tags(unsolven: dict) -> dict:
    """
    Raw tags also contains tag-reference. We solve them into item level.
    """
    solven = {}
    tag_count = 0
    print(sum(len(x) for x in unsolven.values()), len(unsolven))
    while len(unsolven) > len(solven) and tag_count < 100:
        tag_count += 1
        print(tag_count, len(solven))
        for key, val in unsolven.items():
            finished = True
            temp = []
            for item in val:
                # print(item)
                value = item["value"]
                count = item["count"]
                if value[0] != "#":
                    temp += [item]
                elif value in solven:
                    count = Fraction(count[0] /
                                     count[1]).limit_denominator(500)
                    count = [count.numerator, count.denominator]
                    temp += [{
                        "count": mul(x["count"], count),
                        "value": x["value"]
                    } for x in solven[value]]
                else:
                    temp += [item]
                    finished = False
            if finished:
                solven[key] = sorted(temp, key=lambda x: x["value"])
            else:
                unsolven[key] = temp

    for k, v in solven.items():
        TAG_ALIASES[
            "#" + "-".join(sorted([x["value"][CRAFT_RULE_LENGTH:]
                                   for x in v]))] = k

    print(sum(len(x) for x in solven.values()))
    if len(unsolven) > len(solven):
        for k in unsolven:
            if k not in solven:
                print(k, unsolven[k])
    return solven


def process_recipe(recipe: dict) -> dict:
    """
    Process single recipe
    """

    if "cobblestone_slab" in recipe["result"]:
        print(recipe)
    ret = {"recipe_name": "$" + recipe["recipe_name"]}
    for x in ["type", "category", "group"]:
        ret[x] = recipe.get(x, "")

    if recipe["type"] not in USEFUL_RECIPE_TYPES:
        return {}

    if isinstance(output := recipe.get("result", ""), str):
        if len(output) == 0:
            print("ERROR: no result in the recipe")
        ret["output"] = {"count": (recipe.get("count", 1), 1), "value": output}
        # {output: 1}  # {"count": 1, "item": output}
    else:
        ret["output"] = {"value": output["item"]}
        ret["output"]["count"] = (output.get("count", 1), 1)
        # Another EXAMPLE below, does not affect the game.
        if ret["output"]["value"] == f"minecraft:cobblestone_slab":
            print(recipe)
        # {output["item"]: output.get("count", 1)}  # output

    ret["input"] = []
    if "key" in recipe:
        pattern = "".join(recipe["pattern"])
        for k, v in recipe["key"].items():
            cnt = pattern.count(k)
            next_item = {"count": (cnt, 1), "value": []}
            if isinstance(v, dict):
                vals = [v]
            else:
                vals = v

            next_item["value"] = process_homogeneous_item_tag(vals)
            # for val in vals:
            #     next_item["value"] += list(val.values())
            ret["input"] += [next_item]
        return ret

    if "ingredients" in recipe:
        ret["input"] += process_general_list(recipe["ingredients"])

    elif "ingredient" in recipe:
        ret["input"] += process_general_list([recipe["ingredient"]])
    elif "template" in recipe:
        ret["input"] += process_general_list(recipe["template"])
        ret["input"] += process_general_list(
            recipe["addition"]) if "addition" in recipe else []
        ret["input"] += process_general_list(
            recipe["base"]) if "base" in recipe else []

    # [TODO] fuel mechanism: I need to think how this can be solven in different rules.
    if recipe.get("cookingtime", 600) < 600:
        ret["input"] += [{"count": (1, 8), "value": ["#minecraft:fuel"]}]

    return ret


def build_graph(recipes: list, raw_tags: list) -> dict:
    """
    Build tree using Nodes.

    recipes and tags must be pre-processed.

    Returns
    -------
    dict: key is node_name, value is the Node itself.
    """
    used_tags = set()
    node_dict = {}
    raw_tags = solve_tags(raw_tags)

    def get_new_node(node_name: str) -> Node:
        """
        Use existing node or create new node.
        """
        nonlocal node_dict, used_tags
        node_type = "tag" if node_name[0] == "#" else "item"
        if node_name not in node_dict:
            target = Node(node_name, node_type)
            if target.node_type == "tag":
                used_tags.add(node_name)
            node_dict[node_name] = target
        else:
            target = node_dict[node_name]
        return target

    ref_tags = dict((tuple(sorted([x["value"] for x in v])), k)
                    for k, v in raw_tags.items())
    # print(ref_tags["#minecraft:coals"])
    for recipe in recipes:
        name = recipe["recipe_name"]
        node = Node(name, "recipe", **recipe)
        # name = "$" + node.gen_random_node_name()
        node_dict[name] = node
        # OUTPUT part
        out = get_new_node(recipe["output"]["value"])
        cnt_pair = recipe["output"]["count"]
        node.edge_to(out, self_amount=cnt_pair[1], other_amount=cnt_pair[0])

        # INPUT part
        for ingredient in recipe["input"]:
            count = ingredient["count"]
            value = sorted(ingredient["value"])

            if tuple(value) in ref_tags:
                value = [ref_tags[tuple(value)]]
            if len(value) > 1:
                # add a temporary tag node.
                temp_tag_name = Node.gen_md5_node_name("-".join(sorted(value)))
                tag_name = "#" + "-".join(
                    sorted([x[CRAFT_RULE_LENGTH:] for x in value]))
                if tag_name in TAG_ALIASES:
                    tag_name = TAG_ALIASES[tag_name]

                child = get_new_node(tag_name)
                raw_tags[tag_name] = [{
                    "count": (1, 1),
                    "value": x
                } for x in value]
                with open(
                        os.path.join(TAG_DIR,
                                     "_temp_tags/" + temp_tag_name + ".json"),
                        "w") as fp:
                    json.dump({"values": sorted(value)}, fp, indent=2)
            else:
                child = get_new_node(value[0])
            child.edge_to(node, count[1], count[0])

    print("KEYS", len(list(node_dict.keys())))
    # Dealing with tags, they are not in the graph yet.

    tags = solve_tags(raw_tags)
    for tag_name in used_tags:
        for item_pair in tags[tag_name]:
            item_name = item_pair["value"]
            item_count = item_pair["count"]
            item = get_new_node(item_name)
            item.edge_to(node_dict[tag_name],
                         self_amount=item_count[0],
                         other_amount=item_count[1])

    print("KEYS", len(list(node_dict.keys())))
    return node_dict


def load_processed_recipes(recipe_json_filename):
    """
    Load the processed_recipes
    """
    with open(recipe_json_filename, "r") as fp:
        recipes = json.load(fp)


def preprocessing(recipe_prefix=DATA_DIR, tag_prefix=TAG_DIR) -> Graph:
    """
    1. Read all recipes
    2. Read all tags and expand all tag-references
    3. identify all items
    4. make the graph.
    5. return the dictionary of pairs (name, object)
    """
    recipes = load_recipes(recipe_prefix)
    raw_tags = load_tags(tag_prefix, domain=None)
    tags = solve_tags(raw_tags)

    # if not os.path.exists("./temp_data/solven_tags.json"):

    path = os.path.normpath(recipe_prefix)
    path = os.path.dirname(path)

    temp_data_path = os.path.join(path, "temp_data")
    solven_tags_file = os.path.join(temp_data_path, "solven_tags.json")

    if not os.path.exists(temp_data_path):
        os.makedirs(temp_data_path)

    # if not os.path.exists(os.path.join(path, "./temp_data/solven_tags.json")):
    with open(solven_tags_file, "w", encoding="utf8") as fptr:
        for k, val in tags.items():
            fptr.write(f"{k},\n{val},\n")

    processed_recipes = [process_recipe(recipe) for recipe in recipes]
    with open(os.path.join(path, "temp_data/recipe_out.json"),
              "w",
              encoding="utf8") as fptr:
        fptr.write(json.dumps(processed_recipes, indent=4))

    node_dict = build_graph(processed_recipes, raw_tags)
    graph = Graph()
    graph.load_dict(node_dict)
    return graph


def base_graph(prefix="./", recipe_prefix=DATA_DIR, tag_prefix=TAG_DIR):
    try:
        with open(os.path.join(prefix, "temp_data/graph_structure.pkl"),
                  "rb") as fileptr:
            nodes = pickle.load(fileptr)
        graph = Graph()
        graph.load_dict(nodes)
        return graph
    except Exception as e:
        print(e)
        return preprocessing(
            Path(prefix) / recipe_prefix,
            Path(prefix) / tag_prefix)


def attributes_stats_analysis(node_dict):
    from collections import Counter
    c1 = Counter()
    c2 = Counter()
    c3 = Counter()
    c4 = Counter()
    for key, val in node_dict.items():
        c1[val.attributes['group']] += 1
        c2[val.attributes['category']] += 1
        c3[val.attributes['type']] += 1
        c4[val.attributes['node_type']] += 1
    print('group', c1.most_common(10))
    print('category', c2.most_common(10))
    print('type', c3.most_common(10))
    print('node_type', c4.most_common(10))


def nodes_crafting_path(graph: nx.DiGraph):
    for node1 in graph.nodes:
        for node2 in graph.nodes:
            try:
                print(nx.shortest_path(graph, node1, node2))
            except:
                continue


if __name__ == "__main__":
    graph = preprocessing()
    nodes = graph.node_dict
    with open("nodenames.txt", 'w') as fp:
        for x in nodes:
            fp.write(x)
    exit()
    # print("=" * 20, "Testing", "=" * 20)
    wd = nodes[f"{CRAFT_RULE_PREFIX}white_dye"]  # EXAMPLE
    # print("\n".join(wd._parents))
    # print('-' * 60)
    # print("\n".join(wd._children))
    # with open("./temp_data/graph_structure.pkl", "wb") as fileptr:
    #     pickle.dump(nodes, fileptr)

    attributes_stats_analysis(nodes)

    def filter1(key, val):
        return "boat" in key

    def group_filter(key, node):

        return node.attributes['category'] == "food" and node.attributes[
            'node_type'] != 'tag'

    subgraph = graph.subgraph(filter1, "BOATS")
    # print(subgraph.node_dict.keys())
    sub_nx = subgraph.to_networkx()
    # nodes_crafting_path(sub_nx)

    from utils.graph_viz_utils import viz_net
    # viz_net(subgraph.node_dict)

    food_subgraph = graph.subgraph(group_filter, "FOOD")
    viz_net(food_subgraph.node_dict)
    food_nx = food_subgraph.to_networkx()
    nodes_crafting_path(food_nx)
