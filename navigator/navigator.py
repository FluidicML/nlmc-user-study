"""Terminal-based graph navigator."""

from __future__ import annotations

import curses
from dataclasses import dataclass
from enum import Enum

from .node import Node


class Key(Enum):
    """Key codes for navigation."""

    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    QUIT = 5


@dataclass(frozen=True)
class NodeData:
    """Data for a node."""

    # Height of subtree rooted at this node
    # NB: a leaf node has height 1
    height: int
    # Number of reachable descendants in the subtree rooted at this node
    descendants: int
    # Path from the root to this node's parent (inclusive)
    path_to_parent: list[AnnotatedNode]
    # A node is reachable if it is active and its parent is reachable
    reachable: bool


class AnnotatedNode:
    """A node annotated with data."""

    def __init__(
        self,
        node: Node,
        data: NodeData,
        parent: AnnotatedNode | None = None,
        children: list[AnnotatedNode] | None = None,
    ):
        self.node = node
        self.data = data
        self.parent = parent
        self.children = children or []

    def __repr__(self):
        return self.node.__repr__()


class NavigatorState:
    """State of the navigator."""

    def __init__(self, root: Node):
        self.root: AnnotatedNode = self._annotate_tree(root, [])
        self.current_node: AnnotatedNode = self.root

    def handle_keypress(self, key: Key) -> AnnotatedNode | None:
        """
        @nlmeta

        Handle arrow keypress events.

        Key.LEFT: Move to parent
        Key.RIGHT: Move to first child
        Key.UP and Key.DOWN: Move between siblings
        Key.QUIT: Exit the navigator

        Returns:
            The new current node or None if exiting.

        Dependencies:
            .node.Node: class for tree structure.
            Key: enum for key codes.
        """
        if key == Key.QUIT:
            return None

        elif key == Key.LEFT:
            # Move to parent if it exists
            if self.current_node.parent:
                self.current_node = self.current_node.parent

        elif key == Key.RIGHT:
            # Move to first child if any children exist
            if self.current_node.children:
                self.current_node = self.current_node.children[0]

        elif key == Key.UP or key == Key.DOWN:
            # Move between siblings
            if self.current_node.parent:
                siblings = self.current_node.parent.children
                current_index = siblings.index(self.current_node)

                if key == Key.UP and current_index > 0:
                    # Move to previous sibling
                    self.current_node = siblings[current_index - 1]
                elif key == Key.DOWN and current_index < len(siblings) - 1:
                    # Move to next sibling
                    self.current_node = siblings[current_index + 1]

        return self.current_node

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
        # Recursively annotate all children
        annotated_children: list[AnnotatedNode] = []

        # Initialize tree height and descendant count
        max_child_height = 0
        total_descendants = 0

        # Determine if this node is reachable
        # Root node is reachable if it's active
        # Other nodes are reachable if they're active and their parent is reachable
        is_root = len(path_to_parent) == 0
        parent_reachable = True if is_root else path_to_parent[-1].data.reachable
        node_reachable = node.active and parent_reachable

        # Create NodeData for this node
        node_data = NodeData(
            height=1,  # Default height for a leaf node
            descendants=0,  # Default descendants for a leaf node
            path_to_parent=path_to_parent.copy(),  # Copy the path to avoid modifying the original
            reachable=node_reachable,
        )

        # Create the annotated node without setting parent or children yet
        annotated_node = AnnotatedNode(node=node, data=node_data)

        # Create the path for children by adding this node to the path
        path_for_children = path_to_parent.copy()
        path_for_children.append(annotated_node)

        # Process each child
        for child in node.children:
            # Recursively annotate the child with the updated path
            annotated_child = self._annotate_tree(child, path_for_children)
            annotated_children.append(annotated_child)

            # Update maximum child height
            max_child_height = max(max_child_height, annotated_child.data.height)

            # Only count reachable descendants
            if annotated_child.data.reachable:
                # Add child's descendants plus the child itself to total descendants
                total_descendants += annotated_child.data.descendants + 1

        # Update tree height for this node if it has children
        if node.children:
            height = max_child_height + 1

            # Update the NodeData with the calculated values
            # Since NodeData is frozen, we need to create a new instance
            node_data = NodeData(
                height=height,
                descendants=total_descendants,
                path_to_parent=path_to_parent.copy(),
                reachable=node_reachable,
            )

            # Update the annotated node with the new data
            annotated_node.data = node_data

        # Set up parent-child relationships for the annotated nodes
        for child in annotated_children:
            child.parent = annotated_node
            annotated_node.children.append(child)

        return annotated_node


