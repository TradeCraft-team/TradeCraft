"""
Translates numerical and literal structures.
"""

from fractions import Fraction
from .yaml_reader import pr_args

CRAFT_RULE_PREFIX = pr_args["craft_rule_prefix"] + ":"
CRAFT_RULE_LENGTH = len(CRAFT_RULE_PREFIX)


def to_fraction(p: list | dict | int | Fraction | str):
    """
    from pair to fraction
    len(p)==2
    """
    match p:
        case [int(n), int(d)]:
            return Fraction(n, d)
        case [float(n), float(d)] | [float(n), int(d)] | [int(n), float(d)]:
            return Fraction(n).limit_denominator(10000) / Fraction(
                d).limit_denominator(10000)
        case {"n": n, "d": d}:
            return Fraction(n, d)
        case int(s):
            return Fraction(s)
        case float(s):
            return Fraction(s).limit_denominator(10000)
        case str(s):
            try:
                num = [float(x.strip()) for x in s.split("/")]
                num = num[:2] if len(num) >= 2 else num[0]
                return to_fraction(num)
            except Exception as e:
                print(e)
            return -1
        case _:
            return p


def process_item_dict(items: dict):
    """
    Turn items
    """
    ret = {}
    for name, amt in items.items():
        ret[lint_to_fullname(name)] = to_fraction(amt)
    return ret


def process_recipe(recipe: dict):
    """
    Rewrite a recipe
    """
    recipe["input"] = process_item_dict(recipe.get("input", {"_": 1}))
    recipe["output"] = process_item_dict(recipe.get("output", {"_": 1}))
    return recipe


def process_proposal(proposal: dict):
    """
    Rewrite a proposal
    """
    proposal["request"] = process_item_dict(proposal.get("request", {"_": 1}))
    proposal["offer"] = process_item_dict(proposal.get("offer", {"_": 1}))
    return proposal


def element_conditioner(resource):
    """
    Wrapper to construct item discriminator
    """

    def wrap(key, val):
        """
        Inner func
        """
        return key in resource

    return wrap


def lint_to_fullname(src: str | dict):
    """
    Change item name to full name: e.g. "stick" -> "minecraft:stick"
    """
    match src:
        case str(s):
            if s[0] in "$#" or s[:CRAFT_RULE_LENGTH] == CRAFT_RULE_PREFIX:
                return s
            return f"{CRAFT_RULE_PREFIX}{s}"
        case dict(d):
            return dict((lint_to_fullname(k), v) for k, v in d.items())


def lint_to_simplename(src: str | dict):
    """
    Change item name to simple version. Roughly reverse the `lint_to_fullname`
    """
    match src:
        case str(s):
            if s[:CRAFT_RULE_LENGTH] == CRAFT_RULE_PREFIX:
                return s[CRAFT_RULE_LENGTH:]
            return s
        case dict(d):
            return dict((lint_to_simplename(k), v) for k, v in d.items())
