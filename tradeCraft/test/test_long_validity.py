import sys
sys.path.append("..")

from src.utils import print
from src.craft_rules import HandResource, BFS

hands = {

    # "minecraft:iron_ore": 5,
    # "minecraft:cherry_planks": 2,
    "minecraft:oak_log": 2,
    "minecraft:coal": 1
}

target = "minecraft:chest"

test_mydata = BFS()
flag, visited, struct=test_mydata.check_craft_availability(hands,target)
print("11", flag, s=12)
print("\n\n", *[h.hand for h in visited.values()], sep="\n=====\n", s=24)
print("13", [x for x in struct.values()])
