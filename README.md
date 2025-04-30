# User study for nlmc

## Task description

This user study has you implement 3 new features for a terminal-based tree visualizer/navigator.

## Testing

Some basic test cases are provided. As part of the tasks, you will be asked to create some new test cases.

```bash
$ navigator {1,2,3,4,5,6,7,8}
```

## Set up

Clone [nlmc](https://github.com/FluidicML/nlmc) in a folder adjacent to this one.
In an `.env` file at the root-level of the newly cloned repository, add the following:

```
ANTHROPIC_API_KEY=<KEY>
```

where `<KEY>` refers to your own Anthropic key.

Next, from within the `nlmc-user-study` project, run:

```bash
$ poetry shell
$ poetry install
$ npm init -y
$ npm install -g pyright
```

> On newer versions of `poetry`, you may need to run `$(poetry env activate)` instead of `poetry shell`.

Lastly, install [VS Code](https://code.visualstudio.com/docs/setup/setup-overview#_set-up-vs-code-for-your-platform).
Make sure the `code` command is found in your `PATH`.

# Instructions

## Getting started

The goal of this user study is to modify the current visualizer with additional features. First, let's see how the tool currently works. Get a feel for the tool by playing around with a few test cases.

For example, at the top level of the `nlmc-user-study` project, try running:

```bash
$ navigator 8
```

Next, switch over to the `reference` branch. This branch lets you see what the intended end product is.

```bash
$ git checkout reference
$ navigator 8
```

The `reference` branch contains 3 changes that you will be re-implementing:

1. The top line now contains a path from the root, rather than just the immediate parent.
1. The nodes are color coded based on status.
1. Some nodes are rendered as dimmed ("unreachable"). The descendent counts now also only report reachable nodes.

When you are done, switch back over to the `main` branch.

```bash
$ git checkout main
```

### Code base

The tool is implemented in the `navigator` directory. **Note that the user study will only ask you to make changes to the python files in this directory.**

#### `cli.py`

Let's start by looking at the `cli.py` file. This contains the logic for parsing the command line arguments, and is the entrypoint that starts the navigation loop.

In particular, note that `parse_args` limits the test cases that can be specified on the command line.

(Ignore the `nlmeta` sections for now; we will cover these in the next section.)

#### `tests.py`

This file defines the test cases, which consists of randomly constructed trees.

#### `node.py`

`node.py` defines a very basic tree data structure. Each `Node` instance has references to its children and parent.

#### `navigator.py`

Finally, let's look at `navigator.py`, which contains the bulk of the rendering logic.

##### `navigation_loop`

The navigation loop is implemented in the `navigation_loop` function. It is the application's event loop - the central controller for the application - responsible for handling user input (`NavigatorState`) and rendering updated state (`NavigatorRenderer`).

This creates an interactive terminal-based navigation experience for exploring tree structures.

##### `NavigatorState` and `AnnotatedNode`

`NavigatorState` is where the "data" about the tree is stored, specifically, the current node.

To make rendering more efficient, metadata is precomputed with the `_annotate_tree` method during initialization:

- Tree depth (maximum depth of each subtree)
- Descendant count (total nodes in each subtree)

##### `NavigatorRenderer`

All the rendering logic is handled in `NavigatorRenderer`. The main entrypoint is `render`, which handles two distinct cases:

1. If the current node has a parent, we render the parent, the current node, and its siblings. `render_parent` adaptively chooses the best display based on terminal size constraints to show as much context as possible.
1. If the current node is the root of the tree, we simply render the full tree using `render_deepest_tree`. Note that certain display logic (such as highlight the active node) is handled separately in this case.

##### `curses`

The Python curses library powers the terminal interface by:

- Managing terminal I/O
- Enabling text drawing at specific coordinates (x,y positions)
- Providing text styling capabilities (like highlighting for the current node)
- Managing terminal dimensions and constraints
- Handling terminal refresh and screen clearing operations

Don't worry if you are not familiar with this library yet: the LLM is typically quite good at generating `curses` code, and the APIs are generally not too complex.

### Intro to `nlmc`

Let's begin by initializing the project.

In general, you only need to remember one command:

```bash
$ nlmc [navigator/path/to/file.py]
```

If no file is specified, `nlmc` will compile the entire `navigator` project.

The core transformation that `nlmc` will perform is **replacing the body of a function marked for compilation**. A function is considered marked for compilation if the first non-blank line of the function's docstring is `@nlmeta`.

You have 3 main ways to control what the LLM generates:

- The type of the function. This will always be preserved by the compiler.
- The docstring. This will also always be preserved by the compiler.
- The implementation. Providing pseudocode here can be a useful way to guide the implementation. However, for particularly complex problems, declaring an algorithm in the docstring may be a more permanent way to guide the behavior. Note that the LLM will attempt to follow the existing implementation as much as possible in subsequent implementations, so when making large changes, it may help to delete the existing implementation to force a fresh start.

Let's look at an example. (Don't worry about understanding what's going on here, we're just going to use this to demonstrate the syntax of the docstring.)

```python
def render_tree(
    self,
    node: AnnotatedNode,
    x: int,
    y: int,
    depth: int,
    offset: int = 4,
) -> tuple[int, int] | None:
    """
    @nlmeta

    Render a node and its children to a maximum depth.

    Algorithm:
    - If child_depth = 0, render the node as a terminal.
    - If the node has children, recursively render up to self.max_children children at depth - 1.
    - If the node has more than self.max_children children, render a placeholder as an additional child "(+X more children)".
    - Return the number of rows used, or -1 for failutre.

    Args:
        state: The current navigator state
        node: The node to render
        x: X coordinate
        y: Y coordinate
        depth: maximum depth of the tree to render
        offset: Connector length for rendering children

    Dependencies:
        context: NavigatorRenderer.render_siblings: uses this function to render the full display.
            Refer also to the documentation for render format details.
        context: NavigatorRenderer.render_deepest_tree: uses this function to render the deepest tree possible.
        NavigatorRenderer.erase_below: used to erase the screen below a given y coordinate.
            Use this to clear the screen below the current node prior to rendering.
            The caller is responsible for clearing upon failure.
        NavigatorRenderer.render_as_terminal: used to render a node as a terminal (rather than a tree).
        NavigatorRenderer.draw_connectors: use to draw connectors after tree structure has been set.

    Returns:
        None if the tree cannot be rendered.
        Otherwise, returns a tuple of the number of rows used and the actual depth of the tree rendered.
    """
    ...
```

Note the `@nlmeta` tag in the docstring, which marks this as a unit for compilation. This must be on the first line of the docstring.

This docstring follows typical Python conventions and is provided, in full, as context to the configured LLM. Of the blocks written in this docstring, only `Dependencies` is parsed specially.

Lines indented within the `Dependencies` block should be written using the following syntax:

`[context: | required:] IMPORT: HINT`

The `required` and `context` keywords are used to control the order of compilation. `required` units are always compiled first. `context` units allow importing context without creating cycles in the dependency graph. If neither are specified, `required` is assumed.

`IMPORT` refers to a reference to some Python object. It follows Python's import syntax. For instance, `.node` would import the entire file `navigator/node.py` while `.node.Node` would import just the `Node` class in `navigator/node.py`.

Local symbols can be included by excluding the `.` prefix (for instance `NavigatorRenderer.draw_connectors` imports the `draw_connectors` function from `NavigatorRenderer` found within the same file as the annotated function).

`HINT` refers to a string describing what the `IMPORT`ed reference is. Multi-line hints should be indented in the same way as the example.

## Task 1: parent path

Render the path to the parent node on the top line, joined by "->".

If the path is too long, truncate it as follows:

- Render the root
- Render "..."
- Render as many nodes as possible to the parent node.
  If that is still to long, render only "..." and the parent node.

Example:
Root -> ... -> Grandparent -> Parent

For this warm up task, we provide step-by-step instructions for how to implement the functionality using `nlmc`.

To start this task, switch over to the `task1` branch.

```bash
git checkout task1
rm -rf .nlmc
nlmc init
```

### Step 1: Update `NodeData` and `NavigatorState._annotate_tree`

The first thing we need to do is get the path from the current node to the root. To start, in `navigator.py`, add the path to the `NodeData` class.

```python
@dataclass(frozen=True)
class NodeData:
    """Data for a node."""

    # Depth of subtree rooted at this node
    # NB: a leaf node has depth 1
    tree_depth: int
    # Number of descendants in the subtree rooted at this node
    descendants: int
    # Path from the root to this node
    path: list[AnnotatedNode]
```

Rather than compute the path from scratch each time, let's make use of the recursive nature of `NavigatorState._annotate_tree`.
Update the function to take the current path as an additional argument. This will allow it to build the path to the current node incrementally given the path to the parent node.

```python
    def _annotate_tree(
        self,
        node: Node,
        path_to_parent: list[AnnotatedNode],
    ) -> AnnotatedNode:
        """
        @nlmeta

        Recursively annotates a tree with NodeData.

        Returns:
            The annotated version of the (tree rooted at the) node.

        Dependencies:
            .node: module for tree structure.
            NodeData: dataclass for node data.
            AnnotatedNode: class for annotated nodes.
        """
```

Next, update `NavigatorState.__init__` to pass in the empty path when calling `self._annotate_tree`.

```python
    def __init__(self, root: Node):
        self.root: AnnotatedNode = self._annotate_tree(root, [])
        self.current_node: AnnotatedNode = self.root
```

Now you're ready for your first invocation of `nlmc`.
If all goes according to plan, here's what we expect to happen:

- First, `_annotate_tree` will be re-compiled because the docstring has been updated.
- Second, `navigation_loop` will be re-compiled because it declares `NavigatorState` as a dependency.
  - Note updating any member of a dependency (in this case `_annotate_state`) counts as changing the dependency.

However, because this update constitutes only internal logic, it does not necessitate any changes in the navigation loop. Hence, compilation will stop here. (Note however that if `navigation_loop` were to be updated, this could lead to further cascading re-compilations.)

Go ahead now and invoke `nlmc`.

```bash
$ nlmc
```

### Step 2: Add `render_parent_path` and update `render_parent`

Now let's make use of this functionality.

Because the requirements are somewhat involved, we'll create a new function to handle rendering the parent path.
Create a `NavigatorRenderer.render_parent_path` function in `NavigatorRenderer`.
Note that the docstring essentially repeats the requirements and declares `NavigatorState` as a dependency.

```python
    def render_parent_path(self, state: NavigatorState) -> None:
        """
        @nlmeta

        Render the path to the parent node on the top line, joined by "->".

        If the path is too long, truncate it as follows:
        - Render the root
        - Render "..."
        - Render as many nodes as possible to the parent node.
        If that is still to long, render only "..." and the parent node.

        Example:
        Root -> ... -> Grandparent -> Parent

        Args:
            state: The current navigator state

        Dependencies:
            NavigatorState
        """
```

To make sure this function gets used, we also need to update the function responsible for rendering the parent.
Add `NavigatorRenderer.render_parent_path` as a required dependency to `NavigatorRenderer.render_parent`:

```python
    def render_parent(self, state: NavigatorState) -> None:
        """
        @nlmeta

        Render the parent node

        [lines omitted]
            NavigatorRenderer.draw_connectors: use to draw connectors after tree structure has been set.
            NavigatorRenderer.erase_below: use to erase the screen below a given y coordinate.
            NavigatorRenderer.render_parent_path: use this function to render the parent path on the top line.
        """
```

This time, we expect the following to happen:

- `render_parent_path` will be compiled first because it is a brand new function.
- `render_parent` will be re-compiled because it has a new dependency.
- Any units that depend on `render_parent` will also be potentially re-compiled - though as with before, we don't expect any of them to change.

Note that if you don't want to wait, it's safe to quit the compilation process once `render_parent` has passed - all accepted changes will be saved. The stale units will be re-compiled on the next invocation of `nlmc` (though in this case, we won't be needing them anyway.)

```bash
$ nlmc
```

Once you're satisfied with the implementation, feel free to try out the new functionality!

```bash
$ navigator 8
```

### Step 3: Make some new tests

Chances are, your terminal window is wide enough that you aren't able to easily test the truncation behavior.
As a final step, let's remedy that by generating some new test cases.

Add the following lines to the `tests.py` file.

```python
def make_deep_tree(size: int, seed: int) -> Node:
    """
    @nlmeta

    Create a deep tree of a given size.

    Dependencies:
        .node: module for tree structure.
    """


def make_wide_tree(size: int, seed: int) -> Node:
    """
    @nlmeta

    Create a wide tree of a given size.

    Dependencies:
        .node: module for tree structure.
    """
```

Also update the `make_tests` function to use the new test generators:

```python
def create_test_cases() -> dict[int, Node]:
    """
    @nlmeta

    Create test cases for the user study.

    Dependencies:
        make_tree: creates a test case.
        make_deep_tree: creates a deep tree test case.
        make_wide_tree: creates a wide tree test case.
    """
```

Then run `nlmc` again.

```bash
$ nlmc
```

Note that `cli.py` was automatically updated with the new test cases, because of the dependence on `create_test_cases`!

When you're done, you can try one of the "deep" test cases to see if the truncation of the parent path is functioning properly.

This completes the first task!

## Task 2: Node status

For this task, we will add an arbitrary notion of a status to each node and will change the color of the node based on it.

- working: color the node orange
- pending changes: color the node blue
- no changes: color the node green
- not checked: color the node red

While we will still provide a general sequence of instructions, this time it will be up to you to write the actual docstrings.

We'll start by initializing `nlmc` from the `task2` branch:

```bash
$ git checkout task2
$ rm -rf .nlmc
$ nlmc init
```

### Step 1: Create `NodeStatus` and update `Node` in `node.py`

As a starting point, create a new data type to hold the node statuses, and update the `Node` class to take this as a parameter:

```python
from __future__ import annotations

from enum import IntEnum


class NodeStatus(IntEnum):
    """Status of a node."""

    WORKING = 1
    PENDING_CHANGES = 2
    NO_CHANGES = 3
    NOT_CHECKED = 4


class Node:
    """A simple node class for demonstration purposes."""

    def __init__(
        self,
        name: str,
        status: NodeStatus,
        parent: Node | None = None,
    ):
        self.name = name
        self.status = status
        self.parent = parent
        self.children: list[Node] = []
```

Now run `nlmc`.

```bash
$ nlmc
```

Note: when updating the tests, the LLM often chooses to generate a static status, e.g.,

```gitdiff
+from .node import NodeStatus


 def make_deep_tree(size: int, seed: int) -> Node:
@@ -87,7 +88,7 @@ def make_tree(size: int, seed: int) -> Node:
     random.seed(seed)

     # Create the root node
-    root = Node(name="0")
+    root = Node(name="0", status=NodeStatus.NOT_CHECKED)

     # List to keep track of all nodes for random parent selection
     nodes: list[Node] = [root]
@@ -98,7 +99,7 @@ def make_tree(size: int, seed: int) -> Node:
         parent = random.choice(nodes)

         # Create a new node with the selected parent
-        new_node = Node(name=str(i), parent=parent)
+        new_node = Node(name=str(i), status=NodeStatus.NOT_CHECKED, parent=parent)

         # Add the new node as a child to the parent
         parent.add_child(new_node)
No errors compiling make_tree in navigator/tests.py. [a] to accept, [e] to edit, [q] to quit:
```

While this is perfectly legal code, it doesn't make for very interesting output.

In this case, you can try the `edit` feature. By inputting `e` during the `nlmc` compilation, you can open a `code` editor and make arbitrary edits.

Any changes you make WILL propagate: e.g., if you add a dependency, the unit will be re-compiled anew with the dependency; you can even add a new function to be compiled, if you wish.

In this case, it's sufficient to simply update the implementation to use `random.choice` instead:

```gitdiff
+from .node import NodeStatus


 def make_deep_tree(size: int, seed: int) -> Node:
@@ -87,7 +88,7 @@ def make_tree(size: int, seed: int) -> Node:
     random.seed(seed)

     # Create the root node
-    root = Node(name="0")
+    root = Node(name="0", status=random.choice(list(NodeStatus)))

     # List to keep track of all nodes for random parent selection
     nodes: list[Node] = [root]
@@ -98,7 +99,7 @@ def make_tree(size: int, seed: int) -> Node:
         parent = random.choice(nodes)

         # Create a new node with the selected parent
-        new_node = Node(name=str(i), parent=parent)
+        new_node = Node(name=str(i), status=random.choice(list(NodeStatus)), parent=parent)

         # Add the new node as a child to the parent
         parent.add_child(new_node)
```

Save the file and then type `a` in the command line to accept your changes. (Typically the LLM will see the updates and use `random.choice` for the other two test generation functions without needing your help.)

In general, developing with `nlmc` is an interative process: it helps generate a starting point which you can tweak until you're content; it also helps identify when your changes might require adaptations elsewhere in the codebase.

### Step 2: Create the `NavigatorRenderer.render_node` method in `navigator.py`.

Your main task is to finish the docstring of the following new function:

```python
    def render_node(self, node: AnnotatedNode, x: int, y: int, highlight: bool = False):
        """
        @nlmeta

        Render the node at the given coordinates.

        # TODO: your instructions here! e.g. the colors to use for each status.

        Args:
            node: The node to render
            x: X coordinate
            y: Y coordinate
            highlight: Whether to highlight the node

        Dependencies:
            .node: module for tree structure and status codes.
            init_colors: function that initializes all necessary color pairs.
        """
```

Next, add `NavigatorRenderer.render_node` as a dependency to `NavigatorRenderer.render_as_terminal` (the function which handles rendering the terminal nodes in the portion of the tree that is visible).

```python
    def render_as_terminal(
        self,
        node: AnnotatedNode,
        x: int,
        y: int,
        highlight: bool = False,
    ) -> bool:
        """
        @nlmeta

        Render a node as a terminal.

        ...

        Dependencies:
            context: NavigatorRenderer.render_tree: uses this function to render the terminal.
            NavigatorRenderer.render_node: use this function to render the node.
        """
```

Finally, we need to create one last function: a top-level function `init_colors` in `navigator.py`.

```python
def init_colors():
    """
    @nlmeta

    Initialize ALL color pairs for rendering.

    Dependencies:
        .node.NodeStatus: class for node status.
        context: NavigatorRenderer.render_node: Read the docstring carefully to ensure all colors are set up correctly.
    """
```

Note that `init_colors` declares `NavigatorRenderer.render_node` as a **context** dependency, while `NavigatorRenderer.render_node` declares `init_colors` as an (implicitly) **required** dependency. This is because:

1. `init_colors` needs to use `NavigatorRenderer.render_node`'s docstring to determine which colors are necessary, and
1. `NavigatorRenderer.render_node` needs to know how `init_colors` chooses to initialize curses for color rendering.

By declaring one of the dependencies as `context`, we avoid creating a cycle in the (`required`) dependency graph.

When you're happy with your docstring in `render_node`, you can invoke `nlmc` and see how it does!

```bash
$ nlmc
```

Note that you may need to `edit` a few times if the LLM makes any mistakes (e.g., forgetting to add an import).

Hopefully, the colors have been updated:

```bash
$ navigator 8
```

### Step 3 (optional): update the colors along the parent path.

There's a number of ways to achieve this, but perhaps the easiest way is to add `render_node` as a dependency in `render_parent_path` and slightly adjust the docstring.

If you're running short on time, however, you should skip this and instead move to the third and final task.

## Task 3: Reachable nodes

For this task, you will be asked to implement a new feature with minimal guidance.

As with before, start by moving to the `task3` branch:

```bash
git checkout task3
rm -rf .nlmc
nlmc init
```

### Requirements

1. Add a boolean property to `Node`s, indicating whether they are `active`.

2. Define a node as `reachable` if the entire path from the root to the node is active (including the node itself).

Update the node rendering so that a node is colored if it is reachable, and dimmed (`curses.A_DIM` attribute) otherwise.

This should be be applied to both terminal nodes, and the parent path.

3. Optional: update the count to show only reachable descendants, i.e., "node_name (+X more reachable)"
