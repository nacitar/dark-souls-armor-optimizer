from __future__ import annotations  # until Python 3.10+
import logging
import heapq
import math
import bisect
from functools import total_ordering
from dataclasses import dataclass, field
from collections import Counter
from typing import Iterable, Generator, Optional
from . import game_data

LOG = logging.getLogger(__name__)


# TODO: swap float to Fraction?


@total_ordering
@dataclass(frozen=True)
class Metrics:
    weight: float
    weight_multiplier: float
    value: float

    def __lt__(self, other: Metrics) -> bool:
        """sorts by: least weight, largest weight_multiplier, largest value"""
        return (
            self.weight < other.weight
            or self.weight == other.weight
            and (
                self.weight_multiplier > other.weight_multiplier
                or self.weight_multiplier == other.weight_multiplier
                and self.value > other.value
            )
        )

    def __add__(self, other: Metrics) -> Metrics:
        return Metrics(
            weight=self.weight + other.weight,
            weight_multiplier=self.weight_multiplier + other.weight_multiplier,
            value=self.value + other.value,
        )


@dataclass(frozen=True)
class Piece:
    name: str
    alternatives: set[str] = field(default_factory=set)


@total_ordering
@dataclass(frozen=True)
class Solution:
    pieces: list[Piece]
    metrics: Metrics

    def __add__(self, other: Solution) -> Solution:
        return Solution(
            pieces=self.pieces + other.pieces,
            metrics=self.metrics + other.metrics,
        )

    def __lt__(self, other: Solution) -> bool:
        return (
            self.metrics < other.metrics
            or self.metrics == other.metrics
            and len(self.pieces) < len(other.pieces)
            # TODO: flesh out comparison for deterministic results?
        )


@dataclass(kw_only=True, eq=False)
class Database:
    position_field: str
    weight_field: str
    weight_modifier_field: str

    def __post_init__(self):
        self.name_to_data: dict[str, game_data.Data] = {}
        self.position_to_names: dict[str, set[str]] = {}

    def add_entries(self, entries: Iterable[game_data.Entry]) -> None:
        for entry in entries:
            if entry.name in self.name_to_data:
                LOG.warning(f"Replacing existing piece: {entry.name}")
            self.name_to_data[entry.name] = entry.data
            position = entry.data.textual_fields[self.position_field]
            self.position_to_names.setdefault(position, set()).add(entry.name)

    def metrics(self, name: str, *, value_field: str) -> Metrics:
        data = self.name_to_data[name]
        return Metrics(
            weight=data.numeric_fields.get(self.weight_field, 0),
            weight_multiplier=data.numeric_fields.get(
                self.weight_modifier_field, 0
            )
            + 1.0,  # convert relative % to multiplier
            value=data.numeric_fields.get(value_field, 0),
        )

    def solutions_for_position(
        self, position: str, *, value_field: str
    ) -> Generator[Solution, None, None]:
        yield from (
            Solution(
                pieces=[Piece(name=name)],
                metrics=self.metrics(name, value_field=value_field),
            )
            for name in self.position_to_names[position]
        )


@dataclass(kw_only=True)
class Extents:
    minimum_weight: float = 0.0
    maximum_weight_multiplier: float = 1.0

    def __add__(self, other: Extents) -> Extents:
        return Extents(
            minimum_weight=self.minimum_weight + other.minimum_weight,
            maximum_weight_multiplier=(
                self.maximum_weight_multiplier
                * other.maximum_weight_multiplier
            ),
        )

    def __sub__(self, other: Extents) -> Extents:
        return Extents(
            minimum_weight=self.minimum_weight - other.minimum_weight,
            maximum_weight_multiplier=(
                self.maximum_weight_multiplier
                / other.maximum_weight_multiplier
            ),
        )


