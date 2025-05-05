#!/usr/bin/env python3
import dataclasses
import typing
from typing import Any, Type, Callable, Optional
from dataclasses import dataclass
import sys


@dataclass
class Options:
    set_things: set[str]
    list_things: list[str]
    foo: int = 5


def set_inserter(obj: set[Any], value):
    obj.add(value)


def list_inserter(obj: list[Any], value):
    obj.append(value)


@dataclass
class OptionInfo:
    attribute_name: str
    value: Any
    inserter: Callable[[Any, Any], None]


options: dict[str, Any] = {}


# custom actions for everything, specifically to get it to write the value to the right class?
argparse_lookup = {}

for field in dataclasses.fields(Options):
    origin = typing.get_origin(field.type)
    if origin is not None:
        if origin in (set, list):
            if origin is set:
                pass  # TODO

        origin = None  # TODO
    if origin is set:
        type_args = typing.get_args(field.type)

    options[f"--{field.name.replace('_','-')}"] = OptionInfo(
        attribute_name=field.name, value=field.type(), inserter=set_inserter
    )
    print(typing.get_origin(field.type) is set)

print(options)

ctor_args: dict[str, Any] = {}
current_arg: str = ""
option_info: Optional[OptionInfo] = None
for arg in sys.argv[1:]:
    print(f"ARG: {arg}")
    if arg.startswith("--"):
        option_info = options[arg]
        continue
    option_info.inserter(option_info.value, arg)
    print(option_info)
