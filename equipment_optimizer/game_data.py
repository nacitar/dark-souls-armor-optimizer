import importlib.resources
import pkgutil
import itertools
import logging
from typing import Optional, Generator, Union, Iterable, cast
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


# Supports reading dicts of strings and floats.  Any other type, including int
# is not supported and an exception will be thrown when encountered.
# Ultimately, float values are the most compatible for the problem space and
# are necessary for many games.  The input formats supported do not need to be
# vast and general, and imposing these requirements adds much simplicity
# provided that enough validations are performed that users are informed when
# they provide invalid data.
class Reader:
    BUILTIN_GAME_DATA_PACKAGE = f"{__package__}.builtin_game_data"

    def __init__(
        self,
        *,
        name_field: str = "name",
        fields: Optional[set[str]] = None,
        exclude_numeric_field_values: Optional[dict[str, set[float]]] = None,
        exclude_textual_field_values: Optional[dict[str, set[str]]] = None,
    ):
        self._name_field = name_field
        self._fields: Optional[set[str]] = None  # get all of them
        if fields is not None:
            self._fields = set(fields)
            self._fields.add(self._name_field)
        self.exclude_numeric_field_values = exclude_numeric_field_values
        self.exclude_textual_field_values = exclude_textual_field_values

    def is_row_excluded(self, row: dict[str, Union[str, float]]) -> bool:
        for exclude_field_values, expected_value_type in (
            (self.exclude_numeric_field_values, float),
            (self.exclude_textual_field_values, str),
        ):
            if exclude_field_values:
                for field, excluded_values in exclude_field_values.items():
                    value = row.get(field)
                    if isinstance(value, expected_value_type):
                        if value in excluded_values:
                            return True
                    else:
                        raise TypeError(
                            "field with exclusions has unexpected type:"
                            f" {repr(field)} is of type {type(value)}"
                            f" but is expected to be {expected_value_type}"
                        )
        return False

    def rows(self, rows: Iterable[dict[str, Union[str, float]]]):
        for row in rows:
            if self.is_row_excluded(row):
                LOG.debug(f"Skipping excluded row: {repr(row)}")
                continue
            name = ""
            textual_fields: dict[str, str] = {}
            numeric_fields: dict[str, float] = {}
            for field in self._fields if self._fields else row.keys():
                value = row.get(field)
                if value:
                    if field == self._name_field:
                        if isinstance(value, str):
                            name = value
                        else:
                            raise TypeError(
                                f"name field is not a str: {value}"
                            )
                    elif isinstance(value, float):
                        numeric_fields[field] = value
                    elif isinstance(value, str):
                        textual_fields[field] = value
                    else:
                        raise TypeError(
                            "field has invalid value type: "
                            f" {repr(field)} is of type {type(value)}"
                        )
            if not name:
                raise ValueError(f"row has empty or missing name: {repr(row)}")
            yield Entry(
                name=name,
                data=Data(
                    numeric_fields=numeric_fields,
                    textual_fields=textual_fields,
                ),
            )

    @staticmethod
    def _csv_dict_reader(
        lines: Iterable[str],
    ) -> Iterable[dict[str, Union[str, float]]]:
        # csv.QUOTE_NONNUMERIC means that the dicts returned can have both str
        # and float values, however the type hints wrongly only allow for str
        # values.  Casting to correct the type hint for the intended usage.
        return cast(
            Iterable[dict[str, Union[str, float]]],
            csv.DictReader(lines, quoting=csv.QUOTE_NONNUMERIC),
        )

    def csv_file(
        self, path: Union[str, PathLike[str]]
    ) -> Generator[Entry, None, None]:
        with open(path, mode="r", newline="") as csv_file:
            yield from self.rows(Reader._csv_dict_reader(csv_file))

    def csv_content(self, content: str) -> Generator[Entry, None, None]:
        yield from self.rows(Reader._csv_dict_reader(iterate_lines(content)))

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
