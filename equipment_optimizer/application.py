# requires 3.9+ (for mypy dict/tuple instead of Dict/Tuple)
from sortedcontainers import SortedDict  # type: ignore
from typing import Optional, Sequence
import logging
import argparse
import re
from . import game_data

LOG = logging.getLogger(__name__)

# TODO:
#   fix Traveling Gloves in data
#       really, need to get a new data dump because it's missing fields.
# - mypy doesn't deduce the type of argparse arguments

# comma delimited list with leading and trailing whitespace removed
_LIST_PATTERN = re.compile(r"(?:^|,)\s*([^,]*[^,\s])\s*")


def _argument_to_list(argument: str) -> list[str]:
    return re.findall(_LIST_PATTERN, argument)


def _argument_to_set(argument: str) -> set[str]:
    return set(_argument_to_list(argument))


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
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "-g",
        "--game",
        default="Dark Souls",
        help="The name of the built-in game whose data will be used.",
    )
    input_group.add_argument(
        "-i",
        "--input-directory",
        help="A directory with custom csv files whose data will be used.",
    )
    parser.add_argument(
        "-d",
        "--data-sets",
        type=_argument_to_set,
        help="The name of a data set to use in addition to common data.",
    )
    parser.add_argument(
        "-m",
        "--maximize",
        type=_argument_to_list,
        required=True,
        help="Fields to maximize in the output.",
    )
    parser.add_argument(
        "--name-field",
        default="name",
        help="The name of the field holding the name of the piece.",
    )
    parser.add_argument(
        "--position-field",
        default="position",
        help="The name of the field holding the position of the piece.",
    )
    parser.add_argument(
        "--weight-field",
        default="weight",
        help="The name of the field holding the weight of the piece.",
    )
    parser.add_argument(
        "--weight-modifier-field",
        default="weight_modifier",
        help="The name of the field holding the weight modifier of the piece.",
    )
    parser.add_argument(
        "--set-field",
        default="set",
        help="The name of the field holding the name of the piece's set.",
    )
    parser.add_argument(
        "--exclude-sets",
        type=_argument_to_set,
        help="The name of sets to exclude from the data.",
    )
    parser.add_argument(
        "--exclude-pieces",
        type=_argument_to_set,
        help="The name of pieces to exclude from the data.",
    )
    field_group = parser.add_mutually_exclusive_group()
    field_group.add_argument(
        "-f",
        "--fields",
        type=_argument_to_set,
        help="Fields to include in the output.",
    )
    field_group.add_argument(
        "-n",
        "--no-fields",
        action="store_true",
        help="Include no fields in the output.",
    )
    args = parser.parse_args(args=argv)
    logging.getLogger().setLevel(args.verbose)

    if args.fields:
        args.fields.update(args.maximize)
        args.fields.add(args.position_field)
        args.fields.add(args.weight_field)
        args.fields.add(args.weight_modifier_field)

    exclude_textual_field_values = {}
    if args.exclude_pieces is not None:
        exclude_textual_field_values[args.name_field] = args.exclude_pieces
    if args.exclude_sets is not None:
        exclude_textual_field_values[args.set_field] = args.exclude_sets

    game_data_reader = game_data.Reader(
        name_field=args.name_field,
        fields=args.fields,
        exclude_textual_field_values=exclude_textual_field_values,
    )

    if args.input_directory:
        game_data_generator = game_data_reader.custom_game(
            args.input_directory, data_sets=args.data_sets
        )
    else:
        game_data_generator = game_data_reader.builtin_game(
            game=args.game, data_sets=args.data_sets
        )

    equipment_database: dict[str, game_data.Data] = {}
    by_position: dict[str, set[str]] = {}
    for entry in game_data_generator:
        if entry.name in equipment_database:
            LOG.warning(f"Replacing existing piece of equipment: {entry.name}")
        equipment_database[entry.name] = entry.data
        position = entry.data.textual_fields.get(args.position_field)
        if position:
            by_position.setdefault(position, set()).add(entry.name)
    print(by_position)
    return 0


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
