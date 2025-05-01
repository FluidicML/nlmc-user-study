"""Test cases for the user study."""

from __future__ import annotations

import random

from .node import Node
from .node import NodeStatus


def get_random_status() -> NodeStatus:
    """
    Return a random NodeStatus value.
    """
    return random.choice(list(NodeStatus))


def get_random_active() -> bool:
    """
    Return a random active state (True or False) with a higher probability of True.
    Using a 70% chance of being active to avoid too many inactive nodes.
    """
    return random.random() < 0.7  # 70% chance of being active


def make_tree(size: int, seed: int) -> Node:
    """
    Create a random tree of a given size.
    """
    if size <= 0:
        raise ValueError("Tree size must be positive")

    # Set random seed for reproducibility
    random.seed(seed)

    # Create the root node with a random status and active state
    # Making the root always active to ensure at least some nodes are reachable
    root = Node(name="0", status=get_random_status(), active=True)

    # List to keep track of all nodes for random parent selection
    nodes: list[Node] = [root]

    # Create remaining nodes
    for i in range(1, size):
        # Randomly select a parent from existing nodes
        parent = random.choice(nodes)

        # Create a new node with the selected parent, random status and active state
        new_node = Node(
            name=str(i),
            parent=parent,
            status=get_random_status(),
            active=get_random_active(),
        )

        # Add the new node as a child to the parent
        parent.add_child(new_node)

        # Add the new node to our list of nodes
        nodes.append(new_node)

    return root


def make_deep_tree(depth: int) -> Node:
    """
    Create a deep tree (a single linear chain) with the specified depth.
    Each node has exactly one child, creating a straight line from root to leaf.
    """
    if depth <= 0:
        raise ValueError("Tree depth must be positive")

    # Create the root node with a random status
    # Making the root always active to ensure at least some nodes are reachable
    root = Node(name="root", status=get_random_status(), active=True)
    current_node = root

    # Create a linear chain of nodes
    for i in range(1, depth):
        new_node = Node(
            name=f"level_{i}", status=get_random_status(), active=get_random_active()
        )
        current_node.add_child(new_node)
        current_node = new_node

    return root


def make_wide_tree(width: int) -> Node:
    """
    Create a wide tree where a single parent (root) has many children.
    The tree has a minimal depth (just root and its children).
    """
    if width <= 0:
        raise ValueError("Tree width must be positive")

    # Create the root node with a random status
    # Making the root always active to ensure at least some nodes are reachable
    root = Node(name="root", status=get_random_status(), active=True)

    # Add children directly to the root with random statuses and active states
    for i in range(width):
        child = Node(
            name=f"child_{i}", status=get_random_status(), active=get_random_active()
        )
        root.add_child(child)

    return root


def create_test_cases() -> dict[int, Node]:
    """
    Create test cases for the user study.
    """
    return {
        # Original random trees
        1: make_tree(5, 1),
        2: make_tree(10, 1),
        3: make_tree(20, 1),
        4: make_tree(40, 1),
        5: make_tree(80, 1),
        6: make_tree(500, 1),
        7: make_tree(500, 2),
        8: make_tree(500, 3),
        # Deep trees (linear chain)
        9: make_deep_tree(10),  # Deep tree with 10 levels
        10: make_deep_tree(50),  # Deep tree with 50 levels
        11: make_deep_tree(100),  # Deep tree with 100 levels
        # Wide trees (many children)
        12: make_wide_tree(10),  # Wide tree with 10 children
        13: make_wide_tree(50),  # Wide tree with 50 children
        14: make_wide_tree(100),  # Wide tree with 100 children
    }


TESTCASES = create_test_cases()
