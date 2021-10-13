from __future__ import annotations  # until Python 3.10+
import logging
from functools import total_ordering
from dataclasses import dataclass
from . import game_data

LOG = logging.getLogger(__name__)


@total_ordering
@dataclass(frozen=True)
class Metrics:
    weight: float
    weight_modifier: float
    value: float

    def __lt__(self, other: Metrics) -> bool:
        """sorts by: smallest weight, largest weight_modifier, largest value"""
        return (
            self.weight < other.weight
            or self.weight == other.weight
            and (
                self.weight_modifier > other.weight_modifier
                or self.weight_modifier == other.weight_modifier
                and self.value > other.value
            )
        )

    def __add__(self, other: Metrics) -> Metrics:
        return Metrics(
            weight=self.weight + other.weight,
            weight_modifier=self.weight_modifier + other.weight_modifier,
            value=self.value + other.value,
        )


@dataclass(frozen=True)
class Piece:
    name: str
    alternatives: set[str]


@dataclass(frozen=True)
class Equipment:
    pieces: list[Piece]
    metrics: Metrics

    def __add__(self, other: Equipment):
        return Equipment(
            pieces=self.pieces + other.pieces,
            metrics=self.metrics + other.metrics,
        )
