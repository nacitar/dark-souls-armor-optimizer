#!/usr/bin/env python3

import json
import csv
import os
from pathlib import Path

# just for documentation
SOURCE_URL = "http://www.raymondhill.net/darksouls/darksouls-armor-calc.php"

REMOVED_KEYS = ["url1", "location"]
FIRST_KEYS = ["set", "position", "name"]
POSITION_NAMES = ["Head", "Torso", "Arms", "Legs"]
REQUIRED_JSON_KEYS = ["position", "name"]
BASE_STATS_ITEM = "Naked Head"


def filter_csv(
    output_directory: os.PathLike,
    input_path: os.PathLike,
    json_paths: list[os.PathLike] = [],
):
    input_basename = Path(input_path).stem
    output_path = Path(output_directory, f"{input_basename}.csv")
    with open(input_path, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise RuntimeError("No field names retrieved from input file.")

        # add extra fields
        field_names = sorted(reader.fieldnames) + [
            "weight_modifier",
            "health_modifier",
            "stamina_modifier",
            "stamina_regeneration",
        ]
        # remove undesired keys, and move others to the front
        for key in FIRST_KEYS + REMOVED_KEYS:
            field_names.remove(key)
        field_names = FIRST_KEYS + field_names

        base_stats = None
        with open(output_path, mode="w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()
            for row in reader:
                position = POSITION_NAMES[int(row["position"]) - 1]
                set_name = row["set"]
                for suffix in [" Set", "'s"]:
                    set_name = set_name.removesuffix(suffix)
                for prefix in ["Set of the ", "Set of "]:
                    set_name = set_name.removeprefix(prefix)
                if set_name == "Shiny Brass":
                    set_name = "Brass"

                for key in REMOVED_KEYS:
                    del row[key]

                weight_modifier = "0"
                health_modifier = "0"
                stamina_modifier = "0"
                stamina_regeneration = "0"

                if row["name"] == "Mask of the Father":
                    weight_modifier = "0.05"  # +5%
                elif row["name"] == "Mask of the Mother":
                    health_modifier = "0.1"  # +10%
                elif row["name"] == "Mask of the Child":
                    stamina_regeneration = "10"

                # store back the fixed values
                row["set"] = set_name
                row["position"] = position
                row["weight_modifier"] = weight_modifier
                row["health_modifier"] = health_modifier
                row["stamina_modifier"] = stamina_modifier
                row["stamina_regeneration"] = stamina_regeneration

                writer.writerow(row)
                if row["name"] == "Naked Head":
                    # already written out, we can now store and modify this
                    base_stats = row
                    for key in REQUIRED_JSON_KEYS + ["set"]:
                        base_stats[key] = ""
        if not base_stats:
            raise RuntimeError(
                f"No base stats retrieved from: {BASE_STATS_ITEM}"
            )
        for json_path in json_paths:
            input_basename = Path(json_path).stem
            output_path = Path(output_directory, f"{input_basename}.csv")
            with open(json_path, "r") as jsonfile:
                data = json.load(jsonfile)
                with open(output_path, mode="w", newline="") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=field_names)
                    writer.writeheader()
                    for name, stats in data.items():
                        stats["name"] = name
                        for key in REQUIRED_JSON_KEYS:
                            if not stats[key]:
                                raise RuntimeError(
                                    f"JSON item {name} has no field {key}"
                                )
                        row = base_stats.copy()
                        row.update(stats)
                        writer.writerow(row)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=f"Filters the source csv files from {SOURCE_URL}"
    )
    parser.add_argument(
        "output_directory", help="The directory in which to place the results."
    )
    parser.add_argument("input_csv_path", help="The csv file to filter.")
    parser.add_argument(
        "input_json_path", nargs="*", help="Extra json files to process."
    )
    args = parser.parse_args()
    filter_csv(
        args.output_directory, args.input_csv_path, args.input_json_path
    )
