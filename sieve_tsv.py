#! /usr/bin/env python

"""Sieve a TSV file.

Filter a TSV file by a certain column and a list of values
of the column to keep (or to skip, -r/--reverse option).
"""

import argparse
import signal
import sys


def float_perc(float_str):
    if float_str.endswith("%"):
        return float(float_str[:-1]) * 0.01
    return float(float_str)

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sieve a TSV file.", add_help=False,
        epilog="""If neither of -v, -l, --lt, --gt, --le, --ge is specified,
        STDIN will be used as the LIST. The TSV should be passed by name
        in the case."""
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
    set_group.add_argument(
        "--lt", dest="cutoff", metavar="FLOAT",
        type=lambda val: (float.__lt__, float_perc(val)),
        help="keep lines with a value lower than the cutoff"
    )
    set_group.add_argument(
        "--gt", dest="cutoff", metavar="FLOAT",
        type=lambda val: (float.__gt__, float_perc(val)),
        help="keep lines with a value greater than the cutoff"
    )
    set_group.add_argument(
        "--le", dest="cutoff", metavar="FLOAT",
        type=lambda val: (float.__le__, float_perc(val)),
        help="keep lines with a value lower than or equal to the cutoff"
    )
    set_group.add_argument(
        "--ge", dest="cutoff", metavar="FLOAT",
        type=lambda val: (float.__ge__, float_perc(val)),
        help="keep lines with a value greater than or equal to the cutoff"
    )
    parser.add_argument(
        "-d", "--delimiter", metavar="STR",
        help="delimiter for the list of values, default is a whitespace"
    )
    parser.add_argument(
        "-h", "-H", "-?", "--help", action="help", help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)
    index = args.column
    split_num = index + 1
    values = set(args.value or [])
    reverse = args.reverse
    if args.cutoff is not None:
        cutoff_method, cutoff = args.cutoff
        check = lambda row: cutoff_method(float_perc(row[index]), cutoff)
    else:
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
        check = lambda row: row[index] in values
        if len(values) == 1:
            value = values.pop()
            check = lambda row: row[index] == value
    with args.intsv as intsv, args.outsv as outsv:
        _wait_title = True
        for line in intsv:
            if line.startswith("#"):
                if line.startswith("#:") and _wait_title:
                    outsv.write(line)
                    _wait_title = False
                continue
            _wait_title = False
            row = line.strip("\n").split("\t", split_num)
            if check(row) != reverse:
                outsv.write(line)


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

