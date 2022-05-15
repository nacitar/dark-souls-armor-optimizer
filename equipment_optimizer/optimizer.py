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


@dataclass(frozen=True)
class Configuration:
    value_field: str  # like 'maximize' arg
    position_field: str
    weight_field: str
    weight_modifier_field: str


class Database:
    def __init__(self, configuration: Configuration):
        self._configuration = configuration
        self.name_to_data: dict[str, game_data.Data] = {}
        self.position_to_names: dict[str, set[str]] = {}

    def add_entries(self, entries: Iterable[game_data.Entry]) -> None:
        for entry in entries:
            if entry.name in self.name_to_data:
                LOG.warning(f"Replacing existing piece: {entry.name}")
            self.name_to_data[entry.name] = entry.data
            position = entry.data.textual_fields[
                self._configuration.position_field
            ]
            self.position_to_names.setdefault(position, set()).add(entry.name)

    def metrics(self, name: str) -> Metrics:
        data = self.name_to_data[name]
        return Metrics(
            weight=data.numeric_fields.get(
                self._configuration.weight_field, 0
            ),
            weight_modifier=data.numeric_fields.get(
                self._configuration.weight_modifier_field, 0
            ),
            value=data.numeric_fields.get(self._configuration.value_field, 0),
        )

    def solutions_for_position(
        self, position: str
    ) -> Generator[Solution, None, None]:
        yield from (
            Solution(pieces=[Piece(name=name)], metrics=self.metrics(name))
            for name in self.position_to_names[position]
        )


class SolutionSet:
    def __init__(self, solutions: Iterable[Solution], count: int):
        self.count = count
        self.weight_modifier_heap: list[float] = [0.0] * self.count

        def sort_and_track_weight_modifiers(solution: Solution) -> Metrics:
            heapq.heappushpop(
                self.weight_modifier_heap, solution.metrics.weight_modifier
            )
            return solution.metrics

        self.solutions: list[Solution] = sorted(
            solutions, key=sort_and_track_weight_modifiers
        )

    def max_weight_modifier(self):
        return (
            math.prod(
                [
                    weight_modifier + 1.0
                    for weight_modifier in self.weight_modifier_heap
                ]
            )
            - 1.0
        )

    def filter(self, max_other_weights: float):
        # TODO: need to know own capacity
        # - when combining other weights, add 1.0 first then multiply
        # - N max weights where N is the number of items in that position
        pass


def optimize(database: Database, positions: list[str]):
    # TODO; deterministic order?
    # - BestKnapsackItemForModifierGTE
    # - KnapsackItemSlot
    solution_sets = [
        SolutionSet(
            solutions=database.solutions_for_position(position), count=count
        )
        for position, count in Counter(positions).items()
    ]
    for solution_set in solution_sets:
        print(solution_set.weight_modifier_heap)
