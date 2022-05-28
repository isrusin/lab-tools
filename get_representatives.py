#! /usr/bin/env python2

"""Keep the only representative of each group in a TSV file."""

import argparse
import signal
import sys


def load_dct(indct, value_type=str, default=None):
    vals = dict()
    if indct is None:
        return default
    with indct:
        for line in indct:
            if line.startswith("#"):
                continue
            key, value = line.strip("\n").split("\t")
            vals[key] = value_type(value)
    return vals


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Keep the only representative of each group."
    )
    parser.add_argument(
        "intsv", metavar="TSV", type=argparse.FileType("r"),
        help="input .tsv file"
    )
    parser.add_argument(
        "-g", "--groups", metavar="DICT", type=argparse.FileType("r"),
        default=sys.stdin, help="group dictionary, default STDIN"
    )
    parser.add_argument(
        "-o", dest="outsv", metavar="FILE", type=argparse.FileType("w"),
        default=sys.stdout, help="output file, default STDOUT"
    )
    parser.add_argument(
        "-v", "--values", metavar="DICT", type=argparse.FileType("r"),
        help="""dictionary of values (integer) to sort by, IDs with
        the same values are sorted alphabetically; default values are
        line indices"""
    )
    parser.add_argument(
        "-i", "--index", metavar="N", type=int, default=0,
        help="ID column index, default 0"
    )
    parser.add_argument(
        "-j", "--join-id", dest="indices", metavar="N", action="append",
        type=int, help="index of a column to include in the ID"
    )
    parser.add_argument(
        "-r", "--keep-lowest", dest="get_lowest", action="store_false",
        help="""keep the member of each group with the lowest value,
        default is to keep the member with the greatest value"""
    )
    parser.add_argument(
        "-t", "--keep-title", action="store_true",
        help="keep the first title line of the input file"
    )
    parser.add_argument(
        "-#", "--skip-comments", action="store_true",
        help="skip lines starting with '#', default is to keep them"
    )
    args = parser.parse_args(argv)
    groups = load_dct(args.groups)
    values = load_dct(args.values, value_type=int, default=dict())
    index = args.index
    indices = args.indices or []
    with args.intsv as intsv:
        lines = intsv.readlines()
    grouped = dict()
    lids = []
    for i, line in enumerate(lines):
        if i == 0 and args.keep_title:
            lids.append(None)
            continue
        if line.startswith("#"):
            lids.append("#")
            continue
        vals = line.strip("\n").split("\t")
        key = vals[index]
        try:
            group = groups[key]
        except KeyError:
            sys.stderr.write(
                "Warning: no '%s' in group dictionary, skipped!\n" % key
            )
            lids.append("to-skip")
            continue
        value = values.get(key, i)
        aid = tuple(vals[j] for j in indices)
        lid = (key, aid)
        lids.append(lid)
        gid = (group, aid)
        grouped.setdefault(gid, []).append((value, lid))
    selected = set([None])
    if not args.skip_comments:
        selected.add("#")
    which = 0 if args.get_lowest else -1
    for group in grouped.values():
        value, lid = sorted(group)[which]
        selected.add(lid)
    with args.outsv as outsv:
        outsv.writelines(
            line for lid, line in zip(lids, lines) if lid in selected
        )


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

