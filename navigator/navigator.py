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

    # Depth of subtree rooted at this node
    # NB: a leaf node has depth 1
    tree_depth: int
    # Number of descendants in the subtree rooted at this node
    descendants: int


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
        self.root: AnnotatedNode = self._annotate_tree(root)
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

        # Initialize tree depth and descendant count
        max_child_depth = 0
        total_descendants = 0

        # Process each child
        for child in node.children:
            # Recursively annotate the child
            annotated_child = self._annotate_tree(child)
            annotated_children.append(annotated_child)

            # Update maximum child depth
            max_child_depth = max(max_child_depth, annotated_child.data.tree_depth)

            # Add child's descendants plus the child itself to total descendants
            total_descendants += annotated_child.data.descendants + 1

        # Calculate tree depth for this node
        tree_depth = max_child_depth + 1

        # Create NodeData for this node
        node_data = NodeData(
            tree_depth=tree_depth,
            descendants=total_descendants,
        )

        # Create the annotated node without setting parent or children yet
        annotated_node = AnnotatedNode(node=node, data=node_data)

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
    sibling_depth: int

    @classmethod
    def from_node(
        cls,
        node: AnnotatedNode,
        visible_siblings_before: int,
        visible_siblings_after: int,
        sibling_depth: int,
    ) -> RenderConfiguration:
        """
        @nlmeta

        Create a RenderConfiguration from a node and parameters about visible siblings.

        Args:
            node: The current node
            visible_siblings_before: Number of siblings to show before the current node
            visible_siblings_after: Number of siblings to show after the current node
            sibling_depth: How deep to render siblings

        Returns:
            A RenderConfiguration object

        Raises:
            AssertionError: If the node has no parent
        """

        # Ensure the node has a parent
        assert node.parent, "Node must have a parent"

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
            sibling_depth=sibling_depth,
        )


@dataclass(frozen=True)
class RenderResult:
    """A rendering result for a given configuration."""

    configuration: RenderConfiguration
    current_node_depth: int
    current_node_position: int
    total_rows_used: int


