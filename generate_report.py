#!/usr/bin/env python3

from enum import Enum, auto
import json
import bisect
import itertools
import functools
import copy

CHARACTER_CLASS_STATS_JSON = 'darksouls-character-classes.json'
EQUIPMENT_STATS_JSON = 'darksouls-equipment-stats-10.json'
RING_STATS_JSON = 'darksouls-ring-stats.json'
EQUIPMENT_TYPES = ['Head', 'Torso', 'Arms', 'Legs' ]

WEIGHT_KEY = 'weight'
WEIGHT_MODIFIER_KEY = 'weight_modifier'
VALUE_KEY = 'physical'

MAX_WEIGHT_COST = 51.0
MAX_WEIGHT_PERCENT = 0.25
EXTRA_WEIGHT_COST = 2.0  # weapons weight

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

@functools.total_ordering
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

    @classmethod
    def combine_all(cls, items):
        if isinstance(items, cls):
            items = [items]
        else:
            items = list(items)
        result = None
        for item in items:
            if result is None:
                result = item
            else:
                result = KnapsackItem(
                        weight = result.weight + item.weight,
                        value = result.value + item.value,
                        name = result.name + item.name,
                        alternatives = set(itertools.chain(result.alternatives, item.alternatives)))
        return result


    def combine(self, item):
        return type(self).combine_all([self, item])

    def __eq__(self, other):
        return (self.weight == other.weight and self.value == other.value
                and self.name == other.name)

    def __lt__(self, other):
        # sort by weight then inverted value
        # the dominate() algorithm requires this sort order
        return (self.weight < other.weight or
                self.weight == other.weight and self.value > other.value or
                self.value == other.value and self.name < other.name)

    def __str__(self):
        # the str usages here are turning tuples into strings, with quotes and all
        display_name = ' SWAPPABLE '.join(itertools.chain([str(self.name)], map(str, self.alternatives)))
        return f"({self.value}) [{self.weight}] {display_name}"

    # So dict values of this type print
    def __repr__(self):
        return self.__str__()

# This is essentially a lookup table/buffer to remember the highest value item with a
# modifier greater than or equal to the modifier of the item currently being processed.
# The intention is for this to only be used when processing a KnapsackItem list in
# sorted order, because the sort order intentionally places higher value items and
# items that could possibly dominate other items earlier in the list than those
# that would be dominated by them.  This provides the information the algorithm needs
# in order to perform the full domination reduction in a single pass, by allowing it to
# efficiently know that an item with a modifier greater than or equal to the current item
# and a value greater than or equal to the current item exists, and thus that the
# current item can be removed outright due to being suboptimal in all cases.
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

class KnapsackSolution(object):
    def __init__(self, items=None):
        if not isinstance(items, dict):
            raise TypeError('items must be a dict')
        self.items = items
        self._sorted_weights = sorted(self.items.keys())

    def __len__(self):
        return len(self.items)

    # weight modifications need to be applied
    def best_for_load_percentage(self, load, count=1):
        weight = KnapsackWeight(cost = load)
        index = bisect.bisect_right(self._sorted_weights, weight) - 1
        if index == -1:
            return None
        end = index+1
        return [self.items[weight] for weight in reversed(self._sorted_weights[max(end - count, 0):end])]

