#! /usr/bin/env python

"""Calculate numbers of absent and under-represented sites."""

import argparse
from collections import Counter
import math
import sys


class LineParser(object):
    def __init__(self, indices, cutoffs):
        id_index, site_index, obs_index, exp_index = indices
        self.id_index = id_index
        self.site_index = site_index
        self.obs_index = obs_index
        self.exp_index = exp_index
        exp_cutoff, zero_cutoff, under_cutoff = cutoffs
        self.exp_cutoff = exp_cutoff
        self.zero_cutoff = zero_cutoff
        self.under_cutoff = under_cutoff

    def __call__(self, line):
        vals = line.strip().split("\t")
        site = vals[self.site_index]
        sid = None
        if self.id_index is not None:
            sid = vals[self.id_index]
        obs = float(vals[self.obs_index])
        exp = float(vals[self.exp_index])
        is_zero = obs <= self.zero_cutoff
        status = "bad"
        if not (math.isnan(exp) or math.isinf(exp)
                or exp <= self.exp_cutoff):
            ratio = obs / exp
            if ratio <= self.under_cutoff:
                status = "under"
            elif ratio < 1.0:
                status = "less"
            else:
                status = "other"
        return sid, site, is_zero, status


def load_list(inlist):
    if inlist is None:
        return None
    with inlist:
        return set(inlist.read().strip().split())


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Get numbers of absent and under-represented sites."
    )
    parser.add_argument(
        "intsv", metavar="FILE", type=argparse.FileType("r"),
        help="input file with compositional bias values"
    )
    parser.add_argument(
        "-o", dest="outsv", metavar="FILE", type=argparse.FileType("w"),
        default=sys.stdout, help="output file name"
    )
    parser.add_argument(
        "-s", dest="instl", metavar="LIST", type=argparse.FileType("r"),
        help="input list of sites to filter by"
    )
    parser.add_argument(
        "-a", dest="inacv", metavar="LIST", type=argparse.FileType("r"),
        help="input list of sequence IDs to filter by"
    )
    parser.add_argument(
        "-e", "--exp-cutoff", metavar="FLOAT", type=float, default=15.0,
        help="reliable expected number cutoff, default 15"
    )
    parser.add_argument(
        "-z", "--zero-cutoff", metavar="INT", type=int, default=0,
        help="zero observed number cutoff, default 0"
    )
    parser.add_argument(
        "-u", "--under-cutoff", metavar="FLOAT", type=float, default=0.78,
        help="under-representation cutoff, default 0.78"
    )
    parser.add_argument(
        "-I", "--id-index", metavar="N", type=int, default=0,
        help="site column index, default 0"
    )
    parser.add_argument(
        "-S", "--site-index", metavar="N", type=int, default=1,
        help="site column index, default 1"
    )
    parser.add_argument(
        "-O", "--obs-index", metavar="N", type=int, default=2,
        help="observed number column index, default 2"
    )
    parser.add_argument(
        "-E", "--exp-index", metavar="N", type=int, default=-3,
        help="expected number column index, default -3"
    )
    args = parser.parse_args(argv)
    indices = (args.id_index, args.site_index,
               args.obs_index, args.exp_index)
    cutoffs = (args.exp_cutoff, args.zero_cutoff, args.under_cutoff)
    line_parser = LineParser(indices, cutoffs)
    filter_sids = args.inacv is not None
    sids = load_list(args.inacv)
    filter_sites = args.instl is not None
    sites = load_list(args.instl)
    values = dict()
    with args.intsv as intsv:
        intsv.readline()
        for line in intsv:
            sid, site, is_zero, status = line_parser(line)
            if filter_sids and sid not in sids:
                continue
            if filter_sites and site not in sites:
                continue
            counts = values.setdefault(sid, Counter())
            counts["total"] += 1
            counts[status] += 1
            if is_zero:
                counts["zeros"] += 1
                if status == "bad":
                    counts["missed_zeros"] += 1
    with args.outsv as outsv:
        outsv.write(
            "ID\tTotal\tZeros\tZeros, %\tGood\tGood, %\tGood zeros\t"
            "Good zeros, %\tUnder\tUnder, %\tLess\tLess, %\n"
        )
        for sid in sorted(values):
            counts = values[sid]
            total = counts["total"]
            zeros = counts["zeros"]
            zeros_f = zeros * 100.0 / total
            good = total - counts["bad"]
            if good == 0:
                continue
            good_f = good * 100.0 / total
            good_zeros = zeros - counts["missed_zeros"]
            good_zeros_f = good_zeros * 100.0 / good
            unders = counts["under"]
            unders_f = unders * 100.0 / good
            less = unders + counts["less"]
            less_f = less * 100.0 / good
            line = "%s\t%d" + "\t%d\t%.1f" * 5 + "\n"
            outsv.write(line % (
                sid, total, zeros, zeros_f, good, good_f, good_zeros,
                good_zeros_f, unders, unders_f, less, less_f
            ))


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

