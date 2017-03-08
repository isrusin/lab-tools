#! /usr/bin/env python

"""Sieve a TSV file.

Filter a tab-separated text (TSV) file by a certain column and a list
of values of the column to keep (or to skip, -r/--reverse option).
"""

import argparse
import signal
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sieve a TSV file.", add_help=False,
        epilog="""If neither -v nor -l is specified, STDIN will be used
        as the LIST. The TSV should be passed by name in the case."""
    )
    parser.add_argument(
        "intsv", metavar="TSV", type=argparse.FileType("r"), nargs="?",
        default=sys.stdin, help="input TSV file, default is STDIN"
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
        "-l", "--list", dest="inlist", metavar="LIST",
        type=argparse.FileType("r"), default=sys.stdin,
        help="input file with a list of values"
    )
    parser.add_argument(
        "-d", "--delimiter", metavar="STR",
        help="delimiter for the list of values, default is a whitespace"
    )
    parser.add_argument(
        "-h", "-H", "-?", "--help", action="help", help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)
    values = set(args.value or [])
    if not values:
        if args.inlist.name == "<stdin>":
            if args.intsv.name == "<stdin>":
                sys.stderr.write(
                    "Error! Both the TSV and the LIST are STDIN!\n"
                )
                parser.print_usage(sys.stderr)
                return 1
        with args.inlist as inlist:
            values = set(inlist.read().strip().split(args.delimiter))
    index = args.column
    split_num = index + 1
    check = lambda row: row[index] in values
    if len(values) == 1:
        value = values.pop()
        check = lambda row: row[index] == value
    reverse = args.reverse
    with args.intsv as intsv, args.outsv as outsv:
        if args.title:
            outsv.write(intsv.readline())
        for line in intsv:
            row = line.strip().split("\t", split_num)
            if check(row) != reverse:
                outsv.write(line)


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

