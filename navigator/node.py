"""Node class for tree structure."""

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
        active: bool,
        parent: Node | None = None,
    ):
        self.name = name
        self.status = status
        self.parent = parent
        self.active = active
        self.children: list[Node] = []

    def add_child(self, child: Node):
        """
        @nlmeta

        Add a child node.
        """
        # Make sure the child doesn't already belong to another parent
        if child.parent is not None and child.parent is not self:
            raise ValueError("Child already has a parent")

        # Add the child to this node's children list
        self.children.append(child)

        # Update the child's parent reference
        child.parent = self

    def __repr__(self):
        return f"Node({self.name})"
