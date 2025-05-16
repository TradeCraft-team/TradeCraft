# README for `recipe/tag` graph construction

## Definition

- Recipe: a recipe is (suppose we have all tools for crafting) function accepting certain input and turn them into output
  1. A reicpe looks like an AND node in AOG, turns `[(INGREDIENT1, AMOUNT1), ...]` into `[(RESULT, AMOUNT)]`.
  2. For `furnace` and `blast furnace` products, `fuel` including coal, charcoal, planks, logs ... are considered part of the ingredients.
  3. A recipe may have its `type` / `category` / `group` as attributes, if not belonging to any, the attribute is set to empty string.


- Item: an item is an object, occur as result or a recipe / ingredent of a recipe / instance of a tag.

- tag: a group of items / tags which are often used in a recipe as identical objects. A tag can be result of a recipe or an ingredient of a recipe, or instance of another tag.

## Implementation
### `process.py`
Running `process.py` directly will (re)generate `recipe_out.json`, generate `solven_tags.json` if not exists.

Calling `process.main()` will do the above thing, and return a dictionary `node_dict` made of:
- key: `node.node_name`
- value: `node`

For details of `Node`, see Section **About Node** below.

** The return of `process.main()` is necessary for graph-tracing, as parents/children keys are names(keys of `node_dict`) instead of the objects themselves. **




## About Node
```
Help on module node:

NAME
    node - Node for directed graphs.

DESCRIPTION
    For a recipe, it is parent of its resources,
    and it is the child of its result.
    This is for aligning with previous defined tags.

CLASSES
    builtins.object
        Node

    class Node(builtins.object)
     |  Node(node_name: str, node_type: str, **args)
     |
     |  Graph Node
     |
     |  Methods defined here:
     |
     |  __init__(self, node_name: str, node_type: str, **args)
     |      Initialize.
     |
     |      A node may be one of 3 types: an item, a tag or a recipe, stored by `node_type`.
     |      In a graph of nodes, only a **recipe** node is an AND node, all others are OR nodes.
     |
     |      Attributes
     |      ----------
     |      Node.children: dict, ingredents of a recipe / the recipe of the result / items under a tag.
     |                     key: `Child_Node.node_name`, value: `count` in recipe or equivalent ratio in tag (not 1 only for fuels).
     |
     |      Node.parents: dict, forming the inverse of Node.children system, constructed for an easy reverse-tracing. Same in format as Node.children.
     |
     |      Node.attributes: dict with keys in ["group", "type", "category"].
     |
     |      item -> tag -> recipe -> item
     |      item -> recipe -> item
     |      tag -> tag
     |
     |      Node.attributes: dict
     |
     |      Parameters
     |      ----------
     |      node_type: str = "item" "tag" "recipe"
     |      node_name: str. recipe => "$recipe_name"
     |                      tag    => "#tag_name"
     |                      item   => "item_name"
     |
     |  add_child(self, children=[], kw_children={})
     |      Add child, can add multiple.
     |
     |  add_parent(self, parents=[], kw_parents={})
     |      Add parent, can add multiple.
     |
     |  edge_to(self, other, self_amount=1, other_amount=1)
     |      Link an edge from self to other.
     |
     |  gen_random_node_name(self)
     |      Generate random name, used for recipes and temp_tags.
     |
     |  ----------------------------------------------------------------------
     |  Class methods defined here:
     |
     |  gen_md5_node_name(items: str)
     |      Used for temporary tag names.
     |
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |
     |  __dict__
     |      dictionary for instance variables
     |
     |  __weakref__
     |      list of weak references to the object

FUNCTIONS
    add_method(cls)
        Add method to a class

FILE
   \trading_alchemists\craft_rules\node.py

```


## About Graph
- `subgraph` is implemented using a filtering condition (as a `callable(key:str, val:Node)->bool`)

```
Help on module graph:

NAME
    graph - Graph of Nodes

CLASSES
    builtins.object
        Graph

    class Graph(builtins.object)
     |  Graph(graph_name: str = 'None')
     |
     |  Node Graph
     |
     |  Methods defined here:
     |
     |  __getitem__(self, key)
     |      Get any graph node from self.node_dict.
     |
     |      Parameters
     |      ----------
     |      key: str
     |
     |  __init__(self, graph_name: str = 'None')
     |      Initialize.
     |
     |  copy_node_skeleton(self, node: node.Node)
     |      Add a node to graph, forgetting all edges.
     |
     |  load_dict(self, node_dict: dict)
     |      Load from a dictionary of Nodes.
     |
     |  load_pickle(self, name: str)
     |      Load from a pickle file.
     |
     |  pickle_graph(self, name: str = 'graph.pkl')
     |      Pickle current graph
     |
     |  subgraph(self, condition: <built-in function callable>, name: str = 'sub')
     |      Parameters
     |      ----------
     |      condition: callable, a function which takes a `(key:str, val:Node)`
     |                 instance and output a boolean. `True` represents to take
     |                 the node as basic node.
     |      name: str, the name of the subgraph
     |
     |  to_igraph(self)
     |      [TODO] Translate to igraph format.
     |
     |  to_networkx(self)
     |      Translate to a networkx graph.
     |
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |
     |  __dict__
     |      dictionary for instance variables
     |
     |  __weakref__
     |      list of weak references to the object

FILE
    c:\bigai\repos\socialimitationgame-playground\trading_alchemists\craft_rules\graph.py
```
