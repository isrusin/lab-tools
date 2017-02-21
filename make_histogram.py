#! /usr/bin/env python

"""Make a histrogram of contrast ratio values."""

import argparse
import math
import sys

cmpls = {
    "A": "T", "B": "V", "T": "A", "V": "B", "W": "W",
    "C": "G", "D": "H", "G": "C", "H": "D", "S": "S",
    "K": "M", "M": "K", "R": "Y", "Y": "R", "N": "N"
}

def ds(site):
    compl = ""
    for nucl in site:
        compl = cmpls[nucl] + compl
    return min([site, compl])

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Make histrogram of contrast ratio values."
    )
    parser.add_argument(
        "intab", metavar="IN.tsv", type=argparse.FileType("r"),
        help="input tabular file with contrast ratio values"
    )
    parser.add_argument(
        "ouhst", metavar="OU.hst", type=argparse.FileType("w"),
        help="output histogram file"
    )
    parser.add_argument(
        "--bins", dest="bins_number", type=int, default=41,
        help="number of bins, default 41"
    )
    parser.add_argument(
        "--cutoff", dest="cutoff", type=float, default=15,
        help="expected number cutoff, default 15"
    )
    parser.add_argument(
        "--expected", metavar="N", dest="exp", type=int, default=-3,
        help="index of expected number column, default -3"
    )
    parser.add_argument(
        "--observed", metavar="N", dest="obs", type=int, default=2,
        help="index of observed number column, default 2"
    )
    args = parser.parse_args(argv)
    bins = args.bins_number
    bins_total = bins + 1 # + '> 2.0'
    exp_index = args.exp
    obs_index = args.obs
    counts = dict()
    with args.intab as intab:
        intab.readline()
        for line in intab:
            vals = line.strip().split("\t")
            acv = vals[0]
            site = ds(vals[1])
            pair = (acv, site)
            expected = float(vals[exp_index])
            observed = float(vals[obs_index])
            if math.isnan(expected) or expected <= args.cutoff:
                expected = observed = 0
            expected_, observed_ = counts.get(pair, (0, 0))
            expected_ += expected
            observed_ += observed
            counts[pair] = (expected_, observed_)
    hist = [0] * bins_total
    span = 2.0 - 0.0
    labs = ["%.2f" % ((i+0.5) * span / bins) for i in range(bins_total)]
    for expected, observed in counts.values():
        if expected <= args.cutoff:
            continue
        ratio = observed / expected
        bin_index = min(int(ratio * bins / span), bins)
        hist[bin_index] += 1
    total = sum(hist)
    sys.stderr.write("The histogram was build by %d values.\n" % total)
    if not total:
        total = 1
    with args.ouhst as ouhst:
        for label, value in zip(labs, hist):
            ouhst.write("%s\t%.2f\n" % (label, value * 100.0 / total))

if __name__ == "__main__":
    sys.exit(main())
