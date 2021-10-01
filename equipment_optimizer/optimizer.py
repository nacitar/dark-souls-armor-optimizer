import logging
from functools import total_ordering
from dataclasses import dataclass

LOG = logging.getLogger(__name__)


@total_ordering
@dataclass(frozen=True)
class Weight(object):
    cost: float
    modifier: float

    def __lt__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        # sort by smallest cost then largest modifier
        return (
            self.cost < other.cost
            or self.cost == other.cost
            and self.modifier > other.modifier
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.cost != other.cost or self.modifier != other.modifier
