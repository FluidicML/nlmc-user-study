"""Test cases for the user study."""

from __future__ import annotations

import random

from .node import Node
from .node import NodeStatus


def make_tree(size: int, seed: int) -> Node:
    """
    Create a random tree of a given size.
    """
    if size <= 0:
        raise ValueError("Tree size must be positive")

    # Set random seed for reproducibility
    random.seed(seed)

    # Create the root node
    root = Node(
        name="0",
        status=random.choice(list(NodeStatus)),
        active=random.choices([True, False], [0.8, 0.2])[0],
    )

    # List to keep track of all nodes for random parent selection
    nodes: list[Node] = [root]

    # Create remaining nodes
    for i in range(1, size):
        # Randomly select a parent from existing nodes
        parent = random.choice(nodes)

        # Create a new node with the selected parent
        new_node = Node(
            name=str(i),
            status=random.choice(list(NodeStatus)),
            active=random.choices([True, False], [0.8, 0.2])[0],
            parent=parent,
        )

        # Add the new node as a child to the parent
        parent.add_child(new_node)

        # Add the new node to our list of nodes
        nodes.append(new_node)

    return root


def make_deep_tree(size: int, seed: int) -> Node:
    """
    Create a deep tree of a given size.
    """
    if size <= 0:
        raise ValueError("Tree size must be positive")

    # Set random seed for reproducibility
    random.seed(seed)

    # Create the root node
    root = Node(
        name="0",
        status=random.choice(list(NodeStatus)),
        active=random.choices([True, False], [0.8, 0.2])[0],
    )

    # Keep track of the current node to add children to
    current_node: Node = root

    # Create remaining nodes in a chain
    for i in range(1, size):
        # Create a new node as a child of the current node
        new_node = Node(
            name=str(i),
            status=random.choice(list(NodeStatus)),
            active=random.choices([True, False], [0.8, 0.2])[0],
            parent=current_node,
        )

        # Add the new node as a child to the current node
        current_node.add_child(new_node)

        # Update current_node to be the new node for the next iteration
        current_node = new_node

    return root


def make_wide_tree(size: int, seed: int) -> Node:
    """
    Create a wide tree of a given size.
    """
    if size <= 0:
        raise ValueError("Tree size must be positive")

    # Set random seed for reproducibility
    random.seed(seed)

    # Create the root node
    root = Node(
        name="0",
        status=random.choice(list(NodeStatus)),
        active=random.choices([True, False], [0.8, 0.2])[0],
    )

    # Create remaining nodes as direct children of the root
    for i in range(1, size):
        # Create a new node with the root as parent
        new_node = Node(
            name=str(i),
            status=random.choice(list(NodeStatus)),
            active=random.choices([True, False], [0.8, 0.2])[0],
            parent=root,
        )

        # Add the new node as a child to the root
        root.add_child(new_node)

    return root


def create_test_cases() -> dict[int, Node]:
    """
    Create test cases for the user study.
    """
    return {
        # Random tree test cases
        1: make_tree(5, 1),
        2: make_tree(10, 1),
        3: make_tree(20, 1),
        4: make_tree(40, 1),
        5: make_tree(80, 1),
        6: make_tree(500, 1),
        7: make_tree(500, 2),
        8: make_tree(500, 3),
        # Deep tree test cases
        9: make_deep_tree(50, 1),
        10: make_deep_tree(100, 1),
        11: make_deep_tree(200, 1),
        12: make_deep_tree(500, 1),
        # Wide tree test cases
        13: make_wide_tree(50, 1),
        14: make_wide_tree(100, 1),
        15: make_wide_tree(200, 1),
        16: make_wide_tree(500, 1),
    }


TESTCASES = create_test_cases()
