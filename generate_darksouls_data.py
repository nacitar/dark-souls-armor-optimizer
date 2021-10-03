#!/usr/bin/env python3
from pathlib import Path
from filter_raymondhill_source_csv import filter_csv


def main():
    script_directory = Path(__file__).resolve().parent
    source_directory = Path(script_directory, "source-data")
    output_directory = Path(script_directory, "generated-data")

    base_output_directory = Path(output_directory, "base")
    base_csv_filename = "raymondhill-darksouls-armor-stats-0.csv"

    upgraded_output_directory = Path(output_directory, "upgraded")
    upgraded_csv_filename = "raymondhill-darksouls-armor-stats-10.csv"
    # base and rings
    output_directory.mkdir(exist_ok=True)
    filter_csv(
        output_directory=output_directory,
        input_path=Path(source_directory, base_csv_filename),
        json_paths=[
            Path(source_directory, "sevaht-darksouls-ring-stats.json")
        ],
    )
    base_output_directory.mkdir(exist_ok=True)
    Path(output_directory, base_csv_filename).rename(
        Path(base_output_directory, base_csv_filename)
    )
    # upgraded
    upgraded_output_directory.mkdir(exist_ok=True)
    filter_csv(
        output_directory=upgraded_output_directory,
        input_path=Path(source_directory, upgraded_csv_filename),
    )


if __name__ == "__main__":
    main()
