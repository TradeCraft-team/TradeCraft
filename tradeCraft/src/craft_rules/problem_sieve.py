"""
Problem Searching.

Basic version.
"""

from abc import ABC

import random
import json
from typing import Dict
from .tree_search import FULL_GRAPH, HandResource, BFS
from .graph import Graph, SRC_PATH
from .node import Node
from .utils import id_set_conditioner, init_pyviz_graph

from ..utils import lint_to_fullname, lint_to_simplename


class ProblemSieve(ABC):
    """Basic Problem Sieve"""

    save_path = (SRC_PATH.parent / "data" / "search").resolve().mkdir(
        parents=True, exist_ok=True)

    def __init__(self, *args, **kwargs):
        """initialize."""
        self.graph = kwargs.get("graph", FULL_GRAPH)
        self.search_method = kwargs.get("search_method", BFS)
        self.save_path = kwargs.get("save_path", self.save_path)

    def sample_targets(self, n_players=2, n_prob=10) -> set:
        """Sample targets."""
        problem_set = set()
        while len(problem_set) < n_prob:
            target = []
            for _ in range(n_players):
                # choose a node of type "item", randomly.
                while (tgt := random.choice(list(
                        self.graph.node_dict.values()))).node_type != "item":
                    pass
                target += [tgt.node_name]
            problem_set.add(tuple(target))

        return problem_set

    def target_to_graph(self, target: list, **kwargs) -> Graph:
        """Use graph traversing."""
        init_cond = id_set_conditioner(target)
        # Should there be a stop? Assigning MC:fuel might
        # block the transition to LAlchemy2.
        stop_cond = id_set_conditioner("#minecraft:fuel")
        out_graph = self.graph.subgraph(init_cond, "sub")
        return out_graph

    def visualize_graph(self, graph: Graph, name: str = "default"):
        """Visualize generated graph"""
        net = init_pyviz_graph()
        graph.draw_with_pyvis(net)
        net.show(name + ".html", notebook=False)

    def search(self, hand: dict, args: tuple = (9, 3, 2), **kwargs):
        """
        Search from a hand (usualy of final item dict)

        args: args to search_method.search.
        hand: dict
        cache: bool = True. whether save the search results.
        """
        init = HandResource(hand)
        b = self.search_method()
        visited, struct = b.sample_possible_hands(init, *args)
        if kwargs.get("cache", True):
            self.save_search(hand, visited, struct, type_="text")
        return visited, struct

    def save_search(self,
                    init: Dict[Node, int],
                    visited: Dict[str, HandResource],
                    struct: Dict[str, int],
                    type_: str = "json"):
        """
        Save searching result.

        Parameters
        ----------
        visited: {hash-str: HandResource}
        struct: {hash-str: level-from-root}
        type_: str = "json", save type.
        """
        match type_:
            case "json":
                name = "-".join(init.keys())
                with open(self.save_path / f"raw_{name}.json", "w") as fp:
                    json.dump([{
                        "hand": visited.hand,
                        "hand_extra": visited.hand_extra
                    }, struct], fp)
            case "text":
                name = "-".join(init.keys())
                with open(self.save_path / f"raw_{name}.txt", "w") as fp:
                    for key, val in struct.items():
                        fp.write(f"\n\n===  Level {val}  ===\n")
                        for k, v in visited[key].hand.items():
                            item_name = lint_to_simplename(k)
                            item_count = v.numerator / v.denominator
                            fp.write(f"    {item_name} * {item_count:.3}\n")
                            for kk, vv in visited[key].hand_extra.items():
                                tgt_name = lint_to_simplename(kk)
                                fp.write(
                                    f"        d({item_name},{tgt_name})={vv}\n"
                                )

    def load_json(self, file_name: str):
        """
        """
        with open(self.save_path / f"raw_{file_name}.json", "r") as fp:
            visited, struct = json.load(fp)
        return visited, struct

    def split(self, hand):
        """
        """

        return None  # [hand1, hand2]

    def search(self):
        pass
