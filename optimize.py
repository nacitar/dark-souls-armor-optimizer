#!/usr/bin/env python3

import logging
logging.basicConfig(
        level=logging.WARNING,
        format='%(name)-12s: [%(levelname)-8s] %(message)s')

from knapsack import *

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

