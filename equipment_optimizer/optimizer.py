from __future__ import annotations  # until Python 3.10+
import logging
from functools import total_ordering
from dataclasses import dataclass
from .game_data import PieceData

LOG = logging.getLogger(__name__)


@total_ordering
@dataclass(frozen=True)
class Weight(object):
    cost: float
    modifier: float

    def __lt__(self, other: Weight) -> bool:
        # sort by smallest cost then largest modifier
        return (
            self.cost < other.cost
            or self.cost == other.cost
            and self.modifier > other.modifier
        )

    def __add__(self, other: Weight) -> Weight:
        return Weight(
            cost=self.cost + other.cost,
            modifier=self.modifier + other.modifier,
        )


@dataclass(frozen=True)
class Equipment(object):
    pieces: list[str]
    weight: Weight
    value: float

    def __add__(self, other: Equipment):
        return Equipment(
            pieces=self.pieces + other.pieces,
            weight=self.weight + other.weight,
            value=self.value + other.value,
        )