@dataclass(frozen=True)
class RenderConfiguration:
    """A configuration for rendering the parent node."""

    current_node: AnnotatedNode
    siblings_before: list[AnnotatedNode]
    siblings_after: list[AnnotatedNode]
    non_visible_siblings_before: int
    non_visible_siblings_after: int
    sibling_height: int

    @classmethod
    def from_node(
        cls,
        node: AnnotatedNode,
        visible_siblings_before: int,
        visible_siblings_after: int,
        sibling_height: int,
    ) -> RenderConfiguration:
        """
        @nlmeta

        Create a RenderConfiguration from a node and parameters about visible siblings.

        Args:
            node: The current node
            visible_siblings_before: Number of siblings to show before the current node
            visible_siblings_after: Number of siblings to show after the current node
            sibling_height: Height of subtree when rendering siblings

        Returns:
            A RenderConfiguration object

        Raises:
            ValueError: If the node has no parent
        """

        # Ensure the node has a parent
        if not node.parent:
            raise ValueError("Node must have a parent")

        # Get all siblings from the parent
        siblings = node.parent.children

        # Find the index of the current node among siblings
        current_index = siblings.index(node)

        # Calculate which siblings to include before the current node
        start_before = max(0, current_index - visible_siblings_before)
        siblings_before = siblings[start_before:current_index]

        # Calculate which siblings to include after the current node
        end_after = min(len(siblings), current_index + 1 + visible_siblings_after)
        siblings_after = siblings[current_index + 1 : end_after]

        # Calculate how many siblings are not visible
        non_visible_siblings_before = current_index - len(siblings_before)
        non_visible_siblings_after = (
            len(siblings) - current_index - 1 - len(siblings_after)
        )

        # Return a new RenderConfiguration
        return cls(
            current_node=node,
            siblings_before=siblings_before,
            siblings_after=siblings_after,
            non_visible_siblings_before=non_visible_siblings_before,
            non_visible_siblings_after=non_visible_siblings_after,
            sibling_height=sibling_height,
        )


@dataclass(frozen=True)
class RenderResult:
    """A rendering result for a given configuration."""

    configuration: RenderConfiguration
    current_node_height: int
    current_node_position: int
    total_rows_used: int


class Mode(Enum):
    """Mode for measure or render methods."""

    MEASURE = 1
    RENDER = 2


