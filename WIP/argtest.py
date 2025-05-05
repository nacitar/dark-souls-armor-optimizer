#!/usr/bin/env python3

import argparse


class customAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        setattr(args, self.dest, set(values))


parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("-e", "--example", action=customAction, nargs="*")
args = parser.parse_args()

print(repr(args.example))
