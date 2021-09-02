#!/usr/bin/env python3

# requires 3.9+ (for mypy dict/tuple instead of Dict/Tuple)
from sortedcontainers import SortedDict  # type: ignore
from typing import Iterable, Optional, Sequence, Union
from pathlib import Path
from os import PathLike
import csv
import logging
import argparse
import sys
from . import game_data

# from collections.abc import Mapping

LOG = logging.getLogger(__name__)

# TODO:
#   add arguments you want to maximize
#   add set exclusions or something more general
#   get this committed!


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

    equipment = Equipment(statistics=args.statistic)

    if args.input_directory:
        equipment.add_custom_game(args.input_directory, data_sets=args.data_set)
    else:
        equipment.add_builtin_game(game=args.game, data_sets=args.data_set)

    print(equipment.data)
    return 0


class Equipment(object):
    def __init__(
        self,
        *,
        statistics: Optional[Iterable[str]] = None,
        position_key: str = "position",
        name_key: str = "name",
    ):
        # position => name => statistics => nonzero float value
        self.data: dict[str, dict[str, dict[str, float]]] = {}
        # None means to get all of them
        self._statistics = list(statistics) if statistics is not None else None
        self._position_key = position_key
        self._name_key = name_key

    # TODO: set exclusions
    # - is it a whitelist or a blacklist?
    # - probably a blacklist.
    def add(self, piece: dict[str, str]) -> None:
        section = self.data.setdefault(str(piece[self._position_key]), {})
        section[str(piece[self._name_key])] = {
            statistic: nonzero_float
            for statistic, value in piece.items()
            if (
                statistic not in (self._position_key, self._name_key)
                and (self._statistics is None or statistic in self._statistics)
                and bool(
                    nonzero_float := game_data.to_float(value, default=0.0)
                )
            )
        }

    def update(self, pieces: Iterable[dict[str, str]]) -> None:
        for piece in pieces:
            self.add(piece)

    def add_csv(
        self,
        path: Optional[Union[str, PathLike[str]]] = None,
        content: Optional[str] = None,
    ) -> None:
        if path is not None:
            with open(path, mode="r", newline="") as handle:
                self.update(pieces=csv.DictReader(handle))
        elif content is None:
            raise TypeError("Must specify path and/or content.")
        if content is not None:

            self.update(pieces=csv.DictReader(game_data.iterlines(content)))

    def add_builtin_game(
        self, game: str, *, data_sets: Optional[list[str]] = None
    ):
        for path in game_data.get_csv_files(
            game, data_sets=data_sets, is_resource=True
        ):
            self.add_csv(content=game_data.get_resource_content(path))

    def add_custom_game(
        self,
        path: Union[str, PathLike[str]],
        *,
        data_sets: Optional[Iterable[str]] = None,
    ) -> None:
        for path in game_data.get_csv_files(path, data_sets=data_sets):
            self.add_csv(path=path)


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
