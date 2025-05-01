"""Node class for tree structure."""

from __future__ import annotations

from enum import Enum


class NodeStatus(Enum):
    """Status of a node."""

    WORKING = "working"
    PENDING_CHANGES = "pending changes"
    NO_CHANGES = "no changes"
    NOT_CHECKED = "not checked"


class Node:
    """A simple node class for demonstration purposes."""

    def __init__(
        self,
        name: str,
        parent: Node | None = None,
        status: NodeStatus = NodeStatus.NOT_CHECKED,
    ):
        self.name = name
        self.parent = parent
        self.children: list[Node] = []
        self.status = status

    def add_child(self, child: Node):
        """
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
