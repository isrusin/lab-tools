#! /usr/bin/env python

"""Add or update AC versions in a TSV (or LIST) file by AC version list."""

import argparse
import signal
import sys

def main(argv):
    parser = argparse.ArgumentParser(description="Add/update AC version.")
    parser.add_argument(
        "infile", metavar="FILE", type=argparse.FileType("r"),
        help="input AC(v) containing file, use '-' for STDIN"
    )
    parser.add_argument(
        "-t", "--with-title", dest="title", action="store_true",
        help="input file has title"
    )
    parser.add_argument(
        "-c", dest="column", metavar="N", type=int, default=0,
        help="index of AC(v) column in the input file, default 0"
    )
    parser.add_argument(
        "-s", dest="source", metavar="LIST", type=argparse.FileType("r"),
        required=True, help="ACv list to get versions from"
    )
    parser.add_argument(
        "-d", "--delimiter", dest="delimiter", metavar="STRING",
        nargs="?", const=",", help="""switch to 'delimited' mode and
        set up the delimiter, default is coma (-d without value)"""
    )
    ougroup = parser.add_mutually_exclusive_group()
    ougroup.add_argument(
        "-i", "--in-place", dest="inplace", action="store_true",
        help="Add/update AC versions in-place"
    )
    ougroup.add_argument(
        "-o", dest="oufile", metavar="FILE", type=argparse.FileType("w"),
        default=sys.stdout, help="output file, default STDOUT"
    )
    args = parser.parse_args(argv)
    ac2acv = dict()
    with args.source as source:
        for line in source:
            acv = line.strip()
            ac = acv.split(".")[0]
            ac2acv[ac] = acv
    lines = []
    index = args.column
    delimiter = args.delimiter
    with args.infile as infile:
        if args.title:
            lines.append(infile.readline().strip())
        for line in infile:
            vals = line.strip().split("\t")
            val = vals[index]
            if delimiter:
                acs = map(lambda x: x.split(".")[0], val.split(delimiter))
                replaced = set(ac2acv.get(ac, "") for ac in acs)
                replaced.discard("")
                vals[index] = delimiter.join(sorted(replaced))
            else:
                ac = val.split(".")[0]
                vals[index] = ac2acv.get(ac, "")
            lines.append("\t".join(vals))
    oufile = open(infile.name, "w") if args.inplace else args.oufile
    if oufile.name == "<stdout>":
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    with oufile:
        oufile.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    sys.exit(main())

