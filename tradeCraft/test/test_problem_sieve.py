"""
Test / use of Problem Sieving.
"""
import sys
from pathlib import Path

THIS_PATH = Path(__file__)

sys.path.append("..")

from src.craft_rules import ProblemSieve, FULL_GRAPH
from src.craft_rules.graph import *


def main():
    ps = ProblemSieve()
    print("=" * 80)
    print(FULL_GRAPH["$clock"]._children)
    print(FULL_GRAPH["$clock"]._parents)
    tgts = ps.sample_targets(2, 0)
    print(tgts)
    for i, t in enumerate(tgts):
        g = ps.target_to_graph(t)
        ps.visualize_graph(g, f"../../data/Target_No_{i}")


if __name__ == "__main__":
    main()
