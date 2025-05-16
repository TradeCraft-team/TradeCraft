"""
Node for directed graphs.

For a recipe, it is parent of its resources,
and it is the child of its result.
This is for aligning with previous defined tags.
"""
import secrets
import hashlib
import math
from fractions import Fraction

def to_fraction(p: list | dict | int | Fraction | str):
    """
    from pair to fraction
    len(p)==2
    """
    match p:
        case [int(n), int(d)] | (int(n), int(d)):
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
                num = num[:2] if len(num)>=2 else num[0]
                return to_fraction(num)
            except Exception as e:
                print(e)
            return -1
        case _:
            return p

def num_to_string(p: list | dict | int | Fraction) -> str:
    """
    """
    f = to_fraction(p)
    return f"{f.numerator / f.denominator}"


def reduction(x):
    if isinstance(x[0], int) and isinstance(x[1], int):
        gcd = math.gcd(*x)
        return (x[0]//gcd, x[1]//gcd)
    return x

def multiplication(a, b):
    if (ia:=isinstance(a, (list, tuple))) and (ib:=isinstance(b, (list, tuple))):
        return reduction((a[0]*b[0], a[1]*b[1]))
    if ia:
        return reduction((a[0]*b, a[1]))
    if ib:
        return reduction((a*b[0], b[1]))
    return reduction((a*b, 1))



def add_method(cls):
    """
    Add method to a class
    """
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func

    return decorator


class Node:
    """
    Graph Node
    """
    _name_verifier = {
        "recipe": lambda x: x[0] == "$",
        "tag": lambda x: x[0] == "#",
        "item": lambda x: x[0] not in ["$", "#"]
    }

    def __init__(self, node_name: str, node_type: str, **args):
        """
        Initialize.

        A node may be one of 3 types: an item, a tag or a recipe, stored by `node_type`.
        In a graph of nodes, only a **recipe** node is an AND node, all others are OR nodes.

        Attributes
        ----------
        Node._children: dict, ingredents of a recipe / the recipe of the result / items under a tag.
                       key: `Child_Node.node_name`, value: `count` in recipe or equivalent ratio in tag (not 1 only for fuels).
        Node.children: dict, the object-level reference version of Node._children

        Node._parents: dict, forming the inverse of Node.children system, constructed for
                       an easy reverse-tracing. Same in format as Node.children.
        Node.parents: dict the object-level reference version of Node._parents

        Node.attributes: dict with keys in ["group", "type", "category"]

        item -> tag -> recipe -> item
        item -> recipe -> item
        tag -> tag

        Node.attributes: dict

        Parameters
        ----------
        node_type: str = "item" "tag" "recipe"
        node_name: str. recipe => "$recipe_name"
                        tag    => "#tag_name"
                        item   => "item_name"
        """
        # print(node_name, node_type)
        assert self.__class__._name_verifier.get(node_type,
                                                 lambda x: False)(node_name)
        self.node_name = node_name
        self.node_type = node_type
        self._fully_reconstructed = True
        self._parents_obj = {}
        self.attributes = dict(
            (x, args.get(x, "")) for x in ["type", "category", "group"])
        self.attributes['node_type'] = self.node_type
        self._parents = {}
        self._children_obj = {}
        self._children = {}

    def _verify_parent(self, other):
        """
        Verify before adding parent.
        [child -> parent]
        item -> tag -> recipe -> item
        item -> recipe -> item
        tag -> tag
        """
        assert isinstance(other, self.__class__)
        if self.node_type in ["tag"]:
            return other.node_type in {
                "recipe", "tag"
            }  # If allow tag-graph, {"recipe", "tag"}
        if self.node_type in ["item"]:
            return other.node_type in {"recipe", "tag"}
        if self.node_type in ["recipe"]:
            return other.node_type in {"item"}
        return False

    def _verify_child(self, other) -> bool:
        """
        Verify before adding child.

        item -> tag -> recipe -> item
        item -> recipe -> item
        tag -> tag
        """
        assert isinstance(other, self.__class__)
        if self.node_type in ["tag"]:
            return other.node_type in {"item", "tag"}
        if self.node_type in ["item"]:
            return other.node_type in {"recipe"}
        if self.node_type in ["recipe"]:
            return other.node_type in {"item", "tag"}
        return False

    def gen_random_node_name(self):
        """
        Generate random name, used for recipes and temp_tags.
        """
        self.node_name = secrets.token_urlsafe(6)
        return self.node_name

    @classmethod
    def gen_md5_node_name(cls, items: str):
        """
        Used for temporary tag names.
        """
        return hashlib.md5(items.encode("utf-8")).hexdigest()

    def add_child(self, children=[], kw_children={}):
        """
        Add child, can add multiple.
        """
        for child in children:
            self._verify_child(child)
            self._children[child.node_name] = 1
            self._children_obj[child] = 1
        for child, count in kw_children.items():
            self._verify_child(child)
            self._children[child.node_name] = count
            self._children_obj[child] = count

    def add_parent(self, parents=[], kw_parents={}):
        """
        Add parent, can add multiple.
        """
        for parent in parents:
            self._verify_parent(parent)
            self._parents[parent.node_name] = 1
            self._parents_obj[parent] = 1
        for parent, count in kw_parents.items():
            self._verify_parent(parent)
            self._parents[parent.node_name] = count
            self._parents_obj[parent] = count

    def edge_to(self, other, other_amount=1, self_amount=1):
        """
        Link an edge from self to other.
        """
        self.add_parent([], {other: (other_amount, self_amount)})
        other.add_child([], {self: (self_amount, other_amount)})

    def __getstate__(self):
        """
        Defines the behavior of pickle.
        """
        return {
            "_parents": self._parents,
            "_children": self._children,
            "node_name": self.node_name,
            "node_type": self.node_type,
            "attributes": self.attributes
        }

    def __setstate__(self, _dict):
        """
        Defines the behavior of unpickle.
        """
        self.node_type = _dict["node_type"]
        self.node_name = _dict["node_name"]
        self._parents = _dict["_parents"]
        self._parents_obj = {}
        self._children = _dict["_children"]
        self._children_obj = {}
        self.attributes = _dict["attributes"]
        self._fully_reconstructed = False

    def fully_reconstruct(self, node_dict):
        """
        Set a method of fully reconstructing the object.
        """
        for key, val in self._parents.items():
            self._parents_obj[node_dict[key]] = val
        for key, val in self._children.items():
            self._children_obj[node_dict[key]] = val
        self._fully_reconstructed = True

    @property
    def parents(self):
        if self._fully_reconstructed:
            return self._parents_obj
        raise Exception(
            "Please run `self.fully_reconstruct(node_dict)` before using the unpickled Node!"
        )

    @property
    def children(self):
        if self._fully_reconstructed:
            return self._children_obj
        raise Exception(
            "Please run `self.fully_reconstruct(node_dict)` before using the unpickled Node!"
        )

    def __repr__(self):
        if self.node_type=="recipe":
            ret = f"""RECIPE {self.node_name}\n{"-"*(len(self.node_name)+7)}\n"""
            for k,v in self._children.items():
                ret += f"{num_to_string(v)} * {k} + "
            ret = ret[:-3] + " -> \n"
            for k,v in self._parents.items():
                ret += f"{num_to_string(v)} * {k} "
            return ret + "\n"
        ret = f"""{self.node_type.upper()} {self.node_name}\n{"-"*(len(self.node_type)+len(self.node_name)+1)}\n"""
        for k,v in self._children.items():
            ret += f"{num_to_string(v)} * {k} || "
        ret = ret[:-3] + "\n"
        for k,v in self._parents.items():
            ret += f"{num_to_string(v)} * {k} || "
        return ret + "\n"


    def __str__(self):
        return self.__repr__()

if __name__ == '__main__':
    plank = Node("#plank", "tag")
    stick = Node("stick", "item")
    recipe = Node("$2plank->4stick", "recipe")
    recipe.edge_to(stick)
    plank.edge_to(recipe)

    print(recipe.parents, recipe.children, stick.parents, stick.children,
          plank.parents, plank.children)
