#!/usr/bin/env python3

from typing import Iterable, Optional, Union
from pathlib import Path
from os import PathLike
import csv
import logging
from . import game_data

LOG = logging.getLogger(__name__)


exclude = {
    "set": set(["Havel"]),
    "name": set(["Wanderer Manchettes"]),
}


class Equipment(object):
    def __init__(
        self,
        *,
        statistics: Optional[Iterable[str]] = None,
        position_key: str = "position",
        name_key: str = "name",
        exclude: Optional[dict[str, set[str]]] = None,
    ):
        # position => name => statistics => nonzero float value
        self.data: dict[str, dict[str, dict[str, float]]] = {}
        # None means to get all of them
        self._statistics = list(statistics) if statistics is not None else None
        self._position_key = position_key
        self._name_key = name_key
        self._exclude = exclude or {}

    def filter_statistics(
        self, piece: dict[str, str]
    ) -> Optional[dict[str, float]]:
        for statistic, value in self._exclude.items():
            if piece.get(statistic) in value:
                return None
        return {
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

    def import_piece(self, piece: dict[str, str]) -> bool:
        statistics = self.filter_statistics(piece)
        if statistics is not None:
            section = self.data.setdefault(piece[self._position_key], {})
            section[piece[self._name_key]] = statistics
            return True
        return False

    def import_csv(
        self,
        path: Optional[Union[str, PathLike[str]]] = None,
        content: Optional[str] = None,
    ) -> None:
        if path is not None:
            with open(path, mode="r", newline="") as handle:
                for piece in csv.DictReader(handle):
                    self.import_piece(piece)
        elif content is None:
            raise TypeError("Must specify path and/or content.")
        if content is not None:
            for piece in csv.DictReader(game_data.iterlines(content)):
                self.import_piece(piece)

    def import_builtin_game(
        self, game: str, *, data_sets: Optional[list[str]] = None
    ):
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
