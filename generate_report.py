#!/usr/bin/env python3

# requires python 3.7+ for dicts being in insertion order

from enum import Enum, auto
import json
import bisect
import itertools
import functools
import copy

# A weight that incorporates a modifier
@functools.total_ordering
class KnapsackWeight(object):
    def __init__(self, cost, modifier = 1.0):
        self.cost = cost
        self.modifier = modifier

    # to simplify __hash__ and __eq__
    def __key(self):
        return (self.cost, self.modifier)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, KnapsackWeight):
            return self.__key() == other.__key()
        return NotImplemented

    # the inverted sorted of the modifier makes using __key() not super viable
    def __lt__(self, other):
        # sort my cost then inverted modifier.  smallest weight, largest modifier.
        return (self.cost < other.cost or
            self.cost == other.cost and self.modifier > other.modifier)

    def __add__(self, other):
        if isinstance(other, KnapsackWeight):
            return KnapsackWeight(
                    cost = self.cost + other.cost,
                    modifier = self.modifier * other.modifier)
        return NotImplemented

    def __str__(self):
        if self.modifier == 1.0:
            return str(self.cost)
        return "{} ({:+f})".format(self.cost, self.modifier)

    # So dict values of this type print
    def __repr__(self):
        return self.__str__()

# TODO: factor in rings/character endurance for equip load % gear adjustments
class KnapsackItem(object):
    def __init__(self, weight, value, name, alternatives=None):
        if not isinstance(weight, KnapsackWeight):
            weight = KnapsackWeight(cost = weight)
        self.weight = weight
        self.value = value
        if not isinstance(name, tuple):
            name = (name,)
        self.name = name
        if alternatives is None:
            alternatives = set()
        self.alternatives = alternatives

    def flattened(self, max_weight_cost, extra_weight_cost):
        item = copy.copy(self)
        item.weight = copy.copy(item.weight)
        # convert the cost into a percentage of the weight
        item.weight.cost = (item.weight.cost + extra_weight_cost) / (max_weight_cost * item.weight.modifier)
        item.weight.modifier = 1.0
        return item

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

