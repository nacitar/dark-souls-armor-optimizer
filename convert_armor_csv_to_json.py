#!/usr/bin/env python3

import json
import csv

ARMOR_STATS_CSV = 'source/darksouls-armor-stats-10.csv'

def parse_csv_with_headings(handle):
    field_names = []
    first = True
    for row in csv.reader(handle):
        statistics = {}
        if not first and len(row) != len(field_names):
            raise RuntimeError(f"Row field count({len(row)}) doesn't match column "
                    + f"heading count({len(field_names)}) for row: "
                    + str(row))
        for index, cell in enumerate(row):
            if first:
                # column headings
                field_names.append(cell)
            else:
                statistics[field_names[index]] = cell
        if not first:
            yield statistics
        else:
            first = False

def convert_armor_csv_to_json(in_csv_filename, out_json_filename):
    armor_stats = {}
    with open(in_csv_filename, 'r') as handle:
        for entry in parse_csv_with_headings(handle):
            slot = ['Head', 'Torso', 'Arms', 'Legs'][int(entry['position']) - 1]

            if slot in armor_stats:
                slot_entries = armor_stats[slot]
            else:
                slot_entries = {}
                armor_stats[slot] = slot_entries

            del entry['position']
            name = entry['name']
            del entry['name']
            entry['poise'] = int(entry['poise'])
            for field in ['weight', 'physical', 'magic', 'fire', 'lightning',
                    'bleed', 'poison', 'curse']:
                entry[field] = float(entry[field])
            if name == "Mask of the Father":
                entry['weight_modifier'] = 1.05  # +5%
            else:
                entry['weight_modifier'] = 1.00
            slot_entries[name] = entry

    with open(out_json_filename, 'w') as outfile:
        json.dump(armor_stats, outfile, indent=4, sort_keys=True)

convert_armor_csv_to_json(ARMOR_STATS_CSV, "output.json")
