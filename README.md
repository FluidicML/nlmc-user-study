# User study for nlmc

This user study has you implement 3 new features for a terminal-based tree visualizer/navigator.

> Hint: if you're viewing this in VSCode, opening this in preview mode will provide a better viewing experience.

## Set up

> NOTE! If you are participating in the official user study, follow the setup instructions at the end of the pre-survey instead.

Clone [nlmc](https://github.com/FluidicML/nlmc) in a folder adjacent to this one.
In an `.env` file at the root-level of the newly cloned repository, add the following:

```
ANTHROPIC_API_KEY=<KEY>
```

where `<KEY>` refers to your own Anthropic key.

> You should have been provided with a zip file containing the correct directory structure and key pre-installed if you're participating in the official user study.

Make sure your python version is at least 3.12

```bash
$ python3 --version
```

Next, from within the `nlmc-user-study` project, run:

```bash
$ python3 -m venv .venv --prompt nlmc-user-study
$ source .venv/bin/activate
$ poetry install
$ npm init -y
$ npm install pyright
```

If you don't have poetry or npm, you will need to install them:

- [poetry](https://python-poetry.org/docs/#installation)
- [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)

Lastly, install [VS Code](https://code.visualstudio.com/docs/setup/setup-overview#_set-up-vs-code-for-your-platform).

Make sure to follow the instructions to install the `code` in your `PATH`. Test this out by running

```bash
$ code
```

# Task setting: tree visualizer

The goal of this user study is to introduce you to a new code generation tool. You will be performing several tasks to modify an existing tree visualization utility with some additional features.

First, let's see how the utility currently works. At the top level of the `nlmc-user-study` project, try running:

```bash
$ navigator 8
```

Note the controls in the bottom right.

## End product

This user study is designed to be an interactive walkthrough. You will be walked through adding 3 new features to the navigator. Here are the changes that you will be (re-)implementing:

1. The top line now contains a path from the root, rather than just the immediate parent.
1. The nodes are color coded based on status.
1. Some nodes are rendered as dimmed ("unreachable"). The descendent counts now also only report reachable nodes.

Don't worry if you don't understand what some of these changes mean yet; you'll be getting detailed instructions later.

Next, switch over to the `reference` branch. This branch lets you see how the intended end product works.

```bash
$ git checkout reference
$ navigator 8
```

When you are done, switch back over to the `main` branch.

```bash
$ git checkout main
```

> IMPORTANT! Make sure you switch back over to main for this next part!

## Code base

The tool is implemented in the `navigator` directory. **Note that the user study will only ask you to make changes to the python files in this directory.**

This section is meant only to familiarize you with the project’s structure; please hold off on inspecting the files contents for now as we’ll dive into them as the tasks progress.

### `cli.py`

This file contains the logic for parsing the command line arguments, and is the entrypoint that starts the navigation loop.

### `tests.py`

This file defines the test cases, which consists of randomly constructed trees.

### `node.py`

`node.py` defines a very basic tree data structure. Each `Node` instance has references to its children and parent.

### `navigator.py`

`navigator.py` contains the bulk of the rendering logic.

#### `NavigatorState` and `AnnotatedNode`

`NavigatorState` is where the "data" about the tree is stored, specifically, where you are currently located as you walk the tree.

To make rendering more efficient and avoiding recomputing the same properties every time the screen needs to be refreshed, certain metadata is precomputed with the `_annotate_tree` method during initialization:

- Tree height (maximum height of each subtree). This is used by the rendering logic to optimize the layout of the tree.
- Descendant count (total nodes in each subtree). This is used to display how much of the tree is hidden when it won't fit on the screen.

#### `NavigatorRenderer`

All the rendering logic is handled in `NavigatorRenderer`. The main entrypoint is `render`.

## `curses`

The Python curses library powers the terminal interface by:

- Managing terminal I/O
- Enabling text drawing at specific coordinates (x,y positions)
- Providing text styling capabilities (like highlighting for the current node)
- Managing terminal dimensions and constraints
- Handling terminal refresh and screen clearing operations

Don't worry if you are not familiar with this library: the LLM is quite good at generating `curses` code, and the APIs are not too complex.

# Overview of `nlmc`

Let's begin by initializing the project.

In general, you only need to remember one command:

```bash
$ nlmc [navigator/path/to/file.py]
```

If no file is specified, `nlmc` will compile the entire `navigator` project.

The core transformation that `nlmc` will perform is **replacing the body of a function marked for compilation**. A function is considered marked for compilation if the first non-blank line of the function's docstring is `@nlmeta`.

## Controlling `nlmc`

You have 3 main ways to control what the LLM generates:

- The **type of the function**. This will always be preserved by the compiler. All generations are passed through a type checker (`pyright`, in our case), and you will be alerted of any errors.
- The **docstring**. This will also always be preserved by the compiler.
- The **implementation**. This will be repared by the generation. Providing pseudocode here can be a useful way to guide the implementation. However, for particularly complex problems, declaring an algorithm in the docstring is a more persistent way to guide the behavior. Note that the LLM will attempt to follow the existing implementation as much as possible in subsequent implementations, so when making large changes, it may help to delete the existing implementation to force a fresh start.

## Example

Let's look at an example. (Don't worry about understanding what's going on here, and focus instead of the sections in the docstring.)

```python
def fibonacci(
    n: int,
) -> int:
    """
    @nlmeta

    Computes the fibonacci function of n. Uses memoization to speed up the computation.

    Algorithm:
    - if n = 0 or 1, return 0 or 1, respectively
    - check cache, and return value if it's a hit
    - otherwise, compute fibonacci(n-1) + fibonacci(n-2)
    - store result in cache, and return value

    Args:
        n: the input

    Dependencies:
        .utils.Cache
        context: Simulator.count_rabbits: uses this function to estimate a rabbit population over time.
            Note that this loop is very hot, hence the need for an optimized implementation.
    """
    ...
```

### Marking a unit for compilation with @nlmeta

Note the `@nlmeta` tag in the docstring, which marks this as a unit for compilation. This must be on the first line of the docstring.

```python
def fibonacci(
    n: int,
) -> int:
    """
    @nlmeta
    ...
```

### Providing context to the LLM with dependencies

This docstring follows typical Python conventions and is provided, in full, as context to the configured LLM. Of the blocks written in this docstring, only `Dependencies` is parsed specially.

```python
    ...
    Args:
        n: the input

    Dependencies:
        .utils.Cache
        context: Simulator.count_rabbits: uses this function to estimate a rabbit population over time.
            Note that this loop is very hot, hence the need for an optimized implementation.
    """
    ...
```

Lines indented within the `Dependencies` block should be written using the following syntax:

`[context: | required:] IMPORT[: HINT]`

At a high level, each dependency specifies additional text which the language model sees during generation.

`IMPORT` refers to a reference to some Python object. It follows Python's import syntax. For instance, `.utils` would pass the entire file `utils.py` to the LLM, while `.utils.Cache` would import just the `Cache` class in `utils.py`.

Local symbols are also resolved (for instance `Simulator.count_rabbits` imports the `count_rabbits` function from `Simulator` found within the same file as the annotated function).

You can also suggest to the LLM how the `IMPORT`ed reference should be used by providing a `HINT`. `HINT`s can span multiple lines by indenting the subsequent lines as seen in the example. The `HINT` can also be left out, in which case the LLM is passed the dependency as is, without any accompanying text.

Finally, The `required` and `context` keywords are used to control the order of compilation. `required` units are always compiled first. `context` units allow importing context without creating cycles in the dependency graph. If neither are specified (as in the case of `.utils.Cache` in the example), `required` is assumed.

# Task 1: Parent Path

For this warm up task, we provide step-by-step instructions for how to implement some functionality using `nlmc`.

Feel free to copy / paste changes from this README into the codebase; the main objective is just to get a feel for running `nlmc`.

We'll conduct this task on the `task1` branch.

```bash
$ git checkout task1
$ rm -rf .nlmc
$ nlmc init
```

> Note: `rm -rf .nlmc` and `nlmc init` are just used to reset / initialize the cache to a consistent state for this user study. You wouldn’t normally run these commands during everyday use.

## Spec

Render the path to the parent node on the top line, joined by "->".

If the path is too long, shorten it by eliding the middle of the path with ellipses.

We should try to include as many nodes along the path as possible, while keeping the same number of nodes before and after the ellipses

Example:
root -> node1 ... -> node2 -> parent

## Step 1: Update `NodeData` and `NavigatorState._annotate_tree`

The first thing we need to do is get the path from the current node to the root. Rather than compute the path from scratch each time (which could be unacceptably slow for larger trees), let's precompute the path for each node and store it in the metadata in `NavigatorState._annotate_tree`.

To start, in `navigator.py`, add `path_to_parent` to the `NodeData` class. Make sure to include the comment so the LLM knows what `path_to_parent` should store!

```python
@dataclass(frozen=True)
class NodeData:
    """Data for a node."""

    # Height of subtree rooted at this node
    # NB: a leaf node has height 1
    height: int
    # Number of descendants in the subtree rooted at this node
    descendants: int
    # Path from the root to this node's parent (inclusive)
    path_to_parent: list[AnnotatedNode]
```

Next, update the `NavigatorState._annotate_tree` function to take the current path as an additional argument. This will allow it to build the path to the current node recursively given the path to the parent node.

```python
    def _annotate_tree(
        self,
        node: Node,
        path_to_parent: list[AnnotatedNode],  # add this argument
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
        ...
```

We also need to update `NavigatorState.__init__` to pass in the empty path when calling `self._annotate_tree`.

```python
    def __init__(self, root: Node):
        self.root: AnnotatedNode = self._annotate_tree(root, [])
        self.current_node: AnnotatedNode = self.root
```

### Your first `nlmc`

Now you're ready for your first invocation of `nlmc`!

If all goes according to plan, here's what we expect to happen:

- First, `_annotate_tree` will be re-compiled because its declaration has been updated.
- Second, `navigation_loop` will be re-compiled because it declares `NavigatorState` as a dependency.
  - Note updating any member of a dependency (in this case `_annotate_state`) counts as changing the dependency.

However, because this update constitutes only internal logic, it does not necessitate any changes in the navigation loop. Hence, compilation will stop here. (Note however that if `navigation_loop` were to be updated, this could lead to further cascading re-compilations.)

Building with `nlmc` is designed to be an interactive process. Whenever a unit is compiled, there are three possible outcomes:

1. The LLM declines to make a change, because the existing implementation is sufficient.
1. The LLM makes a change and it passes the type checker.
1. The LLM makes a change and it fails the type checker.

In the first case, the compilation will proceed without any input from the user.

For the second case, you will be prompted to either `edit` or `quit`. If you choose to edit, you will be dropped in a `VScode` window to make changes. Note that any changes made during editing will trigger a re-compilation by the LLM. On the other hand, if you choose to `quit`, the compilation will abort and the current changes will be discarded.

For the third case, you have the additional option to `accept` the changes as-is, which will allow compilation to continue with the next unit.

> Once a change has been accepted, it won't be discarded. So if you accept one change and quit the second change, the first change will still be there. This means you are safe to `Ctrl-C` in the middle of compilation without losing your work.

Go ahead now and invoke `nlmc`, and follow the onscreen instructions.

```bash
$ nlmc
```

## Step 2: Add `render_parent_path` and update `render_parent`

Now that we have access to the parent path in the `AnnotatedNode`, let's make use of this functionality.

Because the requirements are somewhat involved, we'll create two new functionw to handle rendering the parent path.

First, create a `NavigatorRenderer.render_parent_path` function in `NavigatorRenderer`.
Note that the docstring essentially repeats the requirements and declares `NavigatorState` as a dependency.

```python
    def render_parent_path(self, state: NavigatorState) -> None:
        """
        @nlmeta

        Render the path to the parent node on the top line, joined by " -> ".

        Algorithm:
        - First try to render the full path.
        - If the full path is too long, shorten it by eliding the end of the path with ellipses ("...").

        Example:
            root -> node1 -> node2 -> ...

        Args:
            state: The current navigator state

        Raises:
            ValueError: If the path is too long to render, or if the current node has no parent.

        Dependencies:
            NavigatorState
        """
```

Finally, to make sure this functionality gets used, we also need to update the function responsible for rendering the parent.
Add `NavigatorRenderer.render_parent_path` as a required dependency to `NavigatorRenderer.render_parent`:

```python
    def render_parent(self, state: NavigatorState) -> None:
        """
        @nlmeta

        Render the parent node

        [lines omitted]
            NavigatorRenderer.render_connectors: use to render connectors after tree structure has been set.
            NavigatorRenderer.compare_results: use this function to compare configurations.
            NavigatorRenderer.render_parent_path: use this function to render the full parent path on the top line.
        """
```

This time, we expect the following to happen:

- `render_parent_path` will be compiled first because it is a brand new function.
- Then `render_parent` will be re-compiled because it has a new dependency.
- Any units that depend on `render_parent` will also be potentially re-compiled - though as with before, we don't expect any of them to change.

Note that if you don't want to wait, it's safe to quit the compilation process once `render_parent` has passed - all accepted changes will be saved. The stale units will be re-compiled on the next invocation of `nlmc` (for this case, we won't be needing them anyway.)

```bash
$ nlmc
```

Once you're satisfied with the implementation, feel free to try out the new functionality!

```bash
$ navigator 8
```

This completes the first task!

# Task 2: Node status

While we will still provide a general sequence of instructions, this time it will be up to you to complete the core function by:

- completing the key section of the docstring
- figure out how to declare it as a dependency to make use of the new functionality.

We'll start by initializing `nlmc` from the `task2` branch:

```bash
$ git clean -f
$ git stash
$ git checkout task2
$ rm -rf .nlmc
$ nlmc init
```

## Spec

Add a status to each node, and apply color to the node based on its status.

- working: color the node yellow
- pending changes: color the node blue
- no changes: color the node green
- not checked: color the node red

## Step 1: Create `NodeStatus` and update `Node` in `node.py`

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

## Step 2: Create the `NavigatorRenderer.render_node` method in `navigator.py`.

Create the following new function in `NavigatorRenderer` and complete the docstring:

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
            NavigatorRenderer.init_colors: function that initializes all necessary color pairs.
        """
```

> For your convenience, here's the spec for this task again (though you're free to choose your own colors if you wish!):
>
> Add a status to each node, and apply color to the node based on its status.
>
> - working: color the node yellow
> - pending changes: color the node blue
> - no changes: color the node green
> - not checked: color the node red

Due to a quirk of how `curses` work, we'll also need to initialize the color functionality separation. Let's make an init function and call it in `NavigatorRenderer.__init__`:

```python
class NavigatorRenderer:
    """Renderer for the navigator."""

    def __init__(self, stdscr: curses.window, max_children: int = 10):
        self.max_children = max_children
        self.stdscr = stdscr
        self.init_colors()

    def init_colors(self):
        """
        @nlmeta

        Initialize ALL color pairs for rendering.

        Dependencies:
            .node.NodeStatus: class for node status.
            context: NavigatorRenderer.render_node: Read the docstring carefully to ensure all colors are set up correctly.
        """
```

Note that `NavigatorRenderer.init_colors` declares `NavigatorRenderer.render_node` as a **context** dependency, while `NavigatorRenderer.render_node` declares `init_colors` as an (implicitly) **required** dependency. This is because:

1. `init_colors` needs to use `NavigatorRenderer.render_node`'s docstring to determine which colors are necessary, and
1. `NavigatorRenderer.render_node` needs to know how `init_colors` chooses to initialize curses for color rendering.

By declaring one of the dependencies as `context`, we avoid creating a cycle in the (`required`) dependency graph.

Finally, add `NavigatorRenderer.render_node` as a dependency to the following functions:

- `NavigatorRenderer.measure_or_render_terminal`
- `NavigatorRenderer.measure_or_render_tree`
- `NavigatorRenderer._render_path_with_ellipses`

Include a short hint so the LLM knows what it's supposed to do with this new dependency.

When you're happy with your changes, you can invoke `nlmc` and see how it does!

```bash
$ nlmc
```

Note that you may need to `edit` a few times if the LLM makes any mistakes (e.g., forgetting to add an import).

Hopefully, the colors have been updated:

```bash
$ navigator 8
```

# Task 3: Reachable nodes

Congratulations for making it this far! For this final task, you will be asked to implement a new feature with minimal guidance.

Note that the goal is not to evaluate your ability to actually implement the feature, so much as to give you an opportunity to use `nlmc` without training wheels.

As with before, start by moving to the `task3` branch:

```bash
git checkout task3
rm -rf .nlmc
nlmc init
```

## Hints

1. For parts 2 and 3, it will help to refresh yourself on what we did in Task 1.
1. To prevent too many updates from building up, run `nlmc` as you go (e.g., after each part).

## Spec

### Part 1

Add a boolean property to `Node`s, indicating whether they are `active`.

### Part 2

Given a tree, a node is `reachable` if the entire path from the root to the node is active (including the node itself).

Update the node rendering so that a node is colored if it is reachable, and dimmed (`curses.A_DIM` attribute) otherwise.

This should be be applied to nodes in the tree as well as nodes along the parent path.

### Part 3

Update the count to show only reachable descendants, i.e., "node_name (+X more reachable)" instead of "node_name (+X more descendants)"