class NavigatorRenderer:
    """Renderer for the navigator."""

    def __init__(self, stdscr: curses.window, max_children: int = 100):
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
        # Check if terminal supports colors
        if not curses.has_colors():
            return

        # Start color mode
        curses.start_color()

        # Define color pairs for each node status
        # Use pair numbers that match NodeStatus enum values for easy reference

        # WORKING status (1) - Yellow
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        # PENDING_CHANGES status (2) - Blue
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

        # NO_CHANGES status (3) - Green
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

        # NOT_CHECKED status (4) - Red
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

    def render_node(self, node: AnnotatedNode, x: int, y: int, highlight: bool = False):
        """
        @nlmeta

        Render the node at the given coordinates.

        If the node is reachable, apply color to the node based on its status:
        - working: color the node yellow
        - pending changes: color the node blue
        - no changes: color the node green
        - not checked: color the node red
        Otherwise, render the node as dimmed.

        Args:
            node: The node to render
            x: X coordinate
            y: Y coordinate
            highlight: Whether to highlight the node

        Dependencies:
            .node: module for tree structure and status codes.
            NavigatorRenderer.init_colors: function that initializes all necessary color pairs.
        """
        node_text = str(node)
        status = node.node.status
        reachable = node.data.reachable

        # Apply styling based on status for reachable nodes
        curses_attr = curses.color_pair(status) if reachable else curses.A_DIM
        if highlight:
            curses_attr |= curses.A_REVERSE

        self.stdscr.attron(curses_attr)

        # Render the node
        self.stdscr.addstr(y, x, node_text)

        # Reset attributes
        self.stdscr.attroff(curses_attr)

    def measure_or_render_terminal(
        self,
        node: AnnotatedNode,
        x: int,
        y: int,
        mode: Mode,
        highlight: bool = False,
    ) -> bool:
        """
        @nlmeta

        Measure or render a node as a terminal.
        i.e., if the node has any children, render "node_name (+X reachable)"

        Args:
            node: The node to render
            x: X coordinate
            y: Y coordinate
            mode: Render mode (MEASURE or RENDER)
            highlight: Whether to highlight node_name

        Returns:
            True if the node was rendered successfully, False otherwise.

        Dependencies:
            context: NavigatorRenderer.measure_or_render_tree: uses this function to render the terminal.
            NavigatorRenderer.render_node: use this function to render nodes.
        """
        # Get terminal dimensions
        max_y, max_x = self.stdscr.getmaxyx()

        # Check if the position is within bounds
        if y >= max_y or x >= max_x:
            return False

        # Format the node name
        node_name = str(node)

        # If the node has children, add the descendant count information
        if node.data.descendants:
            descendant_count = node.data.descendants
            descendant_text = f" (+{descendant_count} reachable)"
        else:
            descendant_text = ""

        # Check if the full text will fit on screen
        if x + len(node_name) + len(descendant_text) >= max_x:
            return False

        if mode == Mode.MEASURE:
            return True

        # Render the node name with proper coloring and highlighting
        self.render_node(node, x, y, highlight)

        if descendant_text:
            # Calculate position for descendant text (right after the node name)
            desc_x = x + len(node_name)

            # Add the descendant text without highlighting
            self.stdscr.addstr(y, desc_x, descendant_text)

        return True

    def render_connectors(self, x: int, ys: list[int], offset: int = 4) -> None:
        """
        @nlmeta

        Render connectors for children.
        - Because we do not know the size or shape of the tree in advance, the connectors should be drawn after the tree has been rendered.
        - The connector should be "├──── " for all but the last child, and "└──── " for the last child (assuming the default offset of 4; adjust as necessary).

        Example: (rendering connectors for the root w/ node x=0, ys=[0,1,2,3,9], offset=4)
            Before:
                Parent
                    (+3 more siblings)
                    Sibling 1
                    Current Node
                    Sibling 2
                    ├---- Node 2
                    |     └---- Node 6 (+5 more descendants)
                    ├---- Node 3
                    ├---- Node 4
                    └---- (+3 more children)
                    (+2 more siblings)

            After:
                Parent
                ├---- (+3 more siblings)
                ├---- Sibling 1
                ├---- Current Node
                ├---- Sibling 2
                |     ├---- Node 2
                |     |     └---- Node 6 (+5 more descendants)
                |     ├---- Node 3
                |     ├---- Node 4
                |     └---- (+3 more children)
                └---- (+2 more siblings)

        Args:
            x: X coordinate for the parent.
            ys: List of Y coordinates for where the children branch off.
            offset: Horizontal offset for the length of the connector

        Dependencies:
            context: NavigatorRenderer.measure_or_render_tree: uses this function to draw the vertical connectors after the tree structure has been set.
            context: NavigatorRenderer.render_parent: uses this function to draw the vertical connectors after the tree structure has been set.
        """
        if not ys:
            return

        # Get terminal dimensions
        max_y, max_x = self.stdscr.getmaxyx()

        if max(ys) >= max_y:
            raise ValueError("Y coordinates out of bounds")

        if x + offset + 1 >= max_x:
            raise ValueError("X coordinate out of bounds")

        ys.sort()  # Sort the y coordinates to ensure correct order

        # Create horizontal connectors for each child
        for i, child_y in enumerate(ys):
            # Determine if this is the last child
            is_last = i == len(ys) - 1

            # Draw the appropriate connector
            if is_last:
                # Last child gets the "└" connector
                connector = "└" + "─" * offset
            else:
                # Other children get the "├" connector
                connector = "├" + "─" * offset

            self.stdscr.addstr(child_y, x, connector)

            # Draw vertical lines connecting siblings
            if not is_last:
                for line_y in range(child_y + 1, ys[i + 1]):
                    self.stdscr.addstr(line_y, x, "│")

    def measure_or_render_tree(
        self,
        node: AnnotatedNode,
        x: int,
        y: int,
        height: int,
        mode: Mode,
        offset: int = 4,
    ) -> tuple[int, int] | None:
        """
        @nlmeta

        Measure or render a node and its children to a maximum height.

        Algorithm:
        - If child_height = 0, render the node as a terminal.
        - If the node has children, recursively render up to self.max_children children at height - 1.
        - If the node has more than self.max_children children, render a placeholder as an additional child "(+X more children)".
        - Return the number of rows used, or -1 for failutre.

        Dependencies:
            context: NavigatorRenderer.measure_or_render_siblings: uses this function to render the full display.
                Refer also to the documentation for render format details.
            context: NavigatorRenderer.measure_tallest_tree: uses this function to measure the tallest tree possible.
            NavigatorRenderer.measure_or_render_terminal: used to render a node as a terminal (rather than a tree).
            NavigatorRenderer.render_connectors: use to render connectors after tree structure has been set.
            NavigatorRenderer.render_node: use this function to render nodes.

        Args:
            node: The node to render
            x: X coordinate
            y: Y coordinate
            height: maximum height of the tree to render
            mode: Render mode (MEASURE or RENDER)
            offset: Connector length for rendering children

        Returns:
            None if the tree cannot be rendered.
            Otherwise, returns a tuple of the number of rows used and the actual height of the tree rendered.
        """
        max_y, max_x = self.stdscr.getmaxyx()

        # If height is 0 or node has no children, render as terminal
        if height == 0 or not node.children:
            if self.measure_or_render_terminal(node, x, y, mode):
                return (1, 0)  # Terminal node takes up 1 row, height 0
            else:
                return None  # Failed to render

        # Render the node itself
        node_text = str(node)
        if x + len(node_text) >= max_x or y >= max_y:
            return None
        if mode == Mode.RENDER:
            # Render the node itself with proper coloring
            self.render_node(node, x, y)

        # Calculate position for children
        child_x = x + offset + 1
        current_y = y + 1

        # Track y positions for all children to draw connectors later
        child_ys: list[int] = []

        # Determine how many children to show
        visible_children = min(
            len(node.children),
            self.max_children,
            max_y - current_y - 1,  # Leave space for the footer
        )
        # Leave space for the placeholder if there are more children
        if visible_children < len(node.children):
            visible_children -= 1

        total_rows = 1  # Start with 1 for the node itself

        # Render each child
        max_child_height = 0
        for i in range(visible_children):
            child = node.children[i]
            child_result = self.measure_or_render_tree(
                child, child_x, current_y, height - 1, mode, offset
            )

            if child_result is None:
                return None

            child_rows, child_height = child_result  # Unpack the result tuple
            max_child_height = max(max_child_height, child_height)
            child_ys.append(current_y)
            current_y += child_rows
            total_rows += child_rows

        # If there are more children than max_children, render a placeholder
        if len(node.children) > self.max_children:
            more_children = len(node.children) - self.max_children
            more_text = f"(+{more_children} more children)"

            if x + len(more_text) >= max_x or current_y >= max_y:
                return None
            if mode == Mode.RENDER:
                self.stdscr.addstr(current_y, child_x, more_text)
            child_ys.append(current_y)
            current_y += 1
            total_rows += 1

        # Draw connectors from node to all children
        if mode == Mode.RENDER:
            self.render_connectors(x, child_ys, offset)

        return (total_rows, max_child_height + 1)

    def measure_tallest_tree(
        self,
        node: AnnotatedNode,
        x: int,
        y: int,
        max_rows: int,
        offset: int = 4,
    ) -> tuple[int, int] | None:
        """
        @nlmeta

        Measure the tallest tree that can be rendered.

        Algorithm:
        - Attempt to render as tree, starting with child_height = 0 and increasing.
            - Increment child_height until either there's no change in the number of lines, or failure.
            - Failure happens when render_tree returns -1 (failure to render) or exceeds max_rows.
        - If failure:
            - If child_height = 0 fails, return -1.
            - Otherwise, render one last time with child_height-1 and return the number of rows.
        - If no change in lines, leave the last rendered tree and just return the number of rows used.

        Args:
            state: The current navigator state
            node: The node to render
            x: X coordinate
            y: Y coordinate
            max_rows: Maximum number of rows to use for rendering
            offset: Connector length for rendering children

        Dependencies:
            NavigatorRenderer.measure_or_render_tree: use this function to render the tree at a given height.

        Returns:
            None if the tree cannot be rendered.
            Otherwise, returns a tuple of the number of rows used and the height of the tree rendered.
        """
        # Start with height 0
        child_height = 0
        prev_rows = -1

        # Incrementally increase height until we see no change in rows or encounter failure
        while True:
            # Try rendering at the current height
            result = self.measure_or_render_tree(
                node,
                x,
                y,
                child_height,
                Mode.MEASURE,
                offset,
            )

            # If rendering failed or exceeds max_rows, go back to the last successful height
            if result is None or (current_rows := result[0]) > max_rows:
                # If we failed at height 0, return None
                if child_height == 0:
                    return None

                # Return the last successful height
                return (prev_rows, child_height - 1)

            # If the number of rows didn't change, we've reached maximum useful height
            if current_rows == prev_rows:
                return (current_rows, child_height - 1)

            # Update tracking variables
            prev_rows = current_rows

            # Increment height for next iteration
            child_height += 1

    def render_tallest_tree(
        self,
        node: AnnotatedNode,
    ):
        """
        @nlmeta

        Render the tallest tree possible for the current node.

        Args:
            node: The node to render

        Dependencies:
            NavigatorRenderer.measure_tallest_tree: use this function to measure the tallest tree.
            NavigatorRenderer.measure_or_render_tree: use this function to render the tree.
            NavigatorRenderer.render_node: use this function to overwrite and highlight the current node.
        """
        y, _ = self.stdscr.getmaxyx()

        # First measure the tallest tree
        result = self.measure_tallest_tree(node, 0, 0, y - 1)
        if result is None:
            return
        _, height = result

        # Then render the tallest tree
        self.measure_or_render_tree(
            node,
            0,
            0,
            height,
            mode=Mode.RENDER,
        )

        # Overwrite and highlight the current node
        self.render_node(node, 0, 0, highlight=True)

    def measure_or_render_siblings(
        self,
        configuration: RenderConfiguration,
        mode: Mode,
    ) -> RenderResult | None:
        """
        @nlmeta

        Render the parent node with a specific configuration of siblings.

        Example:
            - non_visible_siblings_before = 3
            - siblings_before = [Sibling 2]
            - current_node = Current Node
            - siblings_after = [Sibling 1]
            - non_visible_siblings_after = 2
            - sibling_height = 1

        Parent
        ├---- (+3 more siblings)
        ├---- Sibling 2
        ├---- Current Node
        |     ├---- Node 2
        |     |     └---- Node 6 (+5 more descendants)
        |     ├---- Node 3
        |     ├---- Node 4
        |     └---- (+3 more children)
        ├---- Sibling 1
        └---- (+2 more siblings)

        Args:
            configuration: The parent configuration to render

        Returns:
            If successful, a RenderResult object containing the configuration, current node height, and position.
            Else, return None.

        Dependencies:
            RenderConfiguration: class for parent configuration.
            RenderResult: class for rendering result.
            NavigatorRenderer.measure_or_render_tree: use this function to render siblings at a given height.
            NavigatorRenderer.measure_tallest_tree: use this function to measure the tallest tree for the current node.
                use max_rows to leave space for non-visible siblings placeholder.
            context: NavigatorRenderer.render_parent: calls this function to search for a valid rendering configuration.
            NavigatorRenderer.render_node: use this function to render node_text.
        """
        # Get terminal dimensions
        max_y, max_x = self.stdscr.getmaxyx()
        max_y -= 1  # Leave space for the footer line

        # Offset for children
        offset = 4
        child_x = offset + 1

        # Track y positions for all children to draw connectors later
        child_ys: list[int] = []
        current_y = 1

        # Render non-visible siblings before if any
        if configuration.non_visible_siblings_before > 0:
            more_text = f"(+{configuration.non_visible_siblings_before} more siblings)"
            if child_x + len(more_text) >= max_x or current_y >= max_y:
                return None
            if mode == Mode.RENDER:
                self.stdscr.addstr(current_y, child_x, more_text)
            child_ys.append(current_y)
            current_y += 1

        # Render visible siblings before
        for sibling in configuration.siblings_before:
            sibling_result = self.measure_or_render_tree(
                sibling,
                child_x,
                current_y,
                configuration.sibling_height,
                mode,
                offset,
            )
            if sibling_result is None:
                return None

            # Unpack the result tuple - only need the height
            sibling_height, _ = sibling_result

            child_ys.append(current_y)
            current_y += sibling_height

        current_node_y = current_y

        # Calculate max_rows to leave space for siblings after and non-visible siblings after
        remaining_siblings_rows = 0
        for sibling in configuration.siblings_after:
            # Estimate height for each sibling (at least 1 row per sibling)
            remaining_siblings_rows += 1

        # Add 1 row if there are non-visible siblings after
        if configuration.non_visible_siblings_after > 0:
            remaining_siblings_rows += 1

        max_rows_for_current = max_y - current_y - remaining_siblings_rows
        if max_rows_for_current <= 0:
            return None

        # Use render_tallest_tree for the current node
        current_node_result = self.measure_tallest_tree(
            configuration.current_node,
            child_x,
            current_y,
            max_rows_for_current,
            offset,
        )
        if current_node_result is None:
            return None

        # Unpack the result tuple - rows and height
        current_node_rows, current_node_height = current_node_result
        if mode == Mode.RENDER:
            self.measure_or_render_tree(
                configuration.current_node,
                child_x,
                current_y,
                current_node_height,
                mode,
                offset,
            )

        child_ys.append(current_node_y)
        current_y += current_node_rows

        # Render visible siblings after
        for sibling in configuration.siblings_after:
            sibling_result = self.measure_or_render_tree(
                sibling,
                child_x,
                current_y,
                configuration.sibling_height,
                mode,
                offset,
            )
            if sibling_result is None:
                return None

            # Unpack the result tuple - only need the height
            sibling_height, _ = sibling_result

            child_ys.append(current_y)
            current_y += sibling_height

        # Render non-visible siblings after if any
        if configuration.non_visible_siblings_after > 0:
            more_text = f"(+{configuration.non_visible_siblings_after} more siblings)"
            if child_x + len(more_text) >= max_x or current_y >= max_y:
                return None
            if mode == Mode.RENDER:
                self.stdscr.addstr(current_y, child_x, more_text)
            child_ys.append(current_y)
            current_y += 1

        if current_y > max_y:
            return None

        # Draw connectors from parent to all children
        if mode == Mode.RENDER:
            self.render_connectors(0, child_ys, offset)

        # Overwrite and highlight the current node
        if (
            child_x + len(str(configuration.current_node)) >= max_x
            or current_node_y >= max_y
        ):
            return None
        if mode == Mode.RENDER:
            # Overwrite and highlight the current node using render_node
            self.render_node(
                configuration.current_node, child_x, current_node_y, highlight=True
            )

        # Create and return the RenderResult
        return RenderResult(
            configuration=configuration,
            current_node_height=current_node_height,
            current_node_position=current_node_y,
            total_rows_used=current_y - 1,  # Subtract 1 for the header line
        )

    def compare_results(
        self,
        result1: RenderResult,
        result2: RenderResult,
    ) -> int:
        """
        @nlmeta

        Compare two render results.

        Args:
            result1: First result to compare
            result2: Second result to compare

        Returns:
            1 if result1 is better, -1 if result2 is better, 0 if they are equal

        Dependencies:
            RenderResult: dataclass for a result.
            context: NavigatorRenderer.render_parent: uses this function to compare configurations.
                See also documentation for which configurations are preferred.
        """
        # 1. Compare current node height - prefer taller rendering
        if result1.current_node_height > result2.current_node_height:
            return 1
        elif result1.current_node_height < result2.current_node_height:
            return -1

        # 2. If sibling heights are equal, compare how vertically centered the current node is
        # within the screen
        position1 = result1.current_node_position
        position2 = result2.current_node_position
        max_y, _ = self.stdscr.getmaxyx()
        center_y = max_y // 2
        centering1 = abs(position1 - center_y)
        centering2 = abs(position2 - center_y)

        if centering1 < centering2:  # Less distance from center is better
            return 1
        elif centering1 > centering2:
            return -1

        # 3. If heights are equal, compare total number of visible siblings
        config1 = result1.configuration
        config2 = result2.configuration

        siblings1 = len(config1.siblings_before) + len(config1.siblings_after)
        siblings2 = len(config2.siblings_before) + len(config2.siblings_after)

        if siblings1 > siblings2:
            return 1
        elif siblings1 < siblings2:
            return -1

        # 4. If sibling counts are equal, compare sibling height
        if config1.sibling_height > config2.sibling_height:
            return 1
        elif config1.sibling_height < config2.sibling_height:
            return -1

        # If all criteria are equal, the configurations are equivalent
        return 0

    def measure_or_render_path_with_ellipses(
        self,
        prefix_path: list[AnnotatedNode],
        suffix_path: list[AnnotatedNode],
        mode: Mode = Mode.MEASURE,
    ) -> bool:
        """
        @nlmeta

        Try to render a path with ellipses in between.
        If there are no nodes in the suffix, do not render ellipses.

        Args:
            prefix_path: The nodes to render before the ellipses. Cannot be empty.
            suffix_path: The nodes to render after the ellipses
            mode: Render mode (MEASURE or RENDER)

        Returns:
            True if rendering was successful, False otherwise

        Raises:
            ValueError: If the prefix path is empty

        Dependencies:
            Context: NavigatorRenderer.render_parent_path: uses this function to render the path with ellipses.
            NavigatorRenderer.render_node: use this function to render nodes.
        """
        if not prefix_path:
            raise ValueError("Prefix path cannot be empty")

        separator = " -> "
        ellipses_str = "..."
        _, max_x = self.stdscr.getmaxyx()
        current_x = 0

        # Render prefix nodes
        for node in prefix_path:
            # Add separator before all nodes except the first
            if current_x > 0:
                if current_x + len(separator) >= max_x:
                    return False
                if mode == Mode.RENDER:
                    self.stdscr.addstr(0, current_x, separator)
                current_x += len(separator)

            node_str = str(node)
            if current_x + len(node_str) >= max_x:
                return False
            if mode == Mode.RENDER:
                self.render_node(node, current_x, 0)
            current_x += len(node_str)

        if not suffix_path:
            return True

        # Render ellipses
        if current_x > 0:
            if current_x + len(separator) >= max_x:
                return False
            if mode == Mode.RENDER:
                self.stdscr.addstr(0, current_x, separator)
            current_x += len(separator)

        if current_x + len(ellipses_str) >= max_x:
            return False
        if mode == Mode.RENDER:
            self.stdscr.addstr(0, current_x, ellipses_str)
        current_x += len(ellipses_str)

        # Render suffix nodes
        for node in suffix_path:
            if current_x > 0:
                if current_x + len(separator) >= max_x:
                    return False
                if mode == Mode.RENDER:
                    self.stdscr.addstr(0, current_x, separator)
                current_x += len(separator)

            node_str = str(node)
            if current_x + len(node_str) >= max_x:
                return False
            if mode == Mode.RENDER:
                self.render_node(node, current_x, 0)
            current_x += len(node_str)
        return True

    def render_parent_path(self, state: NavigatorState) -> None:
        """
        @nlmeta

        Render the path to the parent node on the top line, joined by "->".

        Algorithm:
        - First try to render the full path.
        - If the full path is too long, shorten it by eliding the middle of the path with ellipses ("...").
        - Start with just the root and parent, then progressively lengthen the prefix and suffix.

        Important: there should always be the same number of nodes before and after the ellipses.

        Example:
            root -> node1 -> ... -> node2 -> parent

        Args:
            state: The current navigator state

        Raises:
            ValueError: If the path is too long to render, or if the current node has no parent.

        Dependencies:
            NavigatorState
            NavigatorRenderer.measure_or_render_path_with_ellipses: use this function to render the path with ellipses.
        """
        # Check if the current node has a parent
        if not state.current_node.parent:
            raise ValueError("Current node has no parent")

        # Get the path to the parent from the current node's data
        path_to_parent = state.current_node.data.path_to_parent

        # Try to render the full path first (no ellipses needed)
        if self.measure_or_render_path_with_ellipses(path_to_parent, [], Mode.MEASURE):
            # If it fits, render it
            self.measure_or_render_path_with_ellipses(path_to_parent, [], Mode.RENDER)
            return

        # Can't shorten the path if it has only 2 nodes
        if len(path_to_parent) <= 2:
            raise ValueError("Path is too long to render.")

        # Progressively add more nodes to both sides
        max_nodes_per_side = (len(path_to_parent) - 1) // 2

        # Keep track of the last successful configuration
        last_successful_prefix = None
        last_successful_suffix = None

        for i in range(1, max_nodes_per_side + 1):
            # Add one more node to each side
            new_prefix = path_to_parent[: i + 1]
            new_suffix = path_to_parent[-(i + 1) :]

            # Try measuring with the new paths
            if self.measure_or_render_path_with_ellipses(
                new_prefix, new_suffix, Mode.MEASURE
            ):
                # Save this configuration as the last successful one
                last_successful_prefix = new_prefix
                last_successful_suffix = new_suffix
            else:
                # If this configuration doesn't fit, use the last successful one
                break

        # Render the last successful configuration if we found one
        if last_successful_prefix is not None and last_successful_suffix is not None:
            self.measure_or_render_path_with_ellipses(
                last_successful_prefix, last_successful_suffix, Mode.RENDER
            )

    def render_parent(self, state: NavigatorState) -> None:
        """
        @nlmeta

        Render the parent node.

        We should always render the number of non-visible siblings before and after the current node as special "+X more siblings" leafs

        Given two configurations, we should prefer the one that:
        1) Renders the current node as tall as possible.
        2) If that is equal, renders the current node as vertically centered within the screen as possible.
        3) If that is equal, renders as many siblings as possible.
        4) If that is equal, renders siblings as tall as possible (all to the same height).

        Algorithm:
        Run in a loop, decreasing num_siblings
        - For each configuration, try different distributions of siblings before and after the current node.
        - Increase the sibling height until the number of rows used doesn't change, or we fail to render.
        - If height=0 fails, break early (and move to the next num_siblings)
        - If we find a valid configuration, compare it with the best one so far.

        Args:
            state: The current navigator state

        Dependencies:
            RenderConfiguration: class for parent configuration.
            RenderResult: class for rendering result.
            NavigatorRenderer.measure_or_render_siblings: use to try rendering different configurations of siblings.
                See also documentation for how to render the parent.
            NavigatorRenderer.render_connectors: use to render connectors after tree structure has been set.
            NavigatorRenderer.compare_results: use this function to compare configurations.
            NavigatorRenderer.render_parent_path: use this function to render the parent path on the top line.
        """
        # Ensure the current node has a parent
        if not state.current_node.parent:
            raise ValueError("Current node must have a parent")

        # Get terminal dimensions
        max_y, _ = self.stdscr.getmaxyx()

        # Each sibling needs at least 1 row, plus 1 row each for parent, current node, and bottom row
        max_sibling_rows = max(0, max_y - 2)

        # Initialize best result to None
        best_result: RenderResult | None = None
        best_siblings: int | None = None

        # Get the total number of siblings
        total_siblings_available = len(state.current_node.parent.children) - 1

        # Run in a loop, decreasing the number of siblings
        # Start with the calculated maximum (or total available, whichever is smaller)
        max_siblings_to_try = min(max_sibling_rows, total_siblings_available)
        max_height_to_try = state.current_node.parent.data.height

        # Try configurations with decreasing number of siblings
        for total_siblings in range(max_siblings_to_try, -1, -1):

            # Try different distributions of siblings before and after
            for siblings_before in range(total_siblings + 1):
                siblings_after = total_siblings - siblings_before

                # Increase sibling height until no change or failure
                prev_rows_used = -1
                start_height = (
                    1
                    if best_result is None
                    else best_result.configuration.sibling_height
                )
                for sibling_height in range(start_height, max_height_to_try + 1):
                    # Create configuration
                    config = RenderConfiguration.from_node(
                        state.current_node,
                        siblings_before,
                        siblings_after,
                        sibling_height,
                    )

                    # Try rendering this configuration
                    result = self.measure_or_render_siblings(config, mode=Mode.MEASURE)

                    # Current height failed, so don't try to go any higher
                    if result is None:
                        break

                    # If rows used didn't change, no need to try taller
                    if prev_rows_used == result.total_rows_used:
                        break

                    prev_rows_used = result.total_rows_used

                    # If this is our first successful result, or it's better than our current best
                    if (
                        best_result is None
                        or self.compare_results(result, best_result) > 0
                    ):
                        best_result = result
                        best_siblings = total_siblings

            if best_siblings and best_siblings - total_siblings > 2:
                break

        # If we found a valid configuration, render it
        if best_result is not None:
            try:
                # Render the best configuration
                self.measure_or_render_siblings(
                    best_result.configuration, mode=Mode.RENDER
                )

                # Render the parent path
                self.render_parent_path(state)

            except curses.error:
                # Handle potential curses errors (e.g., writing outside terminal boundaries)
                pass

    def render_footer(self) -> None:
        """
        @nlmeta

        Render navigation footer (justify right).

        Dependencies:
            NavigatorState.handle_keypress: this function handles keypresses.
        """
        max_y, max_x = self.stdscr.getmaxyx()
        footer_text = 'arrow keys to navigate, "ESC" or "q" to quit.'

        # Calculate position for right-justified text
        x_pos = max_x - len(footer_text) - 1

        # Truncate if too long
        if x_pos < 0:
            footer_text = footer_text[:x_pos]
            x_pos = 0

        self.stdscr.addstr(max_y - 1, x_pos, footer_text)

    def render(self, state: NavigatorState) -> None:
        """
        @nlmeta

        Render the current state of the navigator.

        Dependencies:
            NavigatorRenderer.render_parent: use this function to render the parent node, if there is one.
            NavigatorRenderer.render_tallest_tree: use this function to render the tallest tree when there is no parent.
            NavigatorRenderer.render_footer: use this function to render the footer.
        """
        # Clear the screen
        self.stdscr.clear()

        if state.current_node.parent:
            self.render_parent(state)
        else:
            self.render_tallest_tree(state.current_node)

        self.render_footer()

        # Refresh the screen to display changes
        self.stdscr.refresh()

        # Hide the cursor
        curses.curs_set(0)


def navigation_loop(stdscr: curses.window, root: Node):
    """
    @nlmeta

    Navigation loop for a node.

    ESC and 'q' keys exit the navigator.

    Dependencies:
        .node.Node: class for tree structure.
        NavigatorState: class for navigator state.
        NavigatorRenderer: class for rendering the navigator.
    """
    state = NavigatorState(root)
    renderer = NavigatorRenderer(stdscr)

    # Main navigation loop
    while True:
        # Render the current state
        renderer.render(state)

        # Get user input
        key_code = renderer.stdscr.getch()

        # Map key code to Key enum
        key = {
            curses.KEY_UP: Key.UP,
            curses.KEY_DOWN: Key.DOWN,
            curses.KEY_LEFT: Key.LEFT,
            curses.KEY_RIGHT: Key.RIGHT,
            27: Key.QUIT,  # ESC key
            ord("q"): Key.QUIT,
        }.get(key_code)

        # Wait for a valid keypress
        if not key:
            continue

        # Handle keypress and get new current node (or None to exit)
        if not state.handle_keypress(key):
            return
