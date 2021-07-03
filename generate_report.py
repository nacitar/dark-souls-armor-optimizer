#!/usr/bin/env python3

# Requires python 3.8+ for assignment expressions

import json
import bisect
import itertools
import functools

import collections

# TODO:
# - store the maximum weight modifier for a given slot
# - When pruning, know the highest possible modifier for all remaining slots
#   - How do you know?  You need to know this information while pruning, so
#     this means scanning the input data before pruning.
#   - This means knowing the full slot set prior to pruning.
#   - Prune out things that couldn't possibly be worn because they are too heavy
#     by themselves, even with the highest of all possible modifiers in the other
#     slots.  DONT FORGET THE MODIFIER OF THE ITEM TO BE PRUNED, EITHER!
#   - Would need to know the player equip load and any extra weight during pruning.
# - If presenting items to exclude, weight modifying items should be near the top
#   of the list, because they reduce complexity greatly when removed.
# - The lowest modifier doesn't seem useful.
# - This won't change much with high equip load, but for constrained loads
#   it should be able to prune out a ton of things.

# A weight that incorporates a modifier
@functools.total_ordering
class KnapsackWeight(object):
    def __init__(self, cost, modifier = 1.0):
        self.cost = cost
        self.modifier = modifier

    def has_modifier(self):
        return (self.modifier != 1.0)

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
        if isinstance(other, type(self)):
            # sort by cost then inverted modifier.  smallest cost, largest modifier.
            return (self.cost < other.cost or
                self.cost == other.cost and self.modifier > other.modifier)
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, type(self)):
            return KnapsackWeight(
                    cost = self.cost + other.cost,
                    modifier = self.modifier * other.modifier)
        return NotImplemented

    def __str__(self):
        if not self.has_modifier():
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
        if not isinstance(name, tuple) and name is not None:
            name = (name,)
        self.name = name
        if alternatives is None:
            alternatives = set()
        self.alternatives = alternatives

    def has_weight_modifier(self):
        return (self.weight.modifier != 1.0)

    def without_weight_modifiers(self, max_weight_cost, extra_weight_cost):
        if not extra_weight_cost and not self.weight.has_modifier():
            return self
        return type(self)(
                weight = KnapsackWeight(
                        # convert the cost into a percentage of the weight
                        cost = (self.weight.cost + extra_weight_cost) / (max_weight_cost * self.weight.modifier),
                        modifier = 1.0),
                value = self.value,
                name = self.name,
                alternatives = self.alternatives)

    def __add__(self, other):
        return type(self)(
                weight = self.weight + other.weight,
                value = self.value + other.value,
                # filter None out so special items that are
                # unnamed could be used to make new items from existing
                # ones with adjusted values. Also needed for supporting
                # type(self).ZERO
                name = sum(filter(None, (self.name, other.name)), ()),
                alternatives = set(itertools.chain(self.alternatives, other.alternatives)))

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
# Static members
KnapsackItem.ZERO = KnapsackItem(weight = 0.0, value = 0.0, name=None)

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
    def __init__(self, items=None, sort=True):
        if not isinstance(items, list):
            raise TypeError("items must be a list(KnapSackItem)")
        if sort:
            items = sorted(items)
        self.items = { item.weight: item for item in items }
        self._sorted_weights = list(self.items.keys())

    def __len__(self):
        return len(self.items)

    def best_for_cost(self, cost, count=1):
        weight = KnapsackWeight(cost = cost)
        index = bisect.bisect_right(self._sorted_weights, weight) - 1
        if index == -1:
            return None
        end = index+1
        return [self.items[weight] for weight in reversed(self._sorted_weights[max(end - count, 0):end])]

