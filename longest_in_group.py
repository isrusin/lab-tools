#! /usr/bin/env python

"""Get ACs of the longest sequences grouped by certain IDs."""

import argparse
import signal
import sys


def load_dct(indct, value_type=str):
    vals = dict()
    with indct:
        for line in indct:
            if line.startswith("#"):
                continue
            key, value = line.strip().split("\t")
            vals[key] = value_type(value)
    return vals


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Get ACs of the longest sequences in groups."
    )
    parser.add_argument(
        "indct", metavar="GROUP_DICT", type=argparse.FileType("r"),
        help="input AC-to-GROUP dictionary"
    )
    parser.add_argument(
        "inlens", metavar="LENGTH_DICT", type=argparse.FileType("r"),
        help="input AC-to-LENGTH dictionary"
    )
    parser.add_argument(
        "-a", dest="inacvs", metavar="LIST", type=argparse.FileType("r"),
        help="input list of ACs to filter by"
    )
    parser.add_argument(
        "-o", dest="oufile", metavar="FILE", type=argparse.FileType("w"),
        default=sys.stdout, help="output file, default STDOUT"
    )
    parser.add_argument(
        "--dict", "--map", dest="return_dict", action="store_true",
        help="return GROUP-to-AC dictionary instead of AC list"
    )
    args = parser.parse_args(argv)
    groups = load_dct(args.indct)
    lens = load_dct(args.inlens, value_type=int)
    if args.inacvs:
        with args.inacvs as inacvs:
            acvs = set(inacvs.read().strip().split())
    else:
        acvs = set(groups.keys())
    selected = dict()
    for acv in acvs:
        group = groups[acv]
        length = lens[acv]
        max_acv, max_len = selected.get(group, (None, -1))
        if length > max_len:
            max_acv = acv
            max_len = length
        selected[group] = (max_acv, max_len)
    with args.oufile as oufile:
        if args.return_dict:
            for group, (acv, length) in sorted(selected.items()):
                oufile.write("%s\t%s\n" % (group, acv))
        else:
            for acv, length in sorted(selected.values()):
                oufile.write("%s\n" % acv)


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

