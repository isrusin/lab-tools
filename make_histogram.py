#! /usr/bin/env python2

"""Make a histrogram of compositional bias values."""

import argparse
import math
import sys


COMPLS = {
    "A": "T", "B": "V", "T": "A", "V": "B", "W": "W",
    "C": "G", "D": "H", "G": "C", "H": "D", "S": "S",
    "K": "M", "M": "K", "R": "Y", "Y": "R", "N": "N"
}


def get_ds_site(site):
    rsite = "".join(COMPLS[nucl] for nucl in site[::-1])
    return min(site, rsite), max(site, rsite)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Make histrogram of compositional bias values."
    )
    parser.add_argument(
        "intab", metavar="IN.tsv", type=argparse.FileType("r"),
        help="""input TSV file with compositional bias values, use '-'
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
    parser.add_argument(
        "-m", "--ds-mode", choices=["none", "summarize", "justify"],
        default="summarize", help="""how to handle assymetric sites from
        different strands, possible options are 'none' (handle each site
        separately), 'summarize' (sum up expected and observed numbers
        before calculation of the ratio), and 'justify' (like 'none' but
        also consider every palindromic site twice to justify the
        contributions of assymetric and palindromic sites) """
    )
    args = parser.parse_args(argv)
    ds_mode = args.ds_mode
    bins = args.bins_number
    bins_total = bins + 1 # + '> 2.0'
    exp_index = args.exp
    obs_index = args.obs
    hist = [0] * bins_total
    span = 2.0 - 0.0
    labs = ["%.2f" % ((i+0.5) * span / bins) for i in range(bins_total)]
    waits = dict()
    with args.intab as intab:
        intab.readline()
        for line in intab:
            vals = line.strip().split("\t")
            sid = vals[0]
            site = get_ds_site(vals[1])
            ispal = site[0] == site[1]
            pair = (sid, site)
            expected = float(vals[exp_index])
            observed = float(vals[obs_index])
            if math.isnan(expected) or expected <= args.cutoff:
                continue
            if ds_mode == "summarize" and not ispal:
                observed_, expected_ = waits.get(pair, (0, 0))
                observed += observed_
                expected += expected_
                waits[pair] = (observed, expected)
            else:
                ratio = observed / expected
                bin_index = min(int(ratio * bins / span), bins)
                hist[bin_index] += 1
                if ispal and ds_mode == "justify":
                    hist[bin_index] += 1
    for observed, expected in waits.values():
        ratio = observed / expected
        bin_index = min(int(ratio * bins / span), bins)
        hist[bin_index] += 1
    total = sum(hist)
    sys.stderr.write("The histogram was build by %d values.\n" % total)
    with args.ouhst as ouhst:
        ouhst.write("## Compositional bias histogram\n")
        ouhst.write("## Source: %s\n" % args.intab.name)
        ouhst.write("## Bins number: (%d+1)\n" % args.bins_number)
        ouhst.write("## Expected cutoff: %.1f\n" % args.cutoff)
        ouhst.write("## Assymetric handler: %s\n" % ds_mode)
        ouhst.write("## Total: %d\n" % total)
        ouhst.write("#Bin\tPercent\n")
        if not total:
            total = 1
        for label, value in zip(labs, hist):
            ouhst.write("%s\t%.2f\n" % (label, value * 100.0 / total))


if __name__ == "__main__":
    sys.exit(main())
