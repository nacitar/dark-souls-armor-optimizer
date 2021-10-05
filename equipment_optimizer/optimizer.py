from __future__ import annotations  # until Python 3.10+
import logging
from functools import total_ordering
from dataclasses import dataclass
from . import game_data

LOG = logging.getLogger(__name__)


@total_ordering
@dataclass(frozen=True)
class Metrics(object):
    cost: float
    modifier: float
    value: float

    def __lt__(self, other: Metrics) -> bool:
        """sorts by: smallest cost, largest modifier, largest value"""
        return (
            self.cost < other.cost
            or self.cost == other.cost
            and (
                self.modifier > other.modifier
                or self.modifier == other.modifier
                and self.value > other.value
            )
        )

    def __add__(self, other: Metrics) -> Metrics:
        return Metrics(
            cost=self.cost + other.cost,
            modifier=self.modifier + other.modifier,
            value=self.value + other.value,
        )


@dataclass(frozen=True)
class Piece(object):
    name: str
    alternatives: set[str]


@dataclass(frozen=True)
class Equipment(object):
    pieces: list[Piece]
    metrics: Metrics

    def __add__(self, other: Equipment):
        return Equipment(
            pieces=self.pieces + other.pieces,
            metrics=self.metrics + other.metrics,
        )
