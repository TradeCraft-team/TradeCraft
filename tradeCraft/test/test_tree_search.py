"""
Test / use of Problem Sieving.
"""
import sys
from pathlib import Path

THIS_PATH = Path(__file__).parent

sys.path.append("..")

from src.craft_rules import HandResource, BFS


def test_hand():
    """
    """

    h = HandResource({"minecraft:lectern": 1, "minecraft:clock": 1})
    print(h.hand)
    h.hand_change("minecraft:clock", -3)
    print(h.hand)
    h.hand_change("minecraft:stick", 1)
    print(h.hand)
    for v in h.apply_recipe("$stick"):
        print(v.hand)

    print(list(h.get_recipes()))


def test_bfs():
    """
    """

    t1, t2 = "iron_ingot", "gold_ingot"
    h = HandResource({f"minecraft:{t1}": 1, f"minecraft:{t2}": 1})
    b = BFS()
    b.set_init(h)
    visited, struct = b.sample_possible_hands(h.hand, 7, 3, 2)
    for k, v in struct.items():
        print("-" * 80 + "\n", f"level {v}")
        break
        for key, val in visited[k].hand.items():
            print(">>>  ", key[10:], val.numerator / val.denominator)

    with open(THIS_PATH / "temp_data" / f"{t1}_{t2}.txt", "w") as fp:

        for k, v in struct.items():
            fp.write("-" * 20 + "\n" + f"level {v}\n")

            for key, val in visited[k].hand.items():
                fp.write(
                    f">>> {key[10:]} {val.numerator / val.denominator:.3}\n")
    return visited, struct


def test_back(hand: HandResource):
    dicts = [{}, {}]
    for i, h in enumerate(hand.hand):
        dicts[i % 2][h] = hand.hand[h]

    hand0 = HandResource(dicts[0])
    hand1 = HandResource(dicts[1])
    b = BFS()
    # b.set_init(hand0)
    flag, visited, struct = b.check_craft_availability(hand0,
                                                       "minecraft:clock")

    print(hand0.hand)
    for k, v in struct.items():
        print("=" * 80 + "\n", f"level {v}")
        for key, val in visited[k].hand.items():
            print(">>>  ", key[10:], val.numerator / val.denominator)

    print(flag)


def main_():
    """
    """
    print("AAA")

    # test_hand()
    visited, struct = test_bfs()
    test_hash = [t for t, v in struct.items() if v == 4]
    test_back(visited[test_hash[-1]])


if __name__ == "__main__":
    main_()
