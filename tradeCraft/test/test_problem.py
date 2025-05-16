"""
Test / use of Problem Sieving.
"""
import sys
from pathlib import Path

THIS_PATH = Path(__file__).parent

sys.path.append("..")

from src.craft_rules import HandResource, BFS

hands={
        "minecraft:iron_ore": 5,
        "minecraft:cherry_planks": 1,
        "minecraft:oak_planks": 1,
        "minecraft:coal": 1
    }
target="minecraft:iron_hoe"

test_mydata=BFS()
flag, visited, struct=test_mydata.check_craft_availability(hands,target)
print("11",flag)
print("12",visited)
print("13",struct)

