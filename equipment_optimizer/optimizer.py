from __future__ import annotations  # until Python 3.10+
import logging
from functools import total_ordering
from dataclasses import dataclass
from typing import Protocol, Any

LOG = logging.getLogger(__name__)


class WeightLike(Protocol):
    cost: float
    modifier: float


@total_ordering
@dataclass(frozen=True)
class Weight(object):
    cost: float
    modifier: float

    def __eq__(self, other: Any) -> bool:
        return self.cost == other.cost and self.modifier == other.modifier

    def __lt__(self, other: WeightLike) -> bool:
        # sort by smallest cost then largest modifier
        return (
            self.cost < other.cost
            or self.cost == other.cost
            and self.modifier > other.modifier
        )

    def __add__(self, other: WeightLike) -> Weight:
        return Weight(
            cost=self.cost + other.cost,
            modifier=self.modifier + other.modifier,
        )
