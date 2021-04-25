#!/usr/bin/env python3

# requires python 3.7+ for dicts being in insertion order

from enum import Enum, auto
from collections import defaultdict
import json
import bisect
import itertools

CHARACTER_CLASS_STATS_JSON = 'darksouls-character-classes.json'
EQUIPMENT_STATS_JSON = 'darksouls-equipment-stats-10.json'
WEIGHT_KEY = 'weight'
VALUE_KEY = 'physical'
EQUIPMENT_TYPES = ['Head', 'Torso', 'Arms', 'Legs' ]

# TODO: factor in rings/character endurance for equip load % gear adjustments

class KnapsackItem(object):
    def __init__(self, weight, value, names=None):
        self.weight = weight
        self.value = value
        if names is None:
            names = []
        elif isinstance(names, str):
            names = [names]
        self.names = names

    @staticmethod
    def from_equipment_section(equipment_section, weight_key, value_key):
        # this makes a list, but so would sorted(), so no need to optimize this away
        torso_ks_input = [ KnapsackItem(
                weight = stats[weight_key],
                value = stats[value_key],
                name = name)
                for name, stats in equipment_section.items()]

    def combine(self, other):
        return KnapsackItem(
                weight = self.weight + other.weight,
                value = self.value + other.value,
                names = self.names + other.names)

    def __lt__(self, other):
        # sort by weight then inverted value
        # the dominate() algorithm requires this sort order
        return (self.weight < other.weight or
                self.weight == other.weight and self.value > other.value)

class KnapsackItemGroup(object):
    def __init__(self, items=None):
        self.items = items

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        debug=False
        if isinstance(items, dict):
            self._items = items
        elif isinstance(items, list):
            # dominance filter
            items = sorted(items)
            # the last survivor will have the highest value so far too
            last_survivor = None
            index = 0
            while index < len(items):
                item = items[index]
                if last_survivor is not None:
                    if (item.value < last_survivor.value
                            or item.value == last_survivor.value and item.weight > last_survivor.weight):
                        if debug:
                            print(f"REMOVED: {item.names} is dominated by {last_survivor.names}")
                        del items[index]
                        continue
                    elif item.value == last_survivor.value and item.weight == last_survivor.weight:
                        if debug:
                            print(f"COMBINED: {item.names} is an equal alternative to {last_survivor.names}")
                        last_survivor.names.extend(item.names)
                        del items[index]
                        continue
                last_survivor = item
                if debug:
                    print(f"KEPT: {item.weight} {item.names}")
                index += 1
            self._items = { item.weight: item for item in items }
        else:
            raise ValueError("items must be a dict(weight:KnapSackItem) or a list(KnapSackItem)")
        # optimization
        self._sorted_weights = sorted(self._items.keys())

    @staticmethod
    def from_equipment_section(section, weight_key, value_key):
        return KnapsackItemGroup(items = [ KnapsackItem(
                weight = stats[weight_key],
                value = stats[value_key],
                names = name)
                for name, stats in section.items() ])

    def __len__(self):
        return len(self.items)

    def best_for_weight(self, weight):
        index = bisect.bisect_right(self._sorted_weights, weight) - 1
        if index == -1:
            return None
        return self.items[self._sorted_weights[index]]

    def combine(self, other):
        return KnapsackItemGroup(items = [ KnapsackItem(
            weight = self_item.weight + other_item.weight,
            value = self_item.value + other_item.value,
            names = [(self_item.names, other_item.names)])
            for self_item, other_item in itertools.product(self.items.values(), other.items.values())])


with open(CHARACTER_CLASS_STATS_JSON, 'r') as handle:
    CHARACTER_CLASSES = json.load(handle)

with open(EQUIPMENT_STATS_JSON, 'r') as handle:
    ALL_EQUIPMENT_STATS = json.load(handle)

solution = [ KnapsackItemGroup.from_equipment_section(
        section = ALL_EQUIPMENT_STATS[equipment_type],
        weight_key = WEIGHT_KEY,
        value_key = VALUE_KEY)
        for equipment_type in EQUIPMENT_TYPES ]

# process the solution in groups of 2
while len(solution) > 1:
    index = 0
    count = len(solution) // 2
    while index < count:
        offset = index*2
        solution[index] = solution[offset].combine(solution[offset+1])
        index += 1
    del solution[index:]

solution = solution[0]

print(f"optimal sets for {VALUE_KEY}: {len(solution)}")
print(solution.best_for_weight(30.0).names)
