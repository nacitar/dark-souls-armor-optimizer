import importlib.resources
import pkgutil
import itertools
from typing import Optional, Iterable, Generator, Union, TextIO
from pathlib import Path
from os import PathLike
import re
import json
import csv

# TODO: error handling


def as_package_name(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower())


def iterate_lines(value: str) -> Generator[str, None, None]:
    return (
        line.group(0) for line in re.finditer(r"[^\n]*\r?\n|[^\n]+$", value)
    )


def open_csv(path: Union[str, PathLike[str]]) -> TextIO:
    """
    Simple wrapper around open() that forces newline="" as required by
    the builtin csv library.
    """
    return open(path, mode="r", newline="")


def iterate_csv(
    *,
    file: Optional[TextIO] = None,
    content: Optional[str] = None,
) -> Generator[dict[str, str], None, None]:
    """
    Any file passed to the file argument must be opened with newline="".
    """
    if file is not None:
        for row in csv.DictReader(file):
            yield row
    if content is not None:
        for row in csv.DictReader(iterate_lines(content)):
            yield row


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
    data_sets: Optional[set[str]] = None,
    is_resource: bool = False,
) -> Generator[Path, None, None]:
    if data_sets is None:
        data_sets = set()
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


# TODO: test
# print(list(get_csv_files("dark_souls", data_sets=["upgraded"])))
