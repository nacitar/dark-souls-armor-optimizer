#!/usr/bin/env python3
from typing import Optional, Sequence, Type
from dataclasses import dataclass
from simple_parsing import ArgumentParser
from simple_parsing.utils import Dataclass
from pathlib import Path


def parse(
    type: Type[Dataclass],
    dest: str,
    *,
    arguments: Optional[Sequence[str]] = None
) -> Dataclass:
    parser = ArgumentParser(add_option_string_dash_variants=True)
    parser.add_arguments(type, dest=dest)
    return getattr(parser.parse_args(args=arguments), dest)


@dataclass
class Options:
    maximize: list[str]
    """Fields to maximize in the output."""
    game: str = "Dark Souls"
    """The name of the game whose data will be used.
    Ignored if input directory is specified."""
    exclude_sets: Optional[list[str]] = None
    """The name of sets to exclude from the data."""
    exclude_pieces: Optional[list[str]] = None
    """The name of pieces to exclude from the data."""
    fields: Optional[list[str]] = None
    """Fields to include in the output."""
    data_sets: Optional[list[str]] = None
    """The name of any data sets to use in addition to common data."""
    input_directory: Optional[Path] = None
    """A directory with custom csv files to be used instead of any
    builtin game data."""
    name_field: str = "name"
    """The name of the field holding the name of the piece."""
    position_field: str = "position"
    """The name of the field holding the position of the piece."""
    weight_field: str = "weight"
    """The name of the field holding the weight of the piece."""
    weight_modifier_field: str = "weight_modifier"
    """The name of the field holding the weight modifier of the piece."""
    set_field: str = "set"
    """The name of the field holding the name of the piece's set."""
    verbose: bool = False
    """Increase output verbosity"""


options = parse(Options, "options")

print(options)