# Assumes items are being added in ascending order of ascending weight and descending sort_key
class BestKnapsackItemForModifierGTE(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._keys = []
        self._dict = {}

    def add(self, item):
        key = item.weight.modifier

        index = bisect.bisect_left(self._keys, key)

        if index < len(self._keys) and self._keys[index] == key:
            # the key is already present
            current_item = self._dict[key]
            if current_item.value < item.value:
                self._dict[key] = item
        else:
            self._keys.insert(index, key)
            self._dict[key] = item

        # if the next value is larger, assume that value
        next_index = index + 1
        if next_index < len(self._keys):
            next_item = self._dict[self._keys[next_index]]
            if next_item.value > item.value:
                self._dict[key] = next_item

        # walk backward and make any lesser values greater
        while True:
            index -= 1
            if index < 0:
                break
            prior_key = self._keys[index]
            if self._dict[prior_key].value >= item.value:
                break
            self._dict[prior_key] = item
    
    # if this throws IndexError, there's no key that is >= key
    def lookup(self, item):
        key = item.weight.modifier
        index = bisect.bisect_left(self._keys, key)
        return self._dict[self._keys[index]]

    def lookup_modifier(self, modifier):
        return self.lookup(KnapsackItem(weight=KnapsackWeight(cost=None, modifier=modifier), value=None, name=None))

    # for diagnostic purposes
    def sorted(self):
        return sorted(self._dict.items(), key=lambda item: item[0])

# NOTE: test
if False:
    best_for_modifier_gte = BestKnapsackItemForModifierGTE()
    best_for_modifier_gte.add(KnapsackItem(weight=KnapsackWeight(cost=0, modifier=0), value=10, name='A'))
    print(best_for_modifier_gte.sorted())
    best_for_modifier_gte.add(KnapsackItem(weight=KnapsackWeight(cost=0, modifier=1), value=5, name='B'))
    print(best_for_modifier_gte.sorted())
    best_for_modifier_gte.add(KnapsackItem(weight=KnapsackWeight(cost=0, modifier=2), value=3, name='C'))
    print(best_for_modifier_gte.sorted())
    best_for_modifier_gte.add(KnapsackItem(weight=KnapsackWeight(cost=0, modifier=4), value=6, name='D'))
    print(best_for_modifier_gte.sorted())
    best_for_modifier_gte.add(KnapsackItem(weight=KnapsackWeight(cost=4, modifier=-1), value=5, name='E'))  # needs to become 10
    print(best_for_modifier_gte.sorted())
    print(best_for_modifier_gte.lookup_modifier(0))
    print(best_for_modifier_gte.lookup_modifier(3))
    exit(1)

CHARACTER_CLASS_STATS_JSON = 'darksouls-character-classes.json'
EQUIPMENT_STATS_JSON = 'darksouls-equipment-stats-10.json'
WEIGHT_KEY = 'weight'
WEIGHT_MODIFIER_KEY = 'weight_modifier'
VALUE_KEY = 'physical'
MAX_WEIGHT_COST = 51.0
MAX_WEIGHT_PERCENT = 0.25
EXTRA_WEIGHT_COST = 2.0  # weapons weight
EQUIPMENT_TYPES = ['Head', 'Torso', 'Arms', 'Legs' ]



class KnapsackSolution(object):
    def __init__(self, items=None):
        self.items = items

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        if not isinstance(items, dict):
            raise TypeError('items must be a dict')
        self._items = items
        self._sorted_weights = sorted(self._items.keys())

    def __len__(self):
        return len(self.items)

    # weight modifications need to be applied
    def best_for_load_percentage(self, load, count=1):
        weight = KnapsackWeight(cost = load)
        index = bisect.bisect_right(self._sorted_weights, weight) - 1
        if index == -1:
            return None
        start = max(index - count + 1, 0)
        return [self.items[weight] for weight in reversed(self._sorted_weights[start: start+count])]

class KnapsackItemGroup(object):
    def __init__(self, items, debug=0):
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
            index = 0
            best_for_modifier_gte = BestKnapsackItemForModifierGTE()
            last_survivor = None
            while index < len(items):
                item = items[index]
                try:
                    possible_dominator = best_for_modifier_gte.lookup(item)
                except IndexError:
                    possible_dominator = None

                if possible_dominator is not None:
                    if (item.value < possible_dominator.value
                            or item.value == possible_dominator.value and item.weight > possible_dominator.weight):
                        if self.debug > 1:
                            print(f"REMOVED: {item.name} is dominated by {possible_dominator.name}")
                        del items[index]
                        continue
                if (last_survivor is not None and item.value == last_survivor.value
                        and item.weight == last_survivor.weight):  # checks modifier too 
                    if self.debug > 1:
                        print(f"COMBINED: {item.name} is an equal alternative to {last_survivor.name}")
                    last_survivor.alternatives.add(item.name)
                    del items[index]
                    continue

                last_survivor = item
                best_for_modifier_gte.add(item) 
                if self.debug > 1:
                    print(f"KEPT: {item.weight} {item.name}")
                index += 1
            self._items = { item.weight: item for item in items }
            if self.debug > 0:
                print(f"Entries removed due to being suboptimal: {before_dominance -len(self._items)}")
        else:
            raise ValueError("items must be a dict(weight:KnapSackItem) or a list(KnapSackItem)")

    def __len__(self):
        return len(self.items)

    @staticmethod
    def from_equipment_section(section, weight_key, weight_modifier_key, value_key):
        return KnapsackItemGroup(items = [ KnapsackItem(
                weight = KnapsackWeight(cost=stats[weight_key], modifier=stats[weight_modifier_key]),
                value = stats[value_key],
                name = name)
                for name, stats in section.items() ])

    def flatten_to_solution(self, max_weight_cost, extra_weight_cost):
        flattened = KnapsackItemGroup(items = [ item.flattened(
                    max_weight_cost=max_weight_cost, extra_weight_cost=extra_weight_cost)
                    for item in self.items.values() ])
        return KnapsackSolution(items = flattened.items)

    def combine(self, other):
        return KnapsackItemGroup(items = [ self_item.combine(other_item)
            for self_item, other_item in itertools.product(self.items.values(), other.items.values())])


with open(CHARACTER_CLASS_STATS_JSON, 'r') as handle:
    CHARACTER_CLASSES = json.load(handle)

with open(EQUIPMENT_STATS_JSON, 'r') as handle:
    ALL_EQUIPMENT_STATS = json.load(handle)

groups = [ KnapsackItemGroup.from_equipment_section(
        section = ALL_EQUIPMENT_STATS[equipment_type],
        weight_key = WEIGHT_KEY,
        weight_modifier_key = WEIGHT_MODIFIER_KEY,
        value_key = VALUE_KEY)
        for equipment_type in EQUIPMENT_TYPES ]

# process the groups in batches of 2
# NOTE: certain orders will prune things faster and as a consequence be more efficient
# but I do not know of a good way to decide the order.
while len(groups) > 1:
    index = 0
    count = len(groups) // 2
    while index < count:
        offset = index*2
        groups[index] = groups[offset].combine(groups[offset+1])
        index += 1
    del groups[index:]

# All groups combined into one

solution = groups[0].flatten_to_solution(max_weight_cost=MAX_WEIGHT_COST, extra_weight_cost=EXTRA_WEIGHT_COST)
#print(solution.items)
print(f"optimal sets for {VALUE_KEY}: {len(solution)}")
top_ten = solution.best_for_load_percentage(0.25, count=10)
for entry in top_ten:
    print(entry)


exit(1)