# NOTE: count is a request; if there aren't enough items left after pruning to provide that many selections, less slots will be provided.
class KnapsackItemSlot(object):
    # ensures the items are sorted, unless they are to be
    # assumed already sorted because sort=False
    def __init__(self, items, count=1, allow_duplicates=False, sort=True, debug=0):
        self.debug = debug
        self._has_modifiers = False

        if isinstance(items, list):
            # dominance filter
            before_dominance = len(items)
            while True:
                if sort:
                    items = sorted(items)
                # after the first time we need to sort, because lexicographic order is
                # NOT the sorted order by combined weight.
                sort = True
                index = 0
                best_for_modifier_gte = BestKnapsackItemForModifierGTE()
                last_top_survivor = None
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
                    if (last_top_survivor is not None and item.value == last_top_survivor.value
                            and item.weight == last_top_survivor.weight):  # checks modifier too
                        dominated = lesser_item_count.get(last_top_survivor.name, 0) + 1
                        lesser_item_count[last_top_survivor.name] = dominated
                        alternative = True

                    if dominated > 0:
                        # Each particular item needs to have enough fallbacks to cover extra
                        # slots, so we track how many items each one has dominated to ensure
                        # we don't remove fallback options for once the dominant item has
                        # already been selected but there are more slots to go.  However,
                        # even if the item is ultimately kept as a fallback it isn't a
                        # "top" survivor, as it survived merely due to fallbacks.
                        if dominated + 1 > count:
                            if alternative:
                                if self.debug > 1:
                                    print(f"COMBINED: {item.name} is an equal alternative to {last_top_survivor.name}")
                                last_top_survivor.alternatives.add(item.name)
                            else:
                                if self.debug > 1:
                                    print(f"REMOVED: {item.name} is dominated by {possible_dominator.name}")
                            del items[index]
                            continue
                        else:
                            if self.debug > 1:
                                print(f"KEPT: {item.weight} {item.name} after comparing with {possible_dominator.name}")
                    else:
                        last_top_survivor = item
                        best_for_modifier_gte.add(item) 
                    if not self._has_modifiers and item.weight.has_modifier():
                        if self.debug:
                            print(f"MODIFIER: {item.name} {item.weight}")
                        self._has_modifiers = True
                    index += 1

                if self.debug > 0:
                    print(f"Entries removed due to being suboptimal: {before_dominance -len(items)}")
                possible_slots = min(len(items), count)
                if possible_slots > 1:
                    count = 1
                    if not allow_duplicates:
                        items = [ sum(items, KnapsackItem.ZERO)
                            for items in itertools.combinations(items, r = possible_slots) ]
                    else:
                        items = [ sum(items, KnapsackItem.ZERO)
                            for items in itertools.product(*([items]*possible_slots)) ]
                    continue  # run it again to reduce the combinations
                break
            # in sorted order
            self.items = items  #{ item.weight: item for item in items }
        else:
            raise TypeError("items must be a list(KnapSackItem)")

    def __len__(self):
        return len(self.items)

    def solution_by_weight_percentage(self, max_weight_cost, extra_weight_cost):
        if not self._has_modifiers and extra_weight_cost == 0.0:
            items = self.items
        else:
            without_weight_modifiers = type(self)(items = [ item.without_weight_modifiers(
                        max_weight_cost=max_weight_cost, extra_weight_cost=extra_weight_cost)
                        for item in self.items ])
            items = without_weight_modifiers.items
        # already sorted
        return KnapsackSolution(items = items, sort=False)

    def __add__(self, other):
        if isinstance(other, type(self)):
            return type(self)(
                        items = [first_item + second_item
                                    for first_item, second_item in itertools.product(
                                            self.items,
                                            other.items)])
        return NotImplemented

    @classmethod
    def combine_in_pairs(cls, slots):
        if isinstance(slots, cls):
            # single instance
            return slots
        slots = list(slots)

        while len(slots) > 1:
            slots_iter = iter(slots)
            # replace the slice, so that any extra slot without a pair
            # still sits at the end of the list
            slots[:len(slots) // 2 * 2] = [first_slot + second_slot
                    for first_slot, second_slot in zip(*[slots_iter] * 2)]
        return slots[0]

class EquipmentCollection(object):
    def __init__(self):
        self._sections = {}

    def keys(self):
        return self._sections.keys()

    def __getitem__(self, key):
        return self._sections[key]

    def add_raw_collection(self, data):
        for name, section in data.items():
            if name in self._sections:
                raise KeyError(f'Section {name} is already present within the collection.')
            defaults = section.get('defaults')
            if defaults is not None:
                self._sections[name] = {entry_name: collections.ChainMap(statistics, defaults)
                        for entry_name, statistics in section['entries'].items()}
            else:
                self._sections[name] = section['entries']

    def add_collection_json(self, path):
        with open(path, 'r') as handle:
            data = json.load(handle)
        self.add_raw_collection(data)

    # helper
    def __get_section_settings_defaults(self, name, count=1, allow_duplicates=False):
        return (self[name], count, allow_duplicates)

    def __get_section_settings(self, section_arg):
        if not isinstance(section_arg, tuple):
            section_arg = (section_arg,)
        return self.__get_section_settings_defaults(*section_arg)

    def to_knapsack_item_slot(self, sections, weight_key, weight_modifier_key, value_key):
        return KnapsackItemSlot.combine_in_pairs([
                KnapsackItemSlot(
                    items = [
                        KnapsackItem(
                            weight = KnapsackWeight(
                                # Assignment expression; python 3.8+
                                cost = (statistics := section[name])[weight_key],
                                modifier = statistics[weight_modifier_key]),
                            value = statistics[value_key],
                            name = name)
                        for name in section.keys() ],
                    count = count,
                    allow_duplicates = allow_duplicates)
                for section, count, allow_duplicates in map(self.__get_section_settings, sections)
                ])

##############################################################################

CHARACTER_CLASS_STATS_JSON = 'darksouls-character-classes.json'
#with open(CHARACTER_CLASS_STATS_JSON, 'r') as handle:
#    CHARACTER_CLASSES = json.load(handle)

EQUIPMENT_STATS_JSON = 'darksouls-equipment-stats-10.json'
RING_STATS_JSON = 'darksouls-ring-stats.json'
MAX_WEIGHT_COST = 51.0
#MAX_WEIGHT_PERCENT = 0.08333
#MAX_WEIGHT_PERCENT = 0.16667
MAX_WEIGHT_PERCENT = 0.25
EXTRA_WEIGHT_COST = 2.0  # weapons weight

equipment = EquipmentCollection()
equipment.add_collection_json(EQUIPMENT_STATS_JSON)
equipment.add_collection_json(RING_STATS_JSON)
#print(equipment['Arms']['Balder Gauntlets+10'])

settings = {
        'weight_key': 'weight',
        'weight_modifier_key': 'weight_modifier',
        'value_key': 'physical' }

combined_slot = equipment.to_knapsack_item_slot(
        sections=['Head', 'Torso', 'Arms', 'Legs', ('Fingers', 2, False)],
        **settings)

solution = combined_slot.solution_by_weight_percentage(
        max_weight_cost=MAX_WEIGHT_COST, extra_weight_cost=EXTRA_WEIGHT_COST)

print(f"optimal sets for {settings['value_key']}: {len(solution)}")
top_ten = solution.best_for_cost(MAX_WEIGHT_PERCENT, count=10)
for entry in top_ten:
    print(entry)

exit(0)


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

