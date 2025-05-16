# Docs of Package `craft_rules.py`.

The Package defined in `craft_rules.py` is a customizable crafting rule toolkit
based on MineCraft rule files.

## Structure
### Data
- recipe: this directory contains all raw json style MC crafting rules, i.e., all recipes we consider in tradeCraft. Files are loaded from MC package `JAVA_v_1.20`.
- tags: this directory contains all tag information loaded from MC package `JAVA_v_1.20`.
- `../item_icons/` contains some icons of the items. About 1% of all items fail to have an icon archived here ([TODO] please find them and complete them when you have time).

The data is not 100% complete yet, including some corner-case recipes and tags.

### Code
- process.py: defines necessary processing functions. Use the following main functions, others are building blocks.
  - `base_graph(prefix, recipe_prefix, tag_prefix)` returns a Graph (see `graph.py`) representing the crafting AOG, could simply load a cache file if cache file exists, otherwise regenerate.
  - `preprocessing(recipe_prefix, tag_prefix)` regeneration part of `base_graph()`.

- node.py: Defines the AOG node used in Graph. There are 3 types of nodes: recipe, tag and item. Graph contains children and parents, and stores attributes of the nodes (basically all info in recipes and tags). A child or a parent is a pair (target, amount), describing "one self(Node) equals to `amount` of target in the `self.node_type`". A child is the downstream of node, a parent is the upstream one. For details, see `help(Node)`.

- graph.py: We represent the crafting rules as an **And-Or Graph**, where recipe nodes are **AND-nodes**, and item / tag nodes are **OR-nodes**. `process.preprocessing` outputs the full Graph of crafting, the output graph it is not connected. For details, see `help(Graph)`.
  - `Graph.node_dict` is a dictionary of `{Node.node_name: Node}`, together with parents/children of Nodes, one can easily trace the Graph.
  - method: `subgraph(condition, name, ignore_condition)` implements a way of constructing subgraph on children direction easily, `condition(node_name, node)->bool` and `ignore_condition(node_name, node)->bool` are functions representing initial condition and breadth spreading search conditions in the traversal.

  - method: `reversed_subgraph`, similar to `subgraph`, traverse on parent-side.

  - method `traverse_vectorize` works similar to subgraph, but more flexible, it spans both top-down (child-side) and bottom-up (parent-side) and allow to maintain a statistical vector/tensor data style *(e.g. calculate entropy easily)*. Possible applications could be find in `../analysis/`.

  - **`validate_single_step_crafting`**: checks whether the target could be crafted from resources, conditioned by strict check or not. THIS IS USED in the tradeCraft system as checker for crafting validity!

  - `draw_with_pyvis` attach pyvis.network.Network with their real icons.

- `example_subtree.py` and `viz*.py`: visualization methods.

- utils: package which defines some utility functions.






## TODO list:
- Complete the raw data.
- Easier (but not so flexible traversing methods through existing general ones).
- Checking complicated crafting vaildity (may form it as linear programming and use some linear program solver).

