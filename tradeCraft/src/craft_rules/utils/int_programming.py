"""
Integral programming for the crafting-validation

WORK IN PROGRESS
"""


import cvxpy as cp
import numpy as np
from fractions import Fraction
from typing import List, Tuple
from .. import preprocessing, Graph
from . import *

BASE_GRAPH = preprocessing()


def leaf_spec_generator(node_name: str, resource: List[tuple], graph:Graph=BASE_GRAPH):
    """
    DFS method on the subAOG, finding next possible crafting path
    """
    ret = np.zeros(len(resource), dtype=Fraction)
    inv_item = {}
    for k ,item in enumerate(resource):
        inv_item[item[0]] = k

    spectrum = {node_name:1}

    def dfs(spec, graph):
        pass





def reversed_subgraph(resource:List[tuple], graph:Graph):
    def hand_condition(key, val)->bool:
        return key in resource

    out_graph, feature = graph.reversed_subgraph(hand_condition)
    return out_graph, feature


def verify_crafting_feasibility(resource:List[tuple],
                                target:List[str],
                                graph:Graph=BASE_GRAPH) -> bool:
    """
    Verify the feasibility in crafting from resource to target.

    Parameters
    ----------
    resource: list of (item-name, item-amount).
    target: list of item-name
    graph: The AOG to follow.
    """

    upstream_subgraph, feature = reversed_subgraph(resource, graph)

    if any(tgt not in upstream_subgraph.node_dict for tgt in target):
        return False, "Cannot craft the target items"

    print("All targets are found in the resource table")
    subforest = {}
    for tgt in target:
        subforest[tgt] = upstream_subgraph.subgraph(id_conditioner(tgt))


    N = len(resource) + len(target)
    constraint_coeff = np.zeros([1,N], dtype=float)

    for tgt, tree in subforest.items():
        tree


    constraint_const = np.zeros(constraint_const.shape[0], dtype=float)
    x = cp.Variable(N, integer=True)
    objective = cp.Maximize(cp.sum(x))
    constraints = [0<=x, constraint_coeff*x<=constraint_const]
    prob = cp.Problem(objective, constraints)

    results = prob.solve(solver=cp.CPLEX)
