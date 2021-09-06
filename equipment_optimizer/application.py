#!/usr/bin/env python3

# requires 3.9+ (for mypy dict/tuple instead of Dict/Tuple)
from sortedcontainers import SortedDict  # type: ignore
from typing import Optional, Sequence
import logging
import argparse
import sys
from .equipment import Equipment

# from collections.abc import Mapping

LOG = logging.getLogger(__name__)

# TODO:
#   add arguments you want to maximize
#   add arguments for set/name exclusions


def main(argv: Optional[Sequence[str]] = None) -> int:
    logging.basicConfig(
        style="{",
        format="[{asctime:s}] {levelname:s} {message:s}",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
    parser = argparse.ArgumentParser(description="An equipment optimizer.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-g",
        "--game",
        default="Dark Souls",
        help="The name of the built-in game whose data will be used.",
    )
    group.add_argument(
        "-i",
        "--input-directory",
        help="A directory with custom csv files whose data will be used.",
    )
    parser.add_argument(
        "-d",
        "--data-set",
        action="append",
        nargs="?",
        help="The name of a data set to use in addition to common data.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=logging.DEBUG,
        default=logging.INFO,
        help="Increase output verbosity",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-s",
        "--statistic",
        action="append",
        help="Statistics to include in the output.",
    )
    group.add_argument(
        "-n",
        "--no-statistics",
        action="store_true",
        help="Include no statistics in the output.",
    )
    args = parser.parse_args(args=argv)
    if args.no_statistics:
        args.statistic = []
    LOG.setLevel(args.verbose)

    exclude = None
    # exclude = {
    #        "set": set(["Xanthous"]),
    #        "name": set(["Wanderer Manchettes"])
    #    }
    equipment = Equipment(statistics=args.statistic, exclude=exclude)

    if args.input_directory:
        equipment.import_custom_game(
            args.input_directory, data_sets=args.data_set
        )
    else:
        equipment.import_builtin_game(game=args.game, data_sets=args.data_set)

    print(equipment.data)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# The general concept here is that an item is dominated by any other item with
# a higher weight modifier and the same value or better.
obj = SortedDict(
    {
        # higher keys cannot have higher values
        1.0: 5,
        1.25: 3,
        1.5: 2,
    }
)
# TODO: irange?
best = SortedDict()


def test_zomg():
    print("moo")
    assert 1 == 0
