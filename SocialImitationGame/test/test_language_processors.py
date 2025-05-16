import sys
sys.path.append("..")

from pathlib import Path

from src.proxied_games.tradeCraft import BASIC_TC_LANGUAGE_PROCESSOR, BasicTCLanguageProcessor



def test_generate_prompt():
    proc = BASIC_TC_LANGUAGE_PROCESSOR
    p = proc.generate_prompt("server__proposal",
                             unread_msgs=[("server__proposal",{
                                 "proposal":{"request": {"minecraft:stick":1},
                                             "offer": {"minecraft:cobblestone":1},
                                             "self": "whomever",
                                             "partner": "someone"},
                                 "message": "Hola!!"}),
                              ("server__start_proposal", {
                                  "proposer": "whomever"})
                              ])
    print(p)


def test_parse_hands():
    hands_info = {'minecraft:cherry_planks': {'d': 3, 'n': 1}, 'minecraft:coal': 1, 'minecraft:cobblestone': 1, 'minecraft:raw_copper': 1, 'minecraft:raw_iron': 2}
    language_processor = BasicTCLanguageProcessor()
    print(language_processor._parse_hands(hands_info))


if __name__ == '__main__':
    test_generate_prompt()
    test_parse_hands()
