import importlib.resources
import pkgutil
import itertools
from typing import Optional, Iterable, Generator, Union
from pathlib import Path
from os import PathLike
import re
import json

# TODO: error handling


def as_package_name(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower())


# NOTE: importlib.resources.contents requires an __init__.py to be present
def iterate_directory(
    path: Union[str, PathLike[str]], *, is_resource: bool = False
) -> Generator[Path, None, None]:
    path = Path(path)
    if is_resource:
        path = Path(*(as_package_name(part) for part in path.parts))
        return (
            Path(path, file)
            for file in importlib.resources.contents(
                ".".join(itertools.chain((__name__,), path.parts))
            )
        )
    else:
        return path.iterdir()


def get_csv_files(
    path: Union[str, PathLike[str]],
    *,
    data_sets: Optional[Iterable[str]] = None,
    is_resource: bool = False
) -> Generator[Path, None, None]:
    if data_sets is None:
        data_sets = []
    return (
        file
        for data_set in itertools.chain(("",), data_sets)
        for file in iterate_directory(
            Path(path, data_set), is_resource=is_resource
        )
        if file.suffix.lower() == ".csv"
    )


def get_resource_content(path: Union[str, PathLike[str]]) -> str:
    content = pkgutil.get_data(__name__, str(path))
    if content is not None:
        return content.decode(json.detect_encoding(content))
    return ""


def iterlines(value: str) -> Generator[str, None, None]:
    return (
        line.group(0) for line in re.finditer(r"[^\n]*\r?\n|[^\n]+$", value)
    )


def to_float(value: Union[str, float, int], default: float) -> float:
    try:
        return float(value)
    except ValueError:
        return default


# TODO: test
# print(list(get_csv_files("dark_souls", data_sets=["upgraded"])))