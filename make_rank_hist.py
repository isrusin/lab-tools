#! /usr/bin/env python2

"""Make a histrogram of compositional bias ranks."""

import argparse
import math
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Make histrogram of compositional bias ranks."
    )
    parser.add_argument(
        "intab", metavar="IN.tsv", type=argparse.FileType("r"),
        help="""input TSV file with compositional bias ranks, use '-'
        for STDIN"""
    )
    parser.add_argument(
        "ouhst", metavar="OUT.hst", type=argparse.FileType("w"),
        help="output file"
    )
    parser.add_argument(
        "--bins", dest="bins_number", type=int, default=41,
        help="number of bins, default 41"
    )
    parser.add_argument(
        "--cutoff", dest="cutoff", type=int, default=0,
        help="total number cutoff, default 0"
    )
    parser.add_argument(
        "-R", "--rank-index", metavar="N", type=int, default=-1,
        help="index of normalized ranks column, default -1"
    )
    parser.add_argument(
        "-T", "--total-index", metavar="N", type=int, default=1,
        help="index of the column with total number of ranks, default 1"
    )
    args = parser.parse_args(argv)
    bins = args.bins_number
    rank_index = args.rank_index
    total_index = args.total_index
    cutoff = args.cutoff
    hist = [0] * bins
    span = 1.0 - 0.0
    labs = ["%.2f" % ((i+0.5) * span / bins) for i in range(bins)]
    with args.intab as intab:
        _title = intab.readline()
        for line in intab:
            vals = line.strip().split("\t")
            total = int(vals[total_index])
            if total <= cutoff:
                continue
            ranks = [float(i) for i in vals[rank_index].split(",")]
            for rank in ranks:
                bin_index = min(int(rank * bins / span), bins - 1)
                hist[bin_index] += 1
    total = sum(hist)
    sys.stderr.write("The histogram was build by %d values.\n" % total)
    with args.ouhst as ouhst:
        ouhst.write("## Ranked compositional bias histogram\n")
        ouhst.write("## Source: %s\n" % args.intab.name)
        ouhst.write("## Bins number: %d\n" % bins)
        ouhst.write("## Rank number cutoff: %d\n" % cutoff)
        ouhst.write("## Total: %d\n" % total)
        ouhst.write("#:Bin\tPercent\n")
        if not total:
            total = 1
        for label, value in zip(labs, hist):
            ouhst.write("%s\t%.2f\n" % (label, value * 100.0 / total))


if __name__ == "__main__":
    sys.exit(main())

