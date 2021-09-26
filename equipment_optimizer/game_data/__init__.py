import importlib.resources
import pkgutil
import itertools
import logging
from typing import Optional, Generator, Union
from pathlib import Path
from os import PathLike
import re
import json
import csv

LOG = logging.getLogger(__name__)


def as_package_name(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower())


def iterate_lines(value: str) -> Generator[str, None, None]:
    return (
        line.group(0) for line in re.finditer(r"[^\n]*\r?\n|[^\n]+$", value)
    )


class PieceData(object):
    def __init__(
        self, *, attributes: dict[str, str], statistics: dict[str, float]
    ):
        self.attributes: dict[str, str] = attributes
        self.statistics: dict[str, float] = statistics

    def get_statistic(self, statistic: str) -> float:
        return self.statistics.get(statistic, 0.0)

    def get_attribute(self, attribute: str) -> str:
        return self.attributes.get(attribute, "")

    def __repr__(self) -> str:
        return repr(
            {"attributes": self.attributes, "statistics": self.statistics}
        )


class EquipmentCollection(object):
    def __init__(
        self,
        *,
        name_field: str = "name",
        fields: Optional[set[str]] = None,
        exclude: Optional[dict[str, set[str]]] = None,
    ):
        self.pieces: dict[str, PieceData] = {}
        self._name_field = name_field
        self._fields: Optional[set[str]] = None  # get all of them
        if fields is not None:
            self._fields = set(fields)
            self._fields.add(self._name_field)
        self._exclude = exclude

    def is_row_excluded(self, row: dict[str, str]) -> bool:
        if self._exclude:
            for attribute, value in self._exclude.items():
                if row.get(attribute, "") in value:
                    return True
        return False

    def process_row(self, row: dict[str, str]) -> None:
        if self.is_row_excluded(row):
            LOG.debug(f"Skipping excluded piece of equipment: {repr(row)}")
        else:
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
            if name in self.pieces:
                LOG.warning(f"Replacing existing piece of equipment: {name}")
            self.pieces[name] = PieceData(
                attributes=attributes, statistics=statistics
            )

    def process_csv(
        self,
        path: Optional[Union[str, PathLike[str]]] = None,
        content: Optional[str] = None,
    ) -> None:
        if path is not None:
            with open(path, mode="r", newline="") as csv_file:
                for row in csv.DictReader(csv_file):
                    self.process_row(row)
        if content is not None:
            for row in csv.DictReader(iterate_lines(content)):
                self.process_row(row)

    def process_builtin_game(
        self, game: str, *, data_sets: Optional[set[str]] = None
    ) -> None:
        game_package = f"{__name__}.{as_package_name(game)}"
        if data_sets is None:
            data_sets = set()
        for package in itertools.chain(
            (game_package,),
            (
                f"{game_package}.{as_package_name(data_set)}"
                for data_set in data_sets
            ),
        ):
            for filename in importlib.resources.contents(package):
                if Path(filename).suffix.lower() == ".csv":
                    LOG.debug(f"Loading data: {package} {filename}")
                    data = pkgutil.get_data(package, filename)
                    if data is not None:
                        self.process_csv(
                            content=data.decode(json.detect_encoding(data))
                        )

    def process_custom_game(
        self,
        path: Union[str, PathLike[str]],
        *,
        data_sets: Optional[set[str]] = None,
    ) -> None:
        if data_sets is None:
            data_sets = set()
        for data_directory in itertools.chain(
            (Path(path),), (Path(path, data_set) for data_set in data_sets)
        ):
            for data_file in data_directory.iterdir():
                if data_file.suffix.lower() == ".csv":
                    LOG.debug(f"Loading custom data: {data_file}")
                    self.process_csv(path=data_file)
