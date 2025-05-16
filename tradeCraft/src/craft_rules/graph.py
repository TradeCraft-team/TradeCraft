"""
Graph of Nodes
"""
import pickle
import os
import numpy as np
from scipy.optimize import linprog
from copy import deepcopy
from typing import List
from collections.abc import Callable, Iterable
from fractions import Fraction
from pathlib import Path
if __name__ in {'__main__', "graph"}:
    from node import Node, add_method, to_fraction
    from utils import logger
    from config import pr_args
else:
    from .node import Node, add_method, to_fraction
    from .utils import logger
    from .config import pr_args
try:
    import networkx as nx
    _LOADED_NETWORKX = True
except Exception:
    _LOADED_NETWORKX = False

try:
    import igraph as ig
    _LOADED_IGRAPH = False
except Exception:
    _LOADED_IGRAPH = False

COLOR = {"tag": "#00ff1e", "item": "#ee9999", "recipe": "#8888ee"}
GROUP = {"tag": 0, "item": 1, "recipe": 2}

FILE_PATH = Path(__file__).resolve()
SRC_PATH = Path(__file__).parents[1].resolve()

ICON_PREFIX = SRC_PATH.joinpath(pr_args["craft_rule_base_path"],
                                pr_args["craft_rule_choice"], "item_icons/")


def PROCESS_ICON_KEY(key):
    ext = pr_args["icon_format"]
    if key[0] == "$":
        return f"recipe.{ext}"
    if key[0] == "#":
        return f"tag.{ext}"
    names = key.split(":")
    # print(names)
    return names[1] + f".{ext}"


