"""Test cases for the user study."""

from __future__ import annotations

import random

from .node import Node


def make_tree(size: int, seed: int) -> Node:
    """
    Create a random tree of a given size.
    """
    if size <= 0:
        raise ValueError("Tree size must be positive")

    # Set random seed for reproducibility
    random.seed(seed)

    # Create the root node
    root = Node(name="0")

    # List to keep track of all nodes for random parent selection
    nodes: list[Node] = [root]

    # Create remaining nodes
    for i in range(1, size):
        # Randomly select a parent from existing nodes
        parent = random.choice(nodes)

        # Create a new node with the selected parent
        new_node = Node(name=str(i), parent=parent)

        # Add the new node as a child to the parent
        parent.add_child(new_node)

        # Add the new node to our list of nodes
        nodes.append(new_node)

    return root


def create_test_cases() -> dict[int, Node]:
    """
    Create test cases for the user study.
    """
    return {
        1: make_tree(5, 1),
        2: make_tree(10, 1),
        3: make_tree(20, 1),
        4: make_tree(40, 1),
        5: make_tree(80, 1),
        6: make_tree(500, 1),
        7: make_tree(500, 2),
        8: make_tree(500, 3),
    }


TESTCASES = create_test_cases()
