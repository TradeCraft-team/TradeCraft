"""
"""

import os
import random
import numpy as np
from typing import Iterable, Literal
from itertools import product, combinations_with_replacement
from fractions import Fraction

from tqdm import tqdm

from .graph import Graph
from .process import base_graph
from .node import Node, to_fraction
from ..utils import print

FULL_GRAPH = base_graph(os.path.dirname(__file__))


class RecipeAmountError(Exception):
    pass


class HandResource:
    """Status of Hand Resource and Atomic Dynamics"""

    def __init__(self, hand: Iterable, graph: Graph = FULL_GRAPH, **kwargs):
        """Initialize."""
        self.hand = {}
        self.graph = graph
        self.hand_extra = {}
        self.set_hand(hand)
        self.hashvalue_ = hash("#".join(sorted(self.hand)))

    def rehash(self):
        self.hashvalue_ = hash("#".join(sorted(self.hand)))

    def contains(self, other: Iterable):
        """
        Check whether hands contains other
        """
        if not isinstance(other, Iterable):
            raise TypeError(f"Error, parameter {other} is not an iterable.")
        if isinstance(other, dict):
            return all(val <= self.hand.get(key, 0)
                       for key, val in other.items())
        other_dict = {}
        for x in other:
            item, amount = x
            other_dict[item] = other_dict.get(item, 0) + to_fraction(amount)
        return self.contains(other_dict)

    @property
    def hashvalue(self):
        return self.hashvalue_

    def set_hand(self, hand: Iterable[str] | Iterable[Node]):
        """Set hand, with EMPTY hand_extra"""
        if not isinstance(hand, Iterable):
            raise TypeError(f"Error, parameter {hand} is not an iterable.")
        if not isinstance(hand, dict):
            hand = dict((h, 1) for h in hand)
        for item in hand:
            match item:
                case str(a) if a[:1] not in ["#", "$", ""]:
                    self.hand[a] = to_fraction(hand[a])
                    self.hand_extra[a] = {}
                case Node(a) if a.node_type == "item":
                    self.hand[a.node_name] = to_fraction(hand[a])
                    self.hand_extra[a.node_name] = {}
                case _:
                    raise TypeError(
                        "Error, items in input must be str or Node.")
        self.extra_init()

    def extra_init(self):
        """
        Initialize extra, by setting its values to all items in hand zero.
        """

        for item, val in self.hand_extra.items():
            for tgt in self.hand_extra:
                val[tgt] = 0 if tgt == item else np.inf

    def hand_change(self,
                    name: str,
                    amt: tuple,
                    strict: bool = False,
                    parent: dict = {}) -> int:
        """Change the hand.

        strict: bool=False.
                If True, when not enough in subtracting some item, raise.

        Return code:
        0 for normal change, negative for removing too much.
        """
        amt = to_fraction(amt)
        if amt <= 0:
            # remove something
            # assert int(amt) == amt
            if name not in self.hand:
                raise KeyError(f"{name} does not exist in hand")
            if self.hand[name] <= -amt:
                ret = self.hand[name] + amt
                if ret and strict:
                    raise RecipeAmountError(f"{name} is not enough!")

                self.hand.pop(name)
                return 1

            self.hand[name] += amt
            return 1

        # amt = math.ceil(amt)   # Perhaps no need.
        # Ceiling should happen only when we fix it to hand.
        # No, more complicated.... Fine, as is.
        val = parent.get(name, {})
        self.hand[name] = self.hand.get(name, 0) + amt

        # label the characteristic distance for each item in hand.
        # parent works like an output in a recipe.

        # 1. if new item, set hand_extra.
        if name not in self.hand_extra:
            self.hand_extra[name] = {}
        # 2. for each target, identify distance to each target.
        for tgt_name, dist in parent.items():
            self.hand_extra[name][tgt_name] = min(
                self.hand_extra[name].get(tgt_name, np.inf), dist + 1)
        return 1

    def _gen_single_iter_forward(self, ing: Node, amt: Fraction):
        """
        used in apply_recipe at forward.
        """
        if ing.node_type == "item":
            if self.contains({ing.node_type: to_fraction(amt)}):
                return [(ing.node_name, to_fraction(amt))], 0
            return [], 0

        if ing.node_type == "tag":
            it = list((k, v) for k, v in ing._children.items())
            random.shuffle(it)

            # branch 1: combination within one tag, e.g. bowl or chest
            if (amt.denominator == 1 and amt.numerator > 1):
                next_iter = combinations_with_replacement(it, amt.numerator)

                ret = [x for x in next_iter if self.contains(x)]
                # print("===", ret, s=24)
                return (ret, 1) if ret else ([], 0)
            # branch 2: same kind in a tag. e.g. wooden stairs or boat
            else:
                iter_new = [
                    x for x in it
                    if self.contains({x[0]: to_fraction(x[1]) * amt})
                ]
                # if ing.node_name == "#minecraft:fuel":
                #     print(iter_new, s=3)
                # # print(iter_new, s=23)
                return (iter_new if iter_new else [], 0)

    def _gen_single_iter_backward(self, ing: Node, amt: Fraction) -> Iterable:
        """
        used in apply_recipe at backward

        Backward, ingredients are generated.
        """
        if ing.node_type == "item":
            return [(ing.node_name, to_fraction(amt))], 0

        if ing.node_type == "tag":
            it = list((k, v) for k, v in ing._children.items())
            random.shuffle(it)
            if (amt.denominator == 1 and amt.numerator > 1):
                return combinations_with_replacement(it, amt.numerator)
            return [(x[0], to_fraction(x[1]) * amt) for x in it], 0

    def apply_recipe(self,
                     recipe: str | Node,
                     batch: int = -1,
                     direction: Literal['F', 'B', "Forward", "Backward"] = "B",
                     **kwargs) -> iter:
        """
        Apply a recipe.

        This is NOT a strict mode!!! The hands may expand
        if the recipe keeps generating more output than targets.

        When applying a Forward recipe, it is possible that the recipe does not
        apply to the hand due to availability problem. We may skip them only
        this mode.
        """
        if isinstance(recipe, str):
            recipe = self.graph[recipe]
        assert recipe.node_type == "recipe"
        out, out_amt = list(recipe._parents.items())[0]
        assert (out in self.hand) or direction[0] == "F"

        # direction related aux coefficient (switching add with subtract)
        coeff = 1 if direction[0] == "B" else -1

        iters = []
        amounts = []
        flags = []
        # generate shuffled item combinations for each slot in recipe
        # mainly concerning the polyoptions when tags are in recipe.
        for ing, amt in recipe.children.items():
            amounts += [to_fraction(amt)]

            if direction[0] == "F":
                _iter, _flag = self._gen_single_iter_forward(
                    ing, to_fraction(amt))
                iters += [_iter]
                flags += [_flag]
                continue
            if direction[0] == "B":
                _iter, _flag = self._gen_single_iter_backward(
                    ing, to_fraction(amt))
                iters += [_iter]
                flags += [_flag]

        # generator, yields resulting hand with applying each possible changes.
        batch += 1
        # print(iters)
        for possible_ing in product(*iters):
            if (batch := batch - 1) == 0:
                return
            ret = HandResource(self.hand)
            # Deal with input. In forward mode, recipe may be incorrect.
            try:
                for ii, item_pack in enumerate(possible_ing):
                    validity = True
                    if flags[ii]:
                        for (item, val) in item_pack:
                            # print(item_pack, item, val, ii, amounts, s=1)
                            validity &= ret.hand_change(
                                item,
                                to_fraction(val) * coeff,
                                strict=True,
                                parent=self.hand_extra.get(out, {}))
                    else:
                        # print(item_pack, s=22)
                        item, val = item_pack
                        validity &= ret.hand_change(
                            item,
                            amounts[ii] * to_fraction(val) * coeff,
                            strict=True,
                            parent=self.hand_extra.get(out, {}))
                    if not validity:
                        break


            except RecipeAmountError as e:
                if direction[0] != "F":
                    raise e
                continue
            except KeyError as e:
                if direction[0] != "F":
                    raise e
                continue
            # Deal with output.
            ret.hand_change(out, -to_fraction(out_amt) * coeff)
            ret.rehash()
            print("ApplyRecipe:", recipe, self.hand, ret.hand, s=2)
            # print(possible_ing, amounts, s=5)

            yield ret

    def get_recipes(self,
                    direction: Literal['F', 'B', "Forward", "Backward"] = "B"):
        """Generator of recipes"""
        for item in self.hand:
            if direction[0] == "B":
                temp = list(self.graph[item].children.keys())
            else:
                temp = []
                for x in self.graph[item].parents.keys():
                    temp.extend([
                        y for y in x.parents.keys() if y.node_type == "recipe"
                    ] if x.node_type == "tag" else [x])

            random.shuffle(temp)
            for recipe in temp:
                yield recipe


