#!/usr/bin/env python3

from typing import Iterable, Optional, Union, Iterator
from pathlib import Path
from os import PathLike
import logging
from . import game_data

LOG = logging.getLogger(__name__)


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


class EquipmentDatabase(object):
    def __init__(
        self,
        *,
        name_field: str = "name",
        position_field: str = "position",
        fields: Optional[set[str]] = None,
        exclude: Optional[dict[str, set[str]]] = None,
    ):
        self.pieces: dict[str, PieceData] = {}
        self._name_field = name_field
        self._position_field = position_field
        if fields is not None:
            self._fields = fields.copy()
            self._fields.update((self._name_field, self._position_field))
        else:
            self._fields = None  # get all of them
        self._exclude: dict[str, set[str]] = exclude or {}

    def by_position(
        self, positions: Optional[set[str]] = None
    ) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        for name, data in self.pieces.items():
            position = data.get_attribute(self._position_field)
            if position and (not positions or position in positions):
                result.setdefault(position, set()).add(name)
        return result

    def is_csv_row_excluded(self, row: dict[str, str]) -> bool:
        for attribute, value in self._exclude.items():
            if row.get(attribute, "") in value:
                return True
        return False

    def import_csv_row(self, row: dict[str, str]) -> None:
        if self.is_csv_row_excluded(row):
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

    def import_csv(
        self,
        path: Optional[Union[str, PathLike[str]]] = None,
        content: Optional[str] = None,
    ) -> None:
        if path is not None:
            with game_data.open_csv(path) as csv_file:
                for row in game_data.iterate_csv(file=csv_file):
                    self.import_csv_row(row)
        if content is not None:
            for row in game_data.iterate_csv(content=content):
                self.import_csv_row(row)

    def import_builtin_game(
        self, game: str, *, data_sets: Optional[list[str]] = None
    ) -> None:
        for path in game_data.get_csv_files(
            game, data_sets=data_sets, is_resource=True
        ):
            self.import_csv(content=game_data.get_resource_content(path))

    def import_custom_game(
        self,
        path: Union[str, PathLike[str]],
        *,
        data_sets: Optional[Iterable[str]] = None,
    ) -> None:
        for path in game_data.get_csv_files(path, data_sets=data_sets):
            self.import_csv(path=path)
