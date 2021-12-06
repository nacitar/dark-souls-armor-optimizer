#!/usr/bin/env python3

import argparse
import csv
import os
from typing import Optional, Sequence, Union


def quote_csv_strings(input_path: os.PathLike, output_path: os.PathLike):
    with open(input_path, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise RuntimeError("No field names retrieved from input file.")
        with open(output_path, mode="w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=reader.fieldnames,
                quoting=csv.QUOTE_NONNUMERIC,
            )
            writer.writeheader()
            for row in reader:
                converted_row: dict[str, Union[str, float]] = {}
                for field, value in row.items():
                    try:
                        converted_row[field] = float(value)
                    except ValueError:
                        # leave it as a string
                        converted_row[field] = value
                writer.writerow(converted_row)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Converts unquoted csv files into quoted ones."
    )
    parser.add_argument("input_csv_path", help="The csv file to convert.")
    parser.add_argument("output_csv_path", help="The csv file to output.")
    args = parser.parse_args(args=argv)
    quote_csv_strings(args.input_csv_path, args.output_csv_path)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
