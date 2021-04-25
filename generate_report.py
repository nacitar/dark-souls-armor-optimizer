#!/usr/bin/env python3

# requires python 3.7+ for dicts being in insertion order

from enum import Enum, auto
from collections import defaultdict
import json
import bisect

CHARACTER_CLASS_STATS_JSON = 'darksouls-character-classes.json'
EQUIPMENT_STATS_JSON = 'darksouls-equipment-stats-10.json'
WEIGHT_KEY = 'weight'
VALUE_KEY = 'physical'
EQUIPMENT_TYPES = ['Head', 'Torso', 'Arms', 'Legs' ]



with open(CHARACTER_CLASS_STATS_JSON, 'r') as handle:
    CHARACTER_CLASSES = json.load(handle)

with open(EQUIPMENT_STATS_JSON, 'r') as handle:
    ALL_EQUIPMENT_STATS = json.load(handle)

# Prune out pieces that are dominated by another.

# process equipment lowest weight to highest
# store the highest value retrieved

def ordered_by_named_numeric_values(
        section, weighted_value_keys, combine=False):
    weighted_value_keys = [
            (entry, 1.0) if isinstance(entry, str)
            else (entry[0], 1.0) if len(entry) == 1
            else entry
            for entry in weighted_value_keys]
    sum_if = lambda iterable, enabled: sum(iterable) if enabled else iterable
    return sorted(
            section.items(),
            key=lambda item: sum_if([
                item[1][weighted_value_key[0]] * weighted_value_key[1]
                for weighted_value_key in weighted_value_keys],
                enabled=combine))

# TODO: offset weight of items that modify equip load using character info
def without_dominated_equipment(equipment_section, value_key, weight_key,
        debug=False):
    highest_value = None
    pruned_section = {}
    for name, stats in ordered_by_named_numeric_values(
            equipment_section,
            # weight lowest to highest, value is highest to lowest
            weighted_value_keys=[weight_key, (value_key, -1.0)]):
        value = stats[value_key]
        weight = stats[weight_key]
        if highest_value is not None:
            if (value < highest_value
                    or value == highest_value and weight > last_weight):
                if debug:
                    print(f"{name} is dominated by {last_name}.")
                continue
            elif value == highest_value and weight == last_weight:
                if debug:
                    print(f"{name} is an equal alternative to {last_name}"
                            + f" with a {value_key} value of {value}.")
                pruned_section[last_weight]['alternative'].append(name)
                continue
        highest_value = value
        last_weight = weight
        if debug:
            last_name = name
            print(f"Adding: {stats[weight_key]} {name}")
        new_stats = stats.copy()
        new_stats['name'] = name
        new_stats.setdefault('alternative', [])
        # weight is still in the stats too
        pruned_section[new_stats[weight_key]] = new_stats
    return pruned_section

equipment_stats = { equipment_type: without_dominated_equipment(
    equipment_section, weight_key=WEIGHT_KEY, value_key=VALUE_KEY)
    for equipment_type, equipment_section in ALL_EQUIPMENT_STATS.items() }

# NOTE: in python 3.7 the order is likely already this one
for equipment_type in EQUIPMENT_TYPES:
    for weight, stats in ordered_by_named_numeric_values(
            equipment_stats[equipment_type],
            weighted_value_keys=[WEIGHT_KEY]):
        print(f"{equipment_type} {stats[WEIGHT_KEY]} {stats[VALUE_KEY]} "
                + " | ".join([stats['name']] + stats.get('alternative', [])))
# the above loop prints equipment from the lowest weight to the highest,
# showing the best choice possible for a given weight.


def get_best_piece_for_weight(sorted_weights, weight):
    index = bisect.bisect_right(sorted_weights, weight) - 1
    if index == -1:
        return None
    return sorted_weights[index]





exit(1)


max_weight = 30 - 2
current_weight = 0
current_value = 0
current_equipment = []
sorted_weights = []



# get the best piece possible for the first slot, then continue with what's
# left just to get a baseline starting point.
for equipment_type in EQUIPMENT_TYPES:
    equipment_section = equipment_stats[equipment_type]
    sorted_weights.append(list(sorted(equipment_section.keys())))
    best_key = get_best_piece_for_weight(
            sorted_weights[-1], max_weight - current_weight)
    if best_key is None:
        current_equipment.append(None)
    else:
        piece = equipment_section[best_key]
        current_equipment.append(piece)
        current_weight += piece[WEIGHT_KEY]
        current_value += piece[VALUE_KEY]

print(current_weight, current_value)
for index, piece in enumerate(current_equipment):
    # see if there's an improvement to be made, then see if the other slots can cover it
    if piece[WEIGHT_KEY] == sorted_weights[index][-1]:
        # already the best of this type
        pass
        print(f"Already the best {equipment_type}")
print(current_weight, current_value)


exit(1)

count=0
for helmet in equipment_stats['Head'].keys():
    for torso in equipment_stats['Torso'].keys():
        for arms in equipment_stats['Arms'].keys():
            for legs in equipment_stats['Legs'].keys():
                count+=1
print(f"{count} permutations")
exit(1)

character_class = 'Pyromancer'
settings = EquipmentOptimizerSettings(
        armor_statistics = ARMOR_STATISTICS,
        endurance = CLASS_STATISTICS[character_class]['endurance'],
        weapons_weight = 2.0)


