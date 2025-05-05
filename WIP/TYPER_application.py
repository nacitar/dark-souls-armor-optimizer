# requires 3.9+ (for mypy dict/tuple instead of Dict/Tuple)
from typing import Optional, Sequence, Set, Any
import logging
import argparse
import re
from pathlib import Path
from typer import Option, run
from typer.models import OptionInfo
from inspect import signature
import inspect
import functools

LOG = logging.getLogger(__name__)

# TODO:
#   fix Traveling Gloves in data
#       really, need to get a new data dump because it's missing fields.
# - mypy doesn't deduce the type of argparse arguments


def main():
    run(typer_main)

def set_defaults(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Backup original function defaults.
        original_defaults = f.__defaults__

        # Replace every `Default("...")` argument with its current value.
        function_defaults = []
        import pdb
        pdb.set_trace()
        for default_value in f.__defaults__:
            if isinstance(default_value, OptionInfo):
                function_defaults.append(defaults_value.default)
            else:
                function_defaults.append(default_value)

        # Set the new function defaults.
        f.__defaults__ = tuple(function_defaults)

        return_value = f(*args, **kwargs)

        # Restore original defaults (required to keep this trick working.)
        f.__defaults__ = original_defaults

        return return_value

    return wrapper

def typer_wrapper(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    # NOTE: this doesn't seem to actually work
    wrapper.__kwdefaults__ = {
        key: default_value.default if is_option else default_value
        for key, default_value in f.__kwdefaults__.items()
        if not (is_option := isinstance(default_value, OptionInfo)) or default_value.default is not ...
        }
    wrapper.__defaults__ = tuple([
            default_value.default if isinstance(default_value, OptionInfo) else default_value
            for default_value in (f.__defaults__ or ())])

    #sig = inspect.signature(wrapper)
    #parameters = list(sig.parameters.values())
    #wrapper.__signature__ = sig.replace(parameters = parameters)

    #import pdb
    #pdb.set_trace()
    return wrapper

def typer_main(
    *,
    game: str = Option(
        "Dark Souls",
        "-g",
        "--builtin-game",
        help=(
            "The name of the built-in game whose data will be used."
            "  Ignored if input directory is specified."
        ),
    ),
    input_directory: Optional[Path] = Option(
        None,
        "-i",
        "--input-directory",
        help=(
            "A directory with custom csv files whose data will be used"
            " instead of those of a builtin game."
        ),
    ),
    data_sets: Optional[list[str]] = Option(
        None,
        "-d",
        "--data-set",
        help="The name of a data set to use in addition to common data.",
    ),
    maximize: list[str] = Option(
        ..., "-m", "--maximize", help="Fields to maximize in the output."
    ),
    name_field: str = Option(
        "name", help="The name of the field holding the name of the piece."
    ),
    position_field: str = Option(
        "position",
        help="The name of the field holding the position of the piece.",
    ),
    weight_field: str = Option(
        "weight", help="The name of the field holding the weight of the piece."
    ),
    weight_modifier_field: str = Option(
        "weight_modifier",
        help="The name of the field holding the weight modifier of the piece.",
    ),
    set_field: str = Option(
        "set",
        help="The name of the field holding the name of the piece's set.",
    ),
    exclude_sets: Optional[list[str]] = Option(
        None,
        "--exclude-set",
        help="The name of sets to exclude from the data.",
    ),
    exclude_pieces: Optional[list[str]] = Option(
        None,
        "--exclude-piece",
        help="The name of pieces to exclude from the data.",
    ),
    fields: Optional[list[str]] = Option(
        None, "-f", "--field", help="Fields to include in the output."
    ),
    no_fields: bool = Option(
        False, "-n", "--no-fields", help="Include no fields in the output."
    ),
    verbose: bool = Option(
        False, "-v", "--verbose", help="Increase output verbosity"
    ),
) -> int:
    print(dict(**locals()))
    return 0

other_main = typer_wrapper(typer_main)

other_main()
import pdb
pdb.set_trace()
#other_main(maximize=["moo"])
#run(other_main)
#typer_main(maximize=["moo"])