class NavigatorRenderer:
    """Renderer for the navigator."""

    def __init__(self, stdscr: curses.window, max_children: int = 10):
        self.max_children = max_children
        self.stdscr = stdscr

    def erase_below(self, y: int) -> None:
        """
        @nlmeta

        Erase all lines from the screen below a given y coordinate.
        """
        max_y, _ = self.stdscr.getmaxyx()
        if y >= max_y:
            return

        # Clear each line from y to the bottom of the screen
        for line in range(y, max_y):
            # Move cursor to the beginning of the line
            self.stdscr.move(line, 0)
            # Clear to the end of the line
            self.stdscr.clrtoeol()

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
        i.e., if the node has any children, render "node_name (+X more descendants)"

        Args:
            node: The node to render
            x: X coordinate
            y: Y coordinate
            highlight: Whether to highlight node_name

        Returns:
            True if the node was rendered successfully, False otherwise.

        Dependencies:
            context: NavigatorRenderer.render_tree: uses this function to render the terminal.
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
            descendant_text = f" (+{descendant_count} more descendants)"
        else:
            descendant_text = ""

        # Check if the full text will fit on screen
        if x + len(node_name) + len(descendant_text) >= max_x:
            return False

        # Render the node name with highlighting
        if highlight:
            self.stdscr.attron(curses.A_REVERSE)
            self.stdscr.addstr(y, x, node_name)
            self.stdscr.attroff(curses.A_REVERSE)
        else:
            self.stdscr.addstr(y, x, node_name)

        if descendant_text:
            # Calculate position for descendant text (right after the node name)
            desc_x = x + len(node_name)

            # Add the descendant text without highlighting
            self.stdscr.addstr(y, desc_x, descendant_text)

        return True

    def draw_connectors(self, x: int, ys: list[int], offset: int = 4) -> None:
        """
        @nlmeta

        Draw connectors for children.
        - Because we do not know the size or shape of the tree in advance, the connectors should be drawn after the tree has been rendered.
        - The connector should be "├──── " for all but the last child, and "└──── " for the last child (assuming the default offset of 4; adjust as necessary).

        Example: (drawing connectors for the root w/ node x=0, ys=[0,1,2,3,9], offset=4)
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
            context: NavigatorRenderer.render_tree: uses this function to draw the vertical connectors after the tree structure has been set.
            context: NavigatorRenderer.render_parent: uses this function to draw the vertical connectors after the tree structure has been set.
        """
        if not ys:
            return

        # Get terminal dimensions
        max_y, max_x = self.stdscr.getmaxyx()

        if any(y >= max_y for y in ys):
            raise ValueError("Y coordinates out of bounds")

        if x + offset + 1 >= max_x:
            raise ValueError("X coordinate out of bounds")

        ys = sorted(ys)  # Sort the y coordinates to ensure correct order

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
        try:
            # Clear the screen below the current node before rendering
            self.erase_below(y)

            # If depth is 0 or node has no children, render as terminal
            if depth == 0 or not node.children:
                if self.render_as_terminal(node, x, y):
                    return (1, 0)  # Terminal node takes up 1 row, depth 0
                else:
                    return None  # Failed to render

            # Render the node itself
            node_text = str(node)
            self.stdscr.addstr(y, x, node_text)

            # Calculate position for children
            child_x = x + offset + 1
            current_y = y + 1

            # Track y positions for all children to draw connectors later
            child_ys: list[int] = []

            # Determine how many children to show
            visible_children = min(len(node.children), self.max_children)
            total_rows = 1  # Start with 1 for the node itself

            # Render each child
            max_child_depth = 0
            for i in range(visible_children):
                child = node.children[i]
                child_result = self.render_tree(
                    child, child_x, current_y, depth - 1, offset
                )

                if child_result is None:
                    self.erase_below(y)  # Clean up on failure
                    return None

                child_height, child_depth = child_result  # Unpack the result tuple
                max_child_depth = max(max_child_depth, child_depth)
                child_ys.append(current_y)
                current_y += child_height
                total_rows += child_height

            # If there are more children than max_children, render a placeholder
            if len(node.children) > self.max_children:
                more_children = len(node.children) - self.max_children
                more_text = f"(+{more_children} more children)"

                self.stdscr.addstr(current_y, child_x, more_text)
                child_ys.append(current_y)
                current_y += 1
                total_rows += 1

            # Draw connectors from node to all children
            self.draw_connectors(x, child_ys, offset)

            return (total_rows, max_child_depth + 1)

        except curses.error:
            # Catch all curses errors here
            self.erase_below(y)  # Clean up on failure
            return None

    def render_deepest_tree(
        self,
        node: AnnotatedNode,
        x: int,
        y: int,
        max_rows: int,
        offset: int = 4,
    ) -> tuple[int, int] | None:
        """
        @nlmeta

        Render a node and its children as deeply as possible.

        Algorithm:
        - Attempt to render as tree, starting with child_depth = 0 and increasing.
            - Increment child_depth until either there's no change in the number of lines, or failure.
            - Failure happens when render_tree returns -1 (failure to render) or exceeds max_rows.
        - If failure:
            - If child_depth = 0 fails, return -1.
            - Otherwise, render one last time with child_depth-1 and return the number of rows.
        - If no change in lines, leave the last rendered tree and just return the number of rows used.

        Args:
            state: The current navigator state
            node: The node to render
            x: X coordinate
            y: Y coordinate
            max_rows: Maximum number of rows to use for rendering
            offset: Connector length for rendering children

        Dependencies:
            NavigatorRenderer.render_tree: use this function to render the tree at a given depth.
            NavigatorRenderer.erase_below: used to erase the screen below a given y coordinate upon failure.

        Returns:
            None if the tree cannot be rendered.
            Otherwise, returns a tuple of the number of rows used and the depth of the tree rendered.
        """
        # Start with depth 0
        child_depth = 0
        prev_rows = -1

        # Incrementally increase depth until we see no change in rows or encounter failure
        while True:
            # Try rendering at the current depth
            result = self.render_tree(node, x, y, child_depth, offset)

            # If rendering failed or exceeds max_rows, go back to the last successful depth
            if result is None or (current_rows := result[0]) > max_rows:
                # Erase the failed rendering
                self.erase_below(y)

                # If we failed at depth 0, return None
                if child_depth == 0:
                    return None

                # Render one last time with the last successful depth
                final_rows = self.render_tree(node, x, y, child_depth - 1, offset)
                assert final_rows is not None
                return (final_rows[0], child_depth - 1)

            # If the number of rows didn't change, we've reached maximum useful depth
            # Leave the last rendered tree and return the number of rows used
            if current_rows == prev_rows:
                return (current_rows, child_depth)

            # Update tracking variables
            prev_rows = current_rows

            # Increment depth for next iteration
            child_depth += 1

    def render_siblings(
        self, configuration: RenderConfiguration
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
            - sibling_depth = 1

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
            If successful, a RenderResult object containing the configuration, current node depth, and position.
            Else, return None.

        Dependencies:
            RenderConfiguration: class for parent configuration.
            RenderResult: class for rendering result.
            NavigatorRenderer.render_tree: use this function to render siblings at a given depth.
            NavigatorRenderer.render_deepest_tree: use this function to render the current node as deeply as possible.
                use max_rows to leave space for non-visible siblings placeholder.
            context: NavigatorRenderer.render_parent: calls this function to search for a valid rendering configuration.
        """
        try:
            # Get terminal dimensions
            max_y, _ = self.stdscr.getmaxyx()
            max_y -= 1  # Leave space for the bottom line

            # Offset for children
            offset = 4
            child_x = offset + 1

            # Track y positions for all children to draw connectors later
            child_ys: list[int] = []
            current_y = 1

            # Render non-visible siblings before if any
            if configuration.non_visible_siblings_before > 0:
                more_text = (
                    f"(+{configuration.non_visible_siblings_before} more siblings)"
                )
                self.stdscr.addstr(current_y, child_x, more_text)
                child_ys.append(current_y)
                current_y += 1

            # Render visible siblings before
            for sibling in configuration.siblings_before:
                sibling_result = self.render_tree(
                    sibling, child_x, current_y, configuration.sibling_depth, offset
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

            # Use render_deepest_tree for the current node
            current_node_result = self.render_deepest_tree(
                configuration.current_node,
                child_x,
                current_y,
                max_rows_for_current,
                offset,
            )
            if current_node_result is None:
                return None

            # Unpack the result tuple - rows and depth
            current_node_height, current_node_depth = current_node_result

            child_ys.append(current_node_y)
            current_y += current_node_height

            # Render visible siblings after
            for sibling in configuration.siblings_after:
                sibling_result = self.render_tree(
                    sibling, child_x, current_y, configuration.sibling_depth, offset
                )
                if sibling_result is None:
                    return None

                # Unpack the result tuple - only need the height
                sibling_height, _ = sibling_result

                child_ys.append(current_y)
                current_y += sibling_height

            # Render non-visible siblings after if any
            if configuration.non_visible_siblings_after > 0:
                more_text = (
                    f"(+{configuration.non_visible_siblings_after} more siblings)"
                )
                self.stdscr.addstr(current_y, child_x, more_text)
                child_ys.append(current_y)
                current_y += 1

            # Draw connectors from parent to all children
            self.draw_connectors(0, child_ys, offset)

            # Overwrite and highlight the current node
            self.stdscr.attron(curses.A_REVERSE)
            self.stdscr.addstr(current_node_y, child_x, str(configuration.current_node))
            self.stdscr.attroff(curses.A_REVERSE)

            # Create and return the RenderResult
            return RenderResult(
                configuration=configuration,
                current_node_depth=current_node_depth,
                current_node_position=current_node_y,
                total_rows_used=current_y - 1,
            )

        except curses.error:
            # Catch all curses errors here
            return None

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
        # 1. Compare current node depth - prefer deeper rendering
        if result1.current_node_depth > result2.current_node_depth:
            return 1
        elif result1.current_node_depth < result2.current_node_depth:
            return -1

        # 2. If sibling depths are equal, compare how vertically centered the current node is
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

        # 3. If depths are equal, compare total number of visible siblings
        config1 = result1.configuration
        config2 = result2.configuration

        siblings1 = len(config1.siblings_before) + len(config1.siblings_after)
        siblings2 = len(config2.siblings_before) + len(config2.siblings_after)

        if siblings1 > siblings2:
            return 1
        elif siblings1 < siblings2:
            return -1

        # 4. If sibling counts are equal, compare sibling depth
        if config1.sibling_depth > config2.sibling_depth:
            return 1
        elif config1.sibling_depth < config2.sibling_depth:
            return -1

        # If all criteria are equal, the configurations are equivalent
        return 0

    def render_parent(self, state: NavigatorState) -> None:
        """
        @nlmeta

        Render the parent node.

        We should always render the number of non-visible siblings before and after the current node as special "+X more siblings" leafs

        Given two configurations, we should prefer the one that:
        1) Renders the current node as deeply as possible.
        2) If that is equal, renders the current node as vertically centered within the screen as possible.
        3) If that is equal, renders as many siblings as possible.
        4) If that is equal, renders siblings as deeply as possible (all to the same depth).

        Algorithm:
        Run in a loop, decreasing num_siblings
        - For each configuration, try different distributions of siblings before and after the current node.
        - Increase the sibling depth until the number of rows used doesn't change, or we fail to render.
        - If depth=0 fails, break early (and move to the next num_siblings)
        - If we find a valid configuration, compare it with the best one so far.

        Args:
            state: The current navigator state

        Dependencies:
            RenderConfiguration: class for parent configuration.
            RenderResult: class for rendering result.
            NavigatorRenderer.render_siblings: use to try rendering different configurations of siblings.
                See also documentation for how to render the parent.
            NavigatorRenderer.draw_connectors: use to draw connectors after tree structure has been set.
            NavigatorRenderer.erase_below: use to erase the screen below a given y coordinate.
            NavigatorRenderer.compare_results: use this function to compare configurations.
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

        # Get the total number of siblings
        total_siblings_available = len(state.current_node.parent.children) - 1

        # Run in a loop, decreasing the number of siblings
        # Start with the calculated maximum (or total available, whichever is smaller)
        max_siblings_to_try = min(max_sibling_rows, total_siblings_available)
        max_depth_to_try = state.current_node.parent.data.tree_depth

        # Try configurations with decreasing number of siblings
        for total_siblings in range(max_siblings_to_try, -1, -1):

            # Try different distributions of siblings before and after
            for siblings_before in range(total_siblings + 1):
                siblings_after = total_siblings - siblings_before

                # Increase sibling depth until no change or failure
                prev_rows_used = -1
                start_depth = (
                    1
                    if best_result is None
                    else best_result.configuration.sibling_depth
                )
                for sibling_depth in range(start_depth, max_depth_to_try + 1):
                    # Create configuration
                    config = RenderConfiguration.from_node(
                        state.current_node,
                        siblings_before,
                        siblings_after,
                        sibling_depth,
                    )

                    # Try rendering this configuration
                    result = self.render_siblings(config)

                    # Current depth failed, so don't try to go any deeper
                    if result is None:
                        break

                    # If rows used didn't change, no need to try deeper
                    if prev_rows_used == result.total_rows_used:
                        break

                    prev_rows_used = result.total_rows_used

                    # If this is our first successful result, or it's better than our current best
                    if (
                        best_result is None
                        or self.compare_results(result, best_result) > 0
                    ):
                        best_result = result

        # If we found a valid configuration, render it
        if best_result is not None:
            try:
                # Clear the screen below the parent node
                self.erase_below(0)

                # Render the best configuration
                self.render_siblings(best_result.configuration)

                # Render the parent node
                parent_text = str(state.current_node.parent)

                self.stdscr.addstr(0, 0, parent_text)

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
            NavigatorRenderer.render_parent: use this function to render the parent node.
            NavigatorRenderer.render_deepest_tree: use this function to render the tree when there is not parent.
                Remember to add highlighting for the current node in this case.
            NavigatorRenderer.render_footer: use this function to render the footer.
        """
        # Clear the screen
        self.stdscr.clear()

        if state.current_node.parent:
            # Render the parent node
            self.render_parent(state)
        else:
            y, _ = self.stdscr.getmaxyx()
            # Render the current node directly
            self.render_deepest_tree(state.current_node, 0, 0, y - 1)

            # Overwrite and highlight the current node
            self.stdscr.attron(curses.A_REVERSE)
            self.stdscr.addstr(0, 0, str(state.current_node))
            self.stdscr.attroff(curses.A_REVERSE)

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
