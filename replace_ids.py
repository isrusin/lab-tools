#!/usr/bin/python

import argparse as ap
import signal as sg
import sys

if __name__ == "__main__":
    sg.signal(sg.SIGPIPE, sg.SIG_DFL)
    parser = ap.ArgumentParser(description="Replace IDs by dictionary.")
    parser.add_argument(
            "infile", metavar="FILE", type=ap.FileType("r"),
            help="input file with IDs column, which could be delimited"
            )
    parser.add_argument(
            "-s", dest="indct", type=ap.FileType("r"), metavar="DICT",
            required=True, help="""source .dct file with IDs mapping;
            it should be tab-separated untitled file with IDs in the
            first column, line residuals after the first tab will be
            treated as new IDs (should not be unique actually and could
            contain any non-line-breaking symbols, including spaces and
            tabs)"""
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
            nargs="?", default=",", help="""set up the delimiter for
            multiple-entry values, default is coma; -d with no value means
            not to split values"""
            )
    parser.add_argument(
            "-k", "--keep-order", dest="keep", action="store_true",
            help="""keep order of IDs, meaningless with -d without value;
            default behaviour is to sort new IDs and remove duplicates"""
            )
    parser.add_argument(
            "-m", "--missed", dest="missed", metavar="STRING", nargs="?",
            default="", help="""a string to replace IDs missed in source
            with; -m without value forces to keep missed IDs in place;
            default behaviour (without -m) is to remove all missed IDs"""
            )
    args = parser.parse_args()
    idict = dict()
    with args.indct as indct:
        for line in indct:
            old, new = line.strip().split("\t", 1)
            idict[old] = new
    index = args.index
    keep = args.keep
    delimiter = args.delimiter
    split = lambda x: x.split(delimiter)
    if not delimiter:
        split = lambda x: [x]
    missed = args.missed
    replace = lambda x: idict.get(x, missed)
    if missed is None:
        replace = lambda x: idict.get(x, x)
    with args.infile as infile, args.oufile as oufile:
        if args.title:
            oufile.write(infile.readline())
        for line in infile:
            vals = line.strip().split("\t")
            val = vals[index]
            replaced = [replace(x) for x in split(val)]
            replaced = filter(None, replaced)
            if not keep:
                replaced = sorted(set(replaced))
            vals[index] = (delimiter or "").join(replaced)
            oufile.write("\t".join(vals) + "\n")