class TreeSearch:
    """
    Base TreeSearch
    """

    def __init__(self, graph: Graph = FULL_GRAPH):
        """
        graph: the crafting graph.
        """
        self.graph = graph
        self.treenodes = {}

    def set_init(self, tnode: dict | HandResource):
        """Set initial hand or add a new hand."""
        match tnode:
            case dict(a):
                tnode = HandResource(a)
            case HandResource():
                pass
            case _:
                raise TypeError(
                    "Argument `tnode` should be a dict or HandResource.")
        self.treenodes[tnode.hashvalue] = tnode
        tnode.extra_init()

    def search_backward(self, **kwargs):
        """
        From target(s) to ingredient, an partially expansion.
        """

        raise NotImplementedError

    def search_forward(self, hand, target, **kwargs):
        """
        From hand to see what can be crafted.

        Implement a full breadth first search.
        """
        raise NotImplementedError


class BFS(TreeSearch):
    """Breadth-First Search"""

    def search(self,
               max_depth=-1,
               recipe_width=-1,
               tag_width=-1,
               **kwargs) -> tuple:
        """
        Search!

        stop_cond: callable[HandResource, bool].
        """
        queue = []
        next_queue = list(self.treenodes.values())
        visited = {}
        struct = {}
        cur_depth = 0
        stop_cond = kwargs.get("stop_cond", lambda h: False)
        direction = kwargs.get("direction", "Backward")

        while (cur_depth := cur_depth + 1) != max_depth and len(next_queue):
            print("DEPTH:", cur_depth, "TOSEARCH:", len(next_queue))
            queue += next_queue
            next_queue = []
            i = 0
            while queue:
                if (i := i + 1) % 100 == 0:
                    print(i, len(queue))
                cur = queue.pop()
                # Find all recipes applicable to cur (part of cur gen by recipe)
                recipe_index = -1
                for trans in cur.get_recipes(direction=direction):
                    # print(trans)
                    if (recipe_index := recipe_index + 1) == recipe_width:
                        break
                    # apply this recipe, get possible previous hand status.
                    tag_index = -1
                    for hand in cur.apply_recipe(trans, direction=direction):
                        if hand.hashvalue not in visited:
                            visited[hand.hashvalue] = hand
                            struct[hand.hashvalue] = cur_depth
                            next_queue.append(hand)
                            if stop_cond(hand):
                                return visited, struct, 1

                        if (tag_index := tag_index + 1) == tag_width:
                            break
        return visited, struct, 0

    def check_craft_availability(self, hand: HandResource | dict, target: str,
                                 **kwargs):
        """
        Check whether target can be crafted from hand.
        """
        self.set_init(hand)
        visited, struct, flag = self.search(
            stop_cond=lambda h: target in h.hand,
            direction="Forward",
            **kwargs)
        return flag, visited, struct

    def sample_possible_hands(self,
                              hand: dict | HandResource,
                              max_depth=-1,
                              recipe_width=-1,
                              tag_width=-1):
        """
        Sampling what can possibly craft the hand.
        """
        match hand:
            case str(t):
                self.set_init(HandResource({t: 1}))
            case dict(t):
                self.set_init(HandResource(t))
            case HandResource():
                self.set_init(hand)
        visited, struct, flag = self.search(max_depth, recipe_width, tag_width)
        return visited, struct
