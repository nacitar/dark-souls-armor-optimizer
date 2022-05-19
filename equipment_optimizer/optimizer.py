from __future__ import annotations  # until Python 3.10+
import logging
import heapq
import math
from functools import total_ordering
from dataclasses import dataclass, field
from collections import Counter
from typing import Iterable, Generator
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
        """sorts by: smallest weight, largest weight_multiplier, largest value"""
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


class SolutionSet:
    def __init__(self, solutions: Iterable[Solution], count: int):
        self.count = count
        weight_multiplier_heap: list[float] = [1.0] * self.count

        def sort_by_metrics_and_track_weight_multipliers(
            solution: Solution,
        ) -> Metrics:
            heapq.heappushpop(
                weight_multiplier_heap, solution.metrics.weight_multiplier
            )
            return solution.metrics

        self.solutions: list[Solution] = sorted(
            solutions, key=sort_by_metrics_and_track_weight_multipliers
        )
        self.max_weight_multiplier = math.prod(weight_multiplier_heap)

    def filter(self, max_other_weights: float):
        # TODO: need to know own capacity
        # - N max weights where N is the number of items in that position
        pass


class Optimizer:
    def __init__(
        self, *, database: Database, value_field: str, positions: list[str]
    ):
        self.max_weight_multiplier = 1.0
        self.solution_sets: list[SolutionSet] = []
        for position, count in Counter(positions).items():
            solution_set = SolutionSet(
                solutions=database.solutions_for_position(
                    position, value_field=value_field
                ),
                count=count,
            )
            self.max_weight_multiplier *= solution_set.max_weight_multiplier
            self.solution_sets.append(solution_set)

    def optimize(self, *, max_weight: float, used_weight: float):
        for solution_set in self.solution_sets:
            # max increase in weight multipler possible from other positions.
            max_external_weight_multiplier = (
                self.max_weight_multiplier / solution_set.max_weight_multiplier
            )
            print(
                solution_set.max_weight_multiplier,
                max_external_weight_multiplier,
            )
