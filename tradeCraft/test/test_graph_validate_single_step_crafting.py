"""
Test the Graph.validate_single_step_crafting method
"""


import sys
sys.path.append("..")

from src.craft_rules import Graph, preprocessing, base_graph


def test():
    graph = base_graph("../craft_rules/")
    print("\nTesting Graph.validate_single_step_crafting...")
    torch_result = graph.validate_single_step_crafting(["minecraft:torch",12],
                                        [["minecraft:stick", 4],
                                         ["minecraft:coal", 3]])
    print("Torch result:", torch_result)
    assert torch_result

    chest_result = graph.validate_single_step_crafting(["minecraft:chest",4],
                                        [["minecraft:oak_planks",3],
                                         ["minecraft:cherry_planks",28],
                                         ["minecraft:coal",3]])
    print("Chest result:", chest_result)
    assert not chest_result

    chest_result2 = graph.validate_single_step_crafting(["minecraft:chest",4],
                                        [["minecraft:oak_planks",4],
                                         ["minecraft:cherry_planks",28],
                                         ["minecraft:coal",3]])
    print("Chest result2:", chest_result2)
    assert chest_result2

    print("All 3 tests passed.")

    redstone_torch_result = graph.validate_single_step_crafting(["minecraft:redstone_torch",1],
                                        [["minecraft:redstone",1],
                                         ["minecraft:stick",1],
                                         ["minecraft:coal",1]])
    assert redstone_torch_result

    iron_ingot_res = graph.validate_single_step_crafting(['minecraft:iron_ingot', 1],
                                        [('minecraft:iron_ore', 1), ('minecraft:coal', 1)])
    assert iron_ingot_res


if __name__ == '__main__':
    test()

