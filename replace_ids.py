#!/usr/bin/python

import argparse as ap
import sys

if __name__ == "__main__":
    parser = ap.ArgumentParser(description="Replace IDs by dictionary.")
    parser.add_argument(
            "infile", metavar="FILE", type=ap.FileType("r"),
            help="input file with IDs column, which could be delimited"
            )
    parser.add_argument(
            "-s", dest="indct", type=ap.FileType("r"), metavar="DICT",
            required=True, help="source .dct file with IDs mapping"
            )
    parser.add_argument(
            "-o", "--out", dest="oufile", metavar="FILE",
            type=ap.FileType("w"), default=sys.stdout,
            help="output file, default stdout"
            )
    parser.add_argument(
            "-c", "--column", dest="index", type=int, default=0,
            metavar="N", help="index (from 0) of IDs column, default 0"
            )
    parser.add_argument(
            "-t", "--title", dest="title", action="store_true",
            help="treat the first line of the input file as title line"
            )
    parser.add_argument(
            "-d", "--delimiter", dest="delimiter", metavar="STRING",
            nargs="?", const=",", help="""switch to 'delimited' mode and
            set up the delimiter, default is coma (-d without value)"""
            )
    parser.add_argument(
            "-k", "--keep-order", dest="keep", action="store_true",
            help="keep order of IDs, only with -d"
            )
    args = parser.parse_args()
    idict = dict()
    with args.indct as indct:
        for line in indct:
            old, new = line.strip().split("\t")
            idict[old] = new
    index = args.index
    keep = args.keep
    delimiter = args.delimiter
    with args.infile as infile, args.oufile as oufile:
        if args.title:
            oufile.write(infile.readline())
        for line in infile:
            vals = line.strip().split("\t")
            val = vals[index]
            if delimiter:
                replaced = map(lambda x: idict.get(x, "?"),
                               val.split(delimiter))
                if not keep:
                    replaced = sorted(set(replaced))
                vals[index] = delimiter.join(replaced)
            else:
                vals[index] = idict.get(val, "?")
            oufile.write("\t".join(vals) + "\n")

