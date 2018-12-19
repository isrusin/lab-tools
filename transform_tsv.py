#! /usr/bin/env python

"""Transform TSV by compressing/uncompressing a certain column."""

import argparse
from itertools import chain
import signal
import sys


FIRST_PLACE = 0
NATIVE_PLACE = 1
LAST_PLACE = 2


class LineParser(object):
    def __init__(self, before_indices, after_indices, target_index):
        self.before_indices = before_indices
        self.after_indices = after_indices
        self.target_index = target_index

    def __call__(self, line):
        before_vals = []
        after_vals = []
        vals = before_vals
        indices = self.before_indices
        for i, val in enumerate(line.split("\t")):
            if i == self.target_index:
                vals = after_vals
                indices = self.after_indices
                target_val = val
            elif i in indices:
                vals.append(val)
        return (tuple(before_vals), tuple(after_vals)), target_val


def parse_index_set(set_str, target_index, max_index):
    ranges = set_str.split(",")
    before = set()
    after = set()
    for range_str in ranges:
        if not range_str:
            raise ValueError("Empty index range")
        if ":" in range_str:
            begin, end = range_str.split(":")
            begin = int(begin) if begin else 0
            end = int(end) if end else max_index
            if begin < 0:
                begin += max_index + 1
            if end < 0:
                end += max_index + 1
            while begin < target_index:
                before.add(begin)
                begin += 1
            while begin <= end:
                after.add(begin)
                begin += 1
        else:
            index = int(range_str)
            if index < 0:
                index += max_index + 1
            if index < target_index:
                before.add(index)
            elif index > target_index:
                after.add(index)
    return (tuple(sorted(before)), tuple(sorted(after)))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Transform TSV by [un]compressing a certain column.",
        add_help=False
    )
    io_group = parser.add_argument_group("Input/output arguments")
    io_group.add_argument(
        "intsv", metavar="TSV", type=argparse.FileType("r"),
        help="input TSV file"
    )
    io_group.add_argument(
        "-o", dest="outsv", metavar="TSV", type=argparse.FileType("w"),
        default=sys.stdout, help="output TSV file, default STDOUT"
    )
    io_group.add_argument(
        "-r", "--decompress", dest="compress", action="store_false",
        help="decompress the target column, default is to compress it"
    )
    index_group = parser.add_argument_group("Column indices")
    index_group.add_argument(
        "-T", "--target-column", dest="target_index", metavar="N",
        type=int, default=0, help="index of the target column"
    )
    index_group.add_argument(
        "-K", "--kept-columns", dest="kept_indices", metavar="SET",
        default=":", help="""indices of columns that should be kept,
        all columns are kept by default; RANGE is a comma separated
        list of column indices or index ranges (use ':'), for example
        ':3,5,7:'; the target column will be kept anyway"""
    )
    option_group = parser.add_argument_group("Other options")
    option_group.add_argument(
        "-p", "--position", default="native",
        choices=["F", "first", "N", "native", "L", "last"],
        help="output position of the target column, default is native"
    )
    option_group.add_argument(
        "-d", "--delimiter", metavar="STR", default=",",
        help="inner delimiter of the target column, default is comma"
    )
    option_group.add_argument(
        "-s", "--skip-value", metavar="STR",
        help="which target column values to skip"
    )
    parser.add_argument(
        "-?", "-h", "-help", "--help", action="help",
        help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)
    target_place = {
        "F": FIRST_PLACE, "first": FIRST_PLACE,
        "N": NATIVE_PLACE, "native": NATIVE_PLACE,
        "L": LAST_PLACE, "last": LAST_PLACE
    }[args.position]
    to_compress = args.compress
    skip_value = args.skip_value
    delimiter = args.delimiter
    target_index = args.target_index
    index_set = args.kept_indices
    metadata = []
    data = []
    title = None
    with args.intsv as intsv:
        for line in intsv:
            if line.startswith("#"):
                if line.startswith("##"):
                    metadata.append(line)
                elif line.startswith("#:") and title is None:
                    title = line.rstrip("\n")
            else:
                data.append(line.rstrip("\n"))
    sample_line = data[0] if data else title
    if not sample_line:
        return 1
    max_index = len(sample_line.split("\t")) - 1
    if target_index < 0:
        target_index += max_index + 1
    if target_index < 0 or target_index > max_index:
        parser.error("Target index is out of range.")
    try:
        before_indices, after_indices = parse_index_set(
            index_set, target_index, max_index
        )
    except ValueError:
        parser.error("An error in the set of kept column indices.")
    line_parser = LineParser(before_indices, after_indices, target_index)
    compressed = dict()
    oudata = []
    while data:
        line = data.pop(0)
        key, value = line_parser(line)
        if value == skip_value:
            continue
        if to_compress:
            compressed.setdefault(key, set()).add(value)
        else:
            for item in value.split(delimiter):
                oudata.append((key, item))
    if compressed:
        oudata = sorted(
            (k, delimiter.join(sorted(v))) for k, v in compressed.items()
        )
    if title:
        oudata.insert(0, line_parser(title))
    with args.outsv as outsv:
        outsv.writelines(metadata)
        for vals, target_val in oudata:
            vals = list(vals)
            vals.insert(target_place, (target_val, ))
            outsv.write("\t".join(chain(*vals)) + "\n")


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

