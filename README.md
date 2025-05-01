# Task 1: Parent Path

## Part 1

Render the path to the parent node on the top line, joined by "->".
If the path is too long, shorten it by eliding the middle of the path with ellipses.
We should try to include as many nodes along the path as possible, while keeping the same number of nodes before and after the ellipses

Example:
root -> node1 ... -> node2 -> parent

## Part 2

Add tests for deep (a single linear chain) and wide (a single parent with many children) trees.

# Task 2: Node status

Add a status to each node, and apply color everwhere a node is rendered based on its status.

- working: color the node yellow
- pending changes: color the node blue
- no changes: color the node green
- not checked: color the node red

# Task 3: Reachable nodes

1. Add a boolean property to `Node`s, indicating whether they are `active`.
2. Define a node as `reachable` if the entire path from the root to the node is active (including the node itself).
   Everywhere a node is rendered, apply the dimming attribute if it is not reachable.
3. Update the count to show only reachable descendants, i.e., "node_name (+X more reachable)"
