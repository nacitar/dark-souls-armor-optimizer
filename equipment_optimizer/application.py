#!/usr/bin/env python3

# requires 3.9+ (for mypy dict/tuple instead of Dict/Tuple)
from sortedcontainers import SortedDict  # type: ignore
from typing import Optional, Sequence
import logging
import argparse
import sys
from .equipment import EquipmentDatabase

LOG = logging.getLogger(__name__)

# TODO:
#   fix Traveling Gloves in data
#       really, need to get a new data dump because it's missing fields.
#   consider naming of classes/module itself for 'equipment'
#   allow saving the output of by_position


def main(argv: Optional[Sequence[str]] = None) -> int:
    logging.basicConfig(
        style="{",
        format="[{asctime:s}] {levelname:s} {message:s}",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    parser = argparse.ArgumentParser(description="An equipment optimizer.")
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
        "--data-sets",
        type=lambda argument: argument.split(","),
        help="The name of a data set to use in addition to common data.",
    )
    parser.add_argument(
        "-m",
        "--maximize",
        type=lambda argument: argument.split(","),
        required=True,
        help="Fields to maximize in the output.",
    )
    parser.add_argument(
        "--name-field",
        default="name",
        help="The name of the field that holds the name of the piece.",
    )
    parser.add_argument(
        "--position-field",
        default="position",
        help="The name of the field that holds the position of the piece.",
    )
    parser.add_argument(
        "--set-field",
        default="set",
        help="The name of the field that holds the name of the piece's set.",
    )
    parser.add_argument(
        "--exclude-sets",
        type=lambda argument: set(argument.split(",")),
        help="The name of sets to exclude from the data.",
    )
    parser.add_argument(
        "--exclude-pieces",
        type=lambda argument: set(argument.split(",")),
        help="The name of pieces to exclude from the data.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-f",
        "--fields",
        type=lambda argument: argument.split(","),
        help="Fields to include in the output.",
    )
    group.add_argument(
        "-n",
        "--no-fields",
        action="store_true",
        help="Include no fields in the output.",
    )
    args = parser.parse_args(args=argv)
    logging.getLogger().setLevel(args.verbose)

    fields = set(args.maximize)
    if args.fields:
        fields.update(args.fields)

    exclude = {}
    if args.exclude_pieces is not None:
        exclude[args.name_field] = args.exclude_pieces
    if args.exclude_sets is not None:
        exclude[args.set_field] = args.exclude_sets

    equipment = EquipmentDatabase(
        name_field=args.name_field,
        position_field=args.position_field,
        fields=fields,
        exclude=exclude,
    )

    if args.input_directory:
        equipment.import_custom_game(
            args.input_directory, data_sets=args.data_sets
        )
    else:
        equipment.import_builtin_game(game=args.game, data_sets=args.data_sets)

    print(equipment.by_position())
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