class Graph:
    """
    Node Graph
    """

    def __init__(self, graph_name: str = "None"):
        """
        Initialize.
        """
        self.graph_name = graph_name

        self.node_dict = {}
        self._key_dict = {}
        self._inv_key_dict = {}

    def copy_node_skeleton(self, node: Node):
        """
        Add a node to graph, forgetting all edges.
        """
        if node.node_name not in self.node_dict:
            self.node_dict[node.node_name] = Node(node.node_name,
                                                  **node.attributes)

    def load_dict(self, node_dict: dict):
        """
        Load from a dictionary of Nodes.
        """
        self.node_dict = node_dict

    def pickle_graph(self, name: str = "./temp_data/graph.pkl"):
        """
        Pickle current graph
        """
        with open(name, "wb") as fp:
            pickle.dump(self.node_dict, fp)

    def load_pickle(self, name: str):
        """
        Load from a pickle file.
        """
        assert os.path.exists(
            name), f"The given file name {name} does not exist."
        with open(name, "rb") as fp:
            self.load_dict(pickle.load(fp))
            for key, val in self.node_dict.items():
                val.fully_reconstruct(self.node_dict)

    def to_networkx(self) -> nx.classes.digraph.DiGraph:
        """
        Translate to a networkx graph.
        """
        if not _LOADED_NETWORKX:
            print("Package networkx is required but not installed.")
            return None
        graph = nx.DiGraph()
        graph.add_nodes_from(
            dict((key, {
                "title": key,
                "group": GROUP[val.node_type],
                "shape": "image",
                "image": str(ICON_PREFIX / PROCESS_ICON_KEY(key)),
                "color": COLOR[val.node_type]
            }) for key, val in self.node_dict.items()))
        for key, val in self.node_dict.items():
            graph.add_edges_from([(key, pnt.node_name) for pnt in val.parents])

        self.nxgraph = graph
        return self.nxgraph

    def to_igraph(self):
        """
        Translate to igraph format.
        """
        if not _LOADED_IGRAPH:
            print("Package igraph is required but not installed.")
            return None

    def set_key_dict(self, keys: Iterable[str]):
        """
        Set the key dictionary and inverse key dictionary
        """
        if isinstance(keys, dict):
            self._keys_dict = deepcopy(keys)
        else:
            keys = sorted(list(keys))
            self._keys_dict = dict((ii, key) for ii, key in enumerate(keys))

        self._inv_key_dict = dict((v, k) for k, v in self._keys_dict.items())

    @property
    def inv_key_dict(self) -> dict:
        """
        """
        if len(self._inv_key_dict) != len(self.node_dict):
            print("`inv_key_dict` is not updated, use str order to update it!")
            self.set_key_dict(self.node_dict.keys())

        return self._inv_key_dict

    def __getitem__(self, key: str) -> Node:
        """
        Get any graph node from self.node_dict.

        Parameters
        ----------
        key: str
        """
        return self.node_dict[key]

    def subgraph(self,
                 condition: Callable[..., bool],
                 name: str = "sub",
                 ignore_condition: callable = lambda *x: False):
        """
        Build subgraph expanding from the nodes satisfying `condition`.

        Note: if condition filters out recipes directly, then the direct
        output of the recipe is included in the subgraph. E.g., filtering
        on "group"=="yellow_dye" (resulting on two recipes) results in a
        subgraph containing "minecraft:yellow_dye" item.

        Parameters
        ----------
        condition: callable, a function which takes a `(key:str, val:Node)`
                   instance and output a boolean. `True` represents to take
                   the node as basic node.
        name: str, the name of the subgraph
        """
        out_graph = Graph(name)
        front = []
        for key, val in self.node_dict.items():
            if not condition(key, val):
                continue
            out_graph.copy_node_skeleton(val)
            if val.node_type == "recipe":
                for parent, cnt in val.parents.items():
                    # suppose there is only one pair in parents.
                    out_graph.copy_node_skeleton(parent)
                    out_graph.node_dict[val.node_name].edge_to(
                        out_graph.node_dict[parent.node_name],
                        other_amount=cnt)
            front += [key]

        while len(front) > 0:
            cur = self.node_dict[cid := front.pop(0)]
            if ignore_condition(cur.node_name, cur):
                print("IGNORED:", cur.node_name)
                continue
            # print(cid, len(front))
            for child, cnt in cur.children.items():
                if child.node_name not in out_graph.node_dict:
                    out_graph.copy_node_skeleton(child)
                    front += [child.node_name]
                out_graph.node_dict[child.node_name].edge_to(
                    out_graph.node_dict[cur.node_name],
                    other_amount=cnt[0],
                    self_amount=cnt[1])

        return out_graph

    def traverse_vectorize(
        self, init_condition: Callable[..., bool],
        breadth_manager: Callable[[list, Node, ...], list], feature_size: list,
        node_feature_initializer: Callable[[np.ndarray, Node, dict, ...],
                                           np.ndarray],
        node_feature_top_down: Callable[[np.ndarray, Node, dict, ...],
                                        np.ndarray],
        node_feature_bottom_up: Callable[[np.ndarray, Node, dict, ...],
                                         np.ndarray]):
        """
        init_condition: function(key:str, val:Node) -> bool
        breadth_manager: function(breadth:List[str], current:Node)->List[str]
        node_feature_initializer: function(feature:np.ndarray, current:Node, self.inv_key_dict:dict) -> np.ndarray
        node_feature_updater: function(feature:np.ndarray, current:Node, self.inv_key_dict:dict) -> np.ndarray
        """
        out_graph = Graph()
        breadth = []
        node_feature = np.zeros([len(self.node_dict)] + feature_size)
        for key, val in self.node_dict.items():
            if init_condition(key, val):
                out_graph.copy_node_skeleton(val)
                breadth += [key]
                # node_feature is mutable so return-value could be discarded
                node_feature_initializer(node_feature, val, self.inv_key_dict,
                                         out_graph)

        top_order = []
        while len(breadth) > 0:
            cur = self.node_dict[cid := breadth.pop(0)]

            top_order += [cid]
            # for child, cnt in cur.children.items():
            breadth_manager(breadth, cur, out_graph)
            node_feature_top_down(node_feature, cur, self.inv_key_dict,
                                  out_graph)

        # print(top_order)
        for node_name in top_order[::-1]:
            node_feature_bottom_up(node_feature, self.node_dict[node_name],
                                   self.inv_key_dict, out_graph)

        return out_graph, node_feature

    def reversed_subgraph(self,
                          condition: Callable[..., bool],
                          name: str = "sub",
                          ignore_condition: callable = lambda *x: False):
        """
        Reverse search: from ingredients, see what can be obtained, unlimited.
        """
        front = None

        def breadth_manager(breadth, node, out_graph) -> list:
            nonlocal front

            if ignore_condition(node):
                print(node.node_name, "is ignored")
                return breadth
            if front is None:
                front = set(breadth + [node.node_name])
            for parent, val in node.parents.items():
                if parent.node_type != "recipe":
                    # print(parent.node_name)
                    out_graph.copy_node_skeleton(parent)
                    out_graph.node_dict[node.node_name].edge_to(
                        out_graph.node_dict[parent.node_name],
                        self_amount=val[1],
                        other_amount=val[0])
                    breadth += [parent.node_name
                                ] if parent.node_name not in front else []
                    front.add(parent.node_name)
                    continue
                can_craft = True
                for child in parent.children:
                    if child.node_name not in front:
                        can_craft = False
                if can_craft:
                    out_graph.copy_node_skeleton(parent)
                    for child, value in parent.children.items():
                        out_graph.node_dict[child.node_name].edge_to(
                            out_graph.node_dict[parent.node_name],
                            self_amount=value[0],
                            other_amount=value[1])
                    breadth += [parent.node_name
                                ] if parent.node_name not in front else []
                    front.add(parent.node_name)
                    # print(len(breadth))
            return breadth

        return self.traverse_vectorize(
            init_condition=condition,
            breadth_manager=breadth_manager,
            feature_size=[],
            node_feature_initializer=lambda *x: x[0],
            node_feature_top_down=lambda *x: x[0],
            node_feature_bottom_up=lambda *x: x[0],
        )

    def draw_with_pyvis(self, net):
        """
        Output graph structure to pyvis
        net: pyvis.network.Network
        """

        for key, val in self.node_dict.items():
            net.add_node(key,
                         label=key,
                         shape="image",
                         image=str(ICON_PREFIX / PROCESS_ICON_KEY(key)))

        for key, val in self.node_dict.items():
            for parent, value in val._parents.items():
                net.add_edge(key, parent, value=value[1] / value[0])

    def validate_single_step_crafting_old(self,
                                          target: list,
                                          resource: List[list],
                                          strict: bool = True) -> bool:
        """
        Validate the single step precisely, also checking multiplicity.

        strict: bool, if True, only exact crafting recipe is allowed.
                      if False, only checks sufficiency of resources.
        """
        eps = 1e-6
        if target[0] not in self.node_dict:
            return False
        tgt = self.node_dict[target[0]]
        tgt_cnt = target[1]
        if tgt_cnt.denominator != 1:
            logger.info(
                "Denominator != 1, crafting target must be an integer.")
            return
        assert tgt.node_type == "item", "Crafting target must be an item"

        def dfs_expand_tag(node: Node, cnt: Fraction) -> dict:
            if node.node_type == "item":
                return {node.node_name: cnt}
            ret = {}
            for subnode, subcnt in node.children.items():
                # print("SUBNODE", subnode, subcnt)
                ret.update(dfs_expand_tag(subnode, cnt * to_fraction(subcnt)))
                # Fraction(subcnt[0] / subcnt[1]).limit_denominator(50000)
            return ret

        for recipe, count in tgt.children.items():
            # print(recipe.node_name, count, recipe._children, recipe._parents)
            recipe_repeats = to_fraction(count) * tgt_cnt
            flag = True
            for item, item_cnt in recipe.children.items():
                ingredient = dfs_expand_tag(
                    item,
                    to_fraction(item_cnt) * recipe_repeats)
                # print("Ingredient:", ingredient)
                total_item_cnt = 0
                for (x, c) in resource:
                    if x in ingredient:
                        total_item_cnt += c / ingredient[x]
                    print(x, c, ingredient.get(x, -1), total_item_cnt,
                          total_item_cnt < 1, flag, item_cnt)

                if strict:
                    if abs(total_item_cnt - 1) > eps:
                        flag = False
                        break
                else:
                    if total_item_cnt < 1 - eps:
                        flag = False
                        break

            if flag:
                return True

        return False

    def validate_single_step_crafting(self,
                                      target: list,
                                      resource: List[list],
                                      strict: bool = True) -> bool:
        """
        """
        try:
            return self.validate_single_step_crafting_LP(
                target, resource, strict)
        except Exception as e:
            print(e)
            return self.validate_single_step_crafting_old(
                target, resource, strict)

    def validate_single_step_crafting_LP(self,
                                         target: list,
                                         resource: List[list],
                                         strict: bool = True) -> bool:
        """
        Validate the single step precisely, also checking multiplicity.
        VIA linear programming

        strict: bool, if True, only exact crafting recipe is allowed.
                      if False, only checks sufficiency of resources.

        ## Translating recipe-matching into Linear Programming:
        - Let there be `n` tags in the input of a recipe, `m` items in resource.
        - Let `M` be an `n*m` matrix representing the relations between tag and item,
        i.e. `M[i,j]` represents the amount that one item-j can be treated as how much tag-i.
        `M[i,j]==0` if item-j is not in the list of tag-i.
        - Let `r[i]` be the amount of tag-i required in recipe.
        - Let `c[j]` be the amount of item-j in the resource.
        - Let `P` be a matrix representing the partition of items into tags, or in the crafting,
        `P[i,j]` represents how much item-j is used as tag-i in the recipe.

        Then we have constraints:
        `\sum_{i}(P[i,j]) <= c[j]` and `\sum_{j}(P[i,j]*M[i,j]) >= r[i]`.
        Using one of them as objective and others as constraints, we can write a linear
        programming problem whose solution represents the sufficiency of the crafting.

        E.g.: We use
        `\sum_{i}(P[i,j]) <= c[j]` for all j and `\sum_{j}(P[i,j]*M[i,j]) >= r[i]` for all but last i
        as CONSTRAINTS and set
        `L(P) := \sum_{j}(P[n,j]*M[n,j]) - r[n]`
        as OBJECTIVE.
        then
        - if `max(L(P)) == 0` and `M[i,j]==0` implies `P[i,j]==0` for all (i,j), then the solution
        is exact, meaning the given resource fits the recipe exactly.
        - if `max(L(P)) < 0` then the resource is insufficient.
        - otherwise, we know there are extra resrouce for the recipe.
        """
        eps = 1e-5
        if target[0] not in self.node_dict:
            return False
        tgt = self.node_dict[target[0]]
        tgt_cnt = target[1]
        if tgt_cnt.denominator != 1:
            logger.info(
                "Denominator != 1, crafting target must be an integer.")
            return
        assert tgt.node_type == "item", "Crafting target must be an item"

        from fractions import Fraction

        def dfs_expand_tag(node: Node, cnt: Fraction) -> dict:
            if node.node_type == "item":
                return {node.node_name: cnt}
            ret = {}
            for subnode, subcnt in node.children.items():
                # print("SUBNODE", subnode, subcnt)
                ret.update(dfs_expand_tag(subnode, cnt * to_fraction(subcnt)))
                # Fraction(subcnt[0] / subcnt[1]).limit_denominator(50000))
            return ret

        ever_concluded = False
        for recipe, count in tgt.children.items():
            try:
                recipe_repeats = to_fraction(count) * tgt_cnt
                print("RECIPE, REPEATS", recipe, recipe_repeats)

                if recipe_repeats.denominator != 1:
                    # [TODO] Make every value Fraction.
                    continue
                flag = True
                n, m = len(recipe.children), len(resource)
                cost = np.zeros([n, m], dtype=np.float64)
                row_sums = np.ones([n], dtype=np.float64)
                col_sums = np.zeros([m], dtype=np.float64)

                for i, (item, item_cnt) in enumerate(recipe.children.items()):
                    print(i, item.node_name, item_cnt[0] / item_cnt[1])
                    # row_sums[i] = np.float64(item_cnt[0]/item_cnt[1])
                    ingredient = dfs_expand_tag(
                        item,
                        to_fraction(item_cnt) * recipe_repeats)
                    # print("Ingredient:", ingredient)

                    for j, (x, c) in enumerate(resource):
                        cost[i, j] = np.float64(
                            1 / ingredient[x]) if x in ingredient else 0
                        print(j, cost[:, j])

                for j, (x, c) in enumerate(resource):
                    col_sums[j] = np.float64(c)

                null = np.zeros_like(cost)
                null[-1, :] = -cost[-1, :]
                obj_coef = null.reshape(-1).copy()
                constr_A = (np.ones(n, dtype=np.float64).reshape([-1, 1, 1]) *
                            np.eye(m, dtype=np.float64).reshape([1, m, m]))
                constr_A = constr_A.reshape([-1, m]).T
                null = np.zeros([n, m, n - 1], dtype=np.float64)
                for i in range(n - 1):
                    null[i, :, i] = -cost[i, :]
                constr_A = np.concatenate(
                    [constr_A, null.reshape([-1, n - 1]).T], axis=0)
                constr_B = np.concatenate([col_sums, -row_sums[:-1]])
                print(constr_A, constr_B, obj_coef)
                results = linprog(c=obj_coef,
                                  A_ub=constr_A,
                                  b_ub=constr_B,
                                  bounds=[(0, None)] * (n * m),
                                  method='highs-ds')
                print(results, results.fun, results.status, results.x)
                if abs(results.fun + 1) < eps:
                    return True
            except Exception as e:
                print("LP exception:")
                logger.exception(e)

            raise Exception("NO POSITIVE CONCLUSION FROM LP")
        return False