class BestSolutionWithWeightMultiplierAtLeast:
    """
    This class is essentially a lookup table/buffer to remember the highest
    value solution with a weight multiplier greater than or equal to the weight
    multiplier of the solution currently being processed.  This is intended to
    be used when processing a Solution list in sorted order, as the sort order
    intentionally places higher value solutions and solutions that could
    possibly dominate other solutions earlier in the list.  This provides the
    information the algorithm needs to perform the full domination reduction in
    a single pass, by efficiently knowing that a solution with a weight
    multiplier greater than or equal to the current solution and a value
    greater than or equal to the current solution exists, hence the current
    solution can be removed outright due to being suboptimal in all cases.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        # because the weights are in ascending order, everything will be the
        # same weight or heavier than what has already been processed.
        self._sorted_weight_multipliers: list[float] = []
        # keyed by multiplier
        self._best_at_least: dict[float, Solution] = {}

    def weight_multiplier_index(self, weight_multiplier: float) -> int:
        return bisect.bisect_left(
            self._sorted_weight_multipliers, weight_multiplier
        )

    def add(self, solution: Solution):
        weight_multiplier = solution.metrics.weight_multiplier

        best = self.lookup(weight_multiplier)
        index = self.weight_multiplier_index(weight_multiplier)
        if (
            index < len(self._sorted_weight_multipliers)
            and self._sorted_weight_multipliers[index] == weight_multiplier
        ):
            # an item with this multiplier exists... is the current one better?
            best = self._best_at_least[self._sorted_weight_multipliers[index]]
            if best.metrics.value < solution.metrics.value:
                self._best_at_least[weight_multiplier] = solution
            else:
                return  # nothing changed, so, no state to adjust
        else:
            # add this solution for this multiplier
            self._sorted_weight_multipliers.insert(index, weight_multiplier)
            self._best_at_least[weight_multiplier] = solution

        # If a higher multiplier exists with a higher value, it's the best for
        # this multiplier too (it isn't heavier either, due to order).
        index_next = index + 1
        if index_next < len(self._sorted_weight_multipliers):
            weight_multiplier_next = self._sorted_weight_multipliers[
                index_next
            ]
            best_next = self._best_at_least[weight_multiplier_next]
            if best_next.metrics.value >= solution.metrics.value:
                # higher multiplier, same or better value
                self._best_at_least[weight_multiplier] = best_next

        # Walk backward and update any lesser values to be greater
        while True:
            index -= 1
            if index < 0:
                break
            weight_multiplier_prior = self._sorted_weight_multipliers[index]
            if (
                self._best_at_least[weight_multiplier_prior].metrics.value
                >= solution.metrics.value
            ):
                break
            self._best_at_least[weight_multiplier_prior] = solution

    def lookup(self, weight_multiplier: float) -> Optional[Solution]:
        index = self.weight_multiplier_index(weight_multiplier)
        if index < len(self._sorted_weight_multipliers):
            return self._best_at_least[self._sorted_weight_multipliers[index]]
        return None

    def sorted(self):
        # For diagnostic purposes
        return sorted(self._best_at_least.items(), key=lambda item: item[0])


class SolutionSet:
    def __init__(self, solutions: Iterable[Solution], count: int):
        self.count = count
        weight_multiplier_heap: list[float] = [1.0] * self.count
        minimum_weight = 0.0

        def sort_by_metrics_and_measure_extents(solution: Solution) -> Metrics:
            nonlocal minimum_weight
            heapq.heappushpop(
                weight_multiplier_heap, solution.metrics.weight_multiplier
            )
            minimum_weight = min(solution.metrics.weight, minimum_weight)
            return solution.metrics

        self.solutions: list[Solution] = sorted(
            solutions, key=sort_by_metrics_and_measure_extents
        )
        self.extents = Extents(
            minimum_weight=minimum_weight,
            maximum_weight_multiplier=math.prod(weight_multiplier_heap),
        )

    def filter(
        self,
        *,
        maximum_weight: float,
        used_weight: float,
        full_extents: Extents,
    ) -> Generator[Solution, None, None]:
        external_extents = full_extents - self.extents
        for solution in self.solutions:
            # TODO: actually filter down the solutions!
            # TODO: how is count handled in the result?
            # how will I make a copy?
            yield solution


class Optimizer:
    def __init__(
        self, *, database: Database, value_field: str, positions: list[str]
    ):
        self.full_extents = Extents()
        self.solution_sets: list[SolutionSet] = []
        for position, count in Counter(positions).items():
            solution_set = SolutionSet(
                solutions=database.solutions_for_position(
                    position, value_field=value_field
                ),
                count=count,
            )
            self.full_extents += solution_set.extents
            self.solution_sets.append(solution_set)

    def optimize(self, *, maximum_weight: float, used_weight: float):
        # TODO: everything...
        for solution_set in self.solution_sets:
            solution_set.filter(
                maximum_weight=maximum_weight,
                used_weight=used_weight,
                full_extents=self.full_extents,
            )
