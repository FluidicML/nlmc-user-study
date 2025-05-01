"""CLI for terminal-based graph navigation."""

import argparse
from curses import wrapper

from .navigator import navigation_loop
from .tests import TESTCASES


def parse_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="User Study CLI")
    parser.add_argument(
        "graph",
        type=int,
        choices=range(1, 15),
        help="Select a graph to visualize",
    )
    return parser.parse_args()


def main():
    """Main entrypoint for the CLI."""
    args = parse_args()
    testcase = TESTCASES.get(args.graph)
    assert testcase

    wrapper(navigation_loop, testcase)
