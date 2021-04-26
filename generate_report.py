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
    def __init__(self, weight, value, name, alternatives=None):
        self.weight = weight
        self.value = value
        if not isinstance(name, tuple):
            name = (name,)
        self.name = name
        if alternatives is None:
            alternatives = set()
        self.alternatives = alternatives

    def combine(self, other):
        return KnapsackItem(
                weight = self.weight + other.weight,
                value = self.value + other.value,
                name = self.name + other.name,
                # TODO: should this all be calculated here? or just listed in
                # a manner that could be done later?
                alternatives = set(itertools.product(
                        self.alternatives, other.alternatives)))

    def __lt__(self, other):
        # sort by weight then inverted value
        # the dominate() algorithm requires this sort order
        return (self.weight < other.weight or
                self.weight == other.weight and self.value > other.value)

    def __str__(self):
        # NOTE: the str usages here are turning tuples into strings, with quotes and all
        display_name = ' OR '.join(itertools.chain([str(self.name)], map(str, self.alternatives)))
        return f"({self.value}) [{self.weight}] {display_name}"

    # So dict values of this type print
    def __repr__(self):
        return self.__str__()

class KnapsackItemGroup(object):
    def __init__(self, items=None, debug=0):
        self.debug = debug  # has to happen before setting items
        self.items = items

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        if isinstance(items, dict):
            self._items = items
        elif isinstance(items, list):
            # dominance filter
            before_dominance = len(items)
            items = sorted(items)
            # the last survivor will have the highest value so far too
            last_survivor = None
            index = 0
            while index < len(items):
                item = items[index]
                # TODO: implement some sort of weight limit per-piece to help pruning?
                if last_survivor is not None:
                    if (item.value < last_survivor.value
                            or item.value == last_survivor.value and item.weight > last_survivor.weight):
                        if self.debug > 1:
                            print(f"REMOVED: {item.name} is dominated by {last_survivor.name}")
                        del items[index]
                        continue
                    elif item.value == last_survivor.value and item.weight == last_survivor.weight:
                        if self.debug > 1:
                            print(f"COMBINED: {item.name} is an equal alternative to {last_survivor.name}")
                        last_survivor.alternatives.add(item.name)
                        del items[index]
                        continue
                last_survivor = item
                if self.debug > 1:
                    print(f"KEPT: {item.weight} {item.name}")
                index += 1
            self._items = { item.weight: item for item in items }
            if self.debug > 0:
                print(f"Entries removed due to being suboptimal: {before_dominance -len(self._items)}")
        else:
            raise ValueError("items must be a dict(weight:KnapSackItem) or a list(KnapSackItem)")
        # optimization
        self._sorted_weights = sorted(self._items.keys())

    @staticmethod
    def from_equipment_section(section, weight_key, value_key):
        return KnapsackItemGroup(items = [ KnapsackItem(
                weight = stats[weight_key],
                value = stats[value_key],
                name = name)
                for name, stats in section.items() ])

    def __len__(self):
        return len(self.items)

    def best_for_weight(self, weight, count=1):
        index = bisect.bisect_right(self._sorted_weights, weight) - 1
        if index == -1:
            return None
        start = max(index - count + 1, 0)
        return [self.items[weight] for weight in reversed(self._sorted_weights[start: start+count])]

    def combine(self, other):
        return KnapsackItemGroup(items = [ self_item.combine(other_item)
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
# NOTE: certain orders will prune things faster and as a consequence be more efficient
# but I do not know of a good way to decide the order.
while len(solution) > 1:
    index = 0
    count = len(solution) // 2
    while index < count:
        offset = index*2
        solution[index] = solution[offset].combine(solution[offset+1])
        index += 1
    del solution[index:]

# All groups combined into one
solution = solution[0]
#print(solution.items)
print(f"optimal sets for {VALUE_KEY}: {len(solution)}")
top_ten = solution.best_for_weight(51.0, 10)
for entry in top_ten:
    print(entry)
