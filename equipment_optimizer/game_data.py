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


def sanitize_package_name(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.strip().lower())


def iterate_lines(value: str) -> Generator[str, None, None]:
    return (
        line.group(0) for line in re.finditer(r"[^\n]*\r?\n|[^\n]+$", value)
    )


@dataclass(frozen=True, eq=False)
class Data:
    numeric_fields: dict[str, float]
    textual_fields: dict[str, str]


@dataclass(frozen=True, eq=False)
class Entry:
    name: str
    data: Data


# A small improvement gain could possibly be had by avoiding csv.DictReader and
# parsing in a way that doesn't include all fields.  This would likely be
# difficult to implement faster too so the gain is mostly theoretical.
#
# Fields are already removed by the "exclude" value, but this is only done to
# use less memory and is applied AFTER the full dict is prepared.
# https://github.com/python/cpython/blob/main/Lib/csv.py#L80
class Reader:
    BUILTIN_GAME_DATA_PACKAGE = f"{__package__}.builtin_game_data"

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
            for field, excluded_values in self.exclude.items():
                if row.get(field, "") in excluded_values:
                    return True
        return False

    def rows(
        self, rows: Iterable[dict[str, str]]
    ) -> Generator[Entry, None, None]:
        for row in rows:
            if self.is_row_excluded(row):
                LOG.debug(f"Skipping excluded row: {repr(row)}")
                continue
            textual_fields: dict[str, str] = {}
            numeric_fields: dict[str, float] = {}
            name = ""
            for key, value in row.items():
                if value:
                    if key == self._name_field:
                        name = value
                    elif self._fields is None or key in self._fields:
                        try:
                            float_value = float(value)
                            if float_value != 0.0:
                                numeric_fields[key] = float_value
                        except ValueError:
                            textual_fields[key] = value
            if not name:
                raise ValueError(f"row requires non-empty name: {repr(row)}")
            yield Entry(
                name=name,
                data=Data(
                    numeric_fields=numeric_fields,
                    textual_fields=textual_fields,
                ),
            )

    def csv_file(
        self, path: Union[str, PathLike[str]]
    ) -> Generator[Entry, None, None]:
        with open(path, mode="r", newline="") as csv_file:
            yield from self.rows(csv.DictReader(csv_file))

    def csv_content(self, content: str) -> Generator[Entry, None, None]:
        yield from self.rows(csv.DictReader(iterate_lines(content)))

    def builtin_game(
        self, game: str, *, data_sets: Optional[set[str]] = None
    ) -> Generator[Entry, None, None]:
        game_package = (
            self.__class__.BUILTIN_GAME_DATA_PACKAGE
            + f".{sanitize_package_name(game)}"
        )
        if data_sets is None:
            data_sets = set()
        for package in itertools.chain(
            (game_package,),
            (
                f"{game_package}.{sanitize_package_name(data_set)}"
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
    ) -> Generator[Entry, None, None]:
        if data_sets is None:
            data_sets = set()
        for data_directory in itertools.chain(
            (Path(path),), (Path(path, data_set) for data_set in data_sets)
        ):
            for data_file in data_directory.iterdir():
                if data_file.suffix.lower() == ".csv":
                    LOG.debug(f"Loading custom game data: {data_file}")
                    yield from self.csv_file(data_file)
