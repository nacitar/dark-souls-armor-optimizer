import importlib.resources
import pkgutil
import itertools
import logging
from typing import Optional, Generator, Union, Iterable
from pathlib import Path
from os import PathLike
import re
import json
import csv
from dataclasses import dataclass


LOG = logging.getLogger(__name__)


def _as_package(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower())


def _iterate_lines(value: str) -> Generator[str, None, None]:
    return (
        line.group(0) for line in re.finditer(r"[^\n]*\r?\n|[^\n]+$", value)
    )


@dataclass(frozen=True)
class PieceData(object):
    statistics: dict[str, float]
    attributes: dict[str, str]


class PieceReader(object):
    def __init__(
        self,
        *,
        name_field: str = "name",
        fields: Optional[set[str]] = None,
        exclude: Optional[dict[str, set[str]]] = None,
    ):
        self._name_field = name_field
        self._fields: Optional[set[str]] = None  # get all of them
        if fields is not None:
            self._fields = set(fields)
            self._fields.add(self._name_field)
        self.exclude = exclude

    def is_row_excluded(self, row: dict[str, str]) -> bool:
        if self.exclude:
            for attribute, excluded_values in self.exclude.items():
                if row.get(attribute, "") in excluded_values:
                    return True
        return False

    def rows(
        self, rows: Iterable[dict[str, str]]
    ) -> Generator[tuple[str, PieceData], None, None]:
        for row in rows:
            if self.is_row_excluded(row):
                LOG.debug(f"Skipping excluded piece of equipment: {repr(row)}")
                continue
            attributes: dict[str, str] = {}
            statistics: dict[str, float] = {}
            name = ""
            for key, value in row.items():
                if value:
                    if key == self._name_field:
                        name = value
                    elif self._fields is None or key in self._fields:
                        try:
                            float_value = float(value)
                            if float_value != 0.0:
                                statistics[key] = float_value
                        except ValueError:
                            attributes[key] = value
            if not name:
                raise ValueError(f"row requires non-empty name: {repr(row)}")
            yield (
                name,
                PieceData(statistics=statistics, attributes=attributes),
            )

    def csv_file(
        self,
        path: Union[str, PathLike[str]],
    ) -> Generator[tuple[str, PieceData], None, None]:
        with open(path, mode="r", newline="") as csv_file:
            yield from self.rows(csv.DictReader(csv_file))

    def csv_content(
        self,
        content: str,
    ) -> Generator[tuple[str, PieceData], None, None]:
        yield from self.rows(csv.DictReader(_iterate_lines(content)))

    def builtin_game(
        self, game: str, *, data_sets: Optional[set[str]] = None
    ) -> Generator[tuple[str, PieceData], None, None]:
        game_package = f"{__package__}.builtin_game_data.{_as_package(game)}"
        if data_sets is None:
            data_sets = set()
        for package in itertools.chain(
            (game_package,),
            (
                f"{game_package}.{_as_package(data_set)}"
                for data_set in data_sets
            ),
        ):
            for filename in importlib.resources.contents(package):
                if Path(filename).suffix.lower() == ".csv":
                    LOG.debug(
                        f"Loading builtin game data: {package} {filename}"
                    )
                    data = pkgutil.get_data(package, filename)
                    if data is not None:
                        yield from self.csv_content(
                            data.decode(json.detect_encoding(data))
                        )

    def custom_game(
        self,
        path: Union[str, PathLike[str]],
        *,
        data_sets: Optional[set[str]] = None,
    ) -> Generator[tuple[str, PieceData], None, None]:
        if data_sets is None:
            data_sets = set()
        for data_directory in itertools.chain(
            (Path(path),), (Path(path, data_set) for data_set in data_sets)
        ):
            for data_file in data_directory.iterdir():
                if data_file.suffix.lower() == ".csv":
                    LOG.debug(f"Loading custom game data: {data_file}")
                    yield from self.csv_file(data_file)
