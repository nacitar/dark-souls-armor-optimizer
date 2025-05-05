#!/usr/bin/env python3
from tap import Tap
from typing import Optional
from dataclasses import dataclass


class SimpleArgumentParser(Tap):
    game: str
    messages: Optional[set[str]] = None
    language: str = "Python"  # Programming language

    def __init__(self):
        super().__init__(underscores_to_dashes=True)

    def process_args(self):
        if self.game and self.messages:
            pass
            # raise ValueError('Cool packages cannot have fewer than 4 stars')


parser = SimpleArgumentParser()
args = parser.parse_args()

print(args)
print(type(args))
print(dir(args))