# NOTE: slot_count is a request; if there aren't enough items left after pruning to provide that many selections, less slots will be provided.
class KnapsackItemGroup(object):
    def __init__(self, items, slot_count=1, debug=0):
        self.debug = debug

        if isinstance(items, dict):
            self.items = items
        elif isinstance(items, list):
            # dominance filter
            before_dominance = len(items)
            while True:
                items = sorted(items)
                index = 0
                best_for_modifier_gte = BestKnapsackItemForModifierGTE()
                last_survivor = None
                # how many items thus far have been dominated by the referenced one, even if they weren't pruned
                lesser_item_count = {}
                while index < len(items):
                    item = items[index]
                    try:
                        possible_dominator = best_for_modifier_gte.lookup(item)
                    except IndexError:
                        possible_dominator = None
                    dominated = 0
                    alternative = False
                    
                    if possible_dominator is not None:
                        if (item.value < possible_dominator.value
                                or item.value == possible_dominator.value and item.weight > possible_dominator.weight):
                            dominated = lesser_item_count.get(item.name, 0) + 1
                            lesser_item_count[item.name] = dominated
                    if (last_survivor is not None and item.value == last_survivor.value
                            and item.weight == last_survivor.weight):  # checks modifier too 
                        dominated = lesser_item_count.get(last_survivor.name, 0) + 1
                        lesser_item_count[last_survivor.name] = dominated
                        alternative = True

                    if dominated > 0:
                        # even if we don't prune it out, we don't need this piece to factor
                        # into the domination logic.  There is no need to directly acknowledge
                        # that this item dominates some other when this item itself is also
                        # dominated by some even better item.  The comparison is best performed
                        # between that item and the most dominant item.

                        # other slots could use things we dominate/things that are lesser.
                        # so make sure we have avoided pruning out at LEAST that many of
                        # the lesser items before removing this one.

                        # Each particular item needs to have enough fallbacks to cover extra
                        # slots, so we track how many items each one has dominated to ensure
                        # we don't remove fallback options for once the dominant item has
                        # already been selected but there are more slots to go.
                        if dominated + 1 > slot_count:
                            if alternative:
                                if self.debug > 1:
                                    print(f"COMBINED: {item.name} is an equal alternative to {last_survivor.name}")
                                last_survivor.alternatives.add(item.name)
                            else:
                                if self.debug > 1:
                                    print(f"REMOVED: {item.name} is dominated by {possible_dominator.name}")
                            del items[index]
                            continue
                        else:
                            if self.debug > 1:
                                print(f"KEPT: {item.weight} {item.name} after comparing with {possible_dominator.name}")
                    else:
                        last_survivor = item
                        best_for_modifier_gte.add(item) 
                    index += 1

                if self.debug > 0:
                    print(f"Entries removed due to being suboptimal: {before_dominance -len(items)}")
                possible_slots = min(len(items), slot_count)
                if possible_slots > 1:
                    #import pdb
                    #pdb.set_trace()
                    slot_count = 1
                    items = [ KnapsackItem.combine_all(items)
                        for items in itertools.combinations(items, r = possible_slots) ]
                    continue  # run it again to reduce the combinations
                break
            self.items = { item.weight: item for item in items }
        else:
            raise ValueError("items must be a dict(weight:KnapSackItem) or a list(KnapSackItem)")

    def __len__(self):
        return len(self.items)

    @staticmethod
    def from_equipment_section(section, weight_key, weight_modifier_key, value_key, slot_count):
        defaults = section['defaults']
        return KnapsackItemGroup(items = [ KnapsackItem(
                weight = KnapsackWeight(
                    cost = stats[weight_key] if weight_key in stats else defaults[weight_key],
                    modifier = stats[weight_modifier_key] if weight_modifier_key in stats else defaults[weight_modifier_key]
                    ),
                value = stats[value_key] if value_key in stats else defaults[value_key],
                name = name)
                for name, stats in section['entries'].items() ],
                slot_count = slot_count)

    def flatten_to_solution(self, max_weight_cost, extra_weight_cost):
        flattened = KnapsackItemGroup(items = [ item.flattened(
                    max_weight_cost=max_weight_cost, extra_weight_cost=extra_weight_cost)
                    for item in self.items.values() ])
        return KnapsackSolution(items = flattened.items)

    @classmethod
    def combine_in_pairs(cls, groups):
        if isinstance(groups, cls):
            groups = [groups]
        else:
            groups = list(groups)
        while len(groups) > 1:
            index = 0
            count = len(groups) // 2
            while index < count:
                offset = index*2
                groups[index] = KnapsackItemGroup(
                        items = [ first_item.combine(second_item)
                                for first_item, second_item in itertools.product(
                                        groups[offset].items.values(),
                                        groups[offset+1].items.values())])
                index += 1
            del groups[index:]
        return groups[0]
        
    def combine(self, other):
        return type(self).combine_in_pairs([self, other])


with open(CHARACTER_CLASS_STATS_JSON, 'r') as handle:
    CHARACTER_CLASSES = json.load(handle)

with open(EQUIPMENT_STATS_JSON, 'r') as handle:
    ALL_EQUIPMENT_STATS = json.load(handle)

with open(RING_STATS_JSON, 'r') as handle:
    RING_STATS = json.load(handle)

# NOTE: certain orders will prune things faster and as a consequence be more efficient
# but I do not know of a good way to decide the order.
combined_group = KnapsackItemGroup.combine_in_pairs(
        [ KnapsackItemGroup.from_equipment_section(
                section = ALL_EQUIPMENT_STATS[equipment_type],
                weight_key = WEIGHT_KEY,
                weight_modifier_key = WEIGHT_MODIFIER_KEY,
                value_key = VALUE_KEY,
                slot_count = 1)
                for equipment_type in EQUIPMENT_TYPES ])

# Add rings
combined_group = combined_group.combine(KnapsackItemGroup.from_equipment_section(
        section = RING_STATS['Fingers'],
        weight_key = WEIGHT_KEY,
        weight_modifier_key = WEIGHT_MODIFIER_KEY,
        value_key = VALUE_KEY,
        slot_count = 2))

solution = combined_group.flatten_to_solution(max_weight_cost=MAX_WEIGHT_COST, extra_weight_cost=EXTRA_WEIGHT_COST)
print(f"optimal sets for {VALUE_KEY}: {len(solution)}")
top_ten = solution.best_for_load_percentage(0.25, count=10)
for entry in top_ten:
    print(entry)

exit(1)

# test
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

