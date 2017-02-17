#! /usr/bin/env python

"""Sieve a TSV file.

Filter a tab-separated text file by a certain column and a list of values
of the column to keep (or to skip, -r/--reverse option).
"""

import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sieve a TSV file.", add_help=False,
        usage="\n\t%(prog)s OPTIONS TSV\nor\t... | %(prog)s OPTIONS --pipe"
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "intsv", metavar="TSV", type=argparse.FileType("r"), nargs="?",
        help="input TSV file"
    )
    input_group.add_argument(
        "-p", "--pipe", action="store_true",
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "-o", "--out", dest="outsv", metavar="FILE",
        type=argparse.FileType("w"), default=sys.stdout,
        help="output TSV file, default is STDOUT"
    )
    parser.add_argument(
        "-r", "--reverse", action="store_true", help="reverse the filter"
    )
    parser.add_argument(
        "-n", "--no-title", dest="title", action="store_false",
        help="do not treat the first line as title"
    )
    parser.add_argument(
        "-c", "--column", metavar="N", type=int, default=0,
        help="index of the column to filter by, default 0"
    )
    set_group = parser.add_mutually_exclusive_group(required=False)
    set_group.add_argument(
        "-v", "--value", metavar="STR", action="append",
        help="a list of values to filter with"
    )
    set_group.add_argument(
        "-l", "--list", type=argparse.FileType("r"),
        default=sys.stdin, help="input file with a list of values"
    )
    parser.add_argument(
        "-d", "--delimiter", metavar="STR",
        help="delimiter for the list of values, default is a whitespace"
    )
    parser.add_argument(
        "-h", "-H", "-?", "--help", action="help", help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)

if __name__ == "__main__":
    sys.exit(main())

