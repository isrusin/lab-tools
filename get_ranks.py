#! /usr/bin/env python2

"""Get site ranks for selected pairs in control dataset."""

import argparse
from collections import Counter
import math
import sys


class LineParser(object):
    def __init__(self, indices, exp_cutoff):
        id_index, site_index, obs_index, exp_index = indices
        self.id_index = id_index
        self.site_index = site_index
        self.obs_index = obs_index
        self.exp_index = exp_index
        self.exp_cutoff = exp_cutoff

    def __call__(self, line):
        vals = line.strip().split("\t")
        sid = vals[self.id_index]
        site = vals[self.site_index]
        obs = float(vals[self.obs_index])
        exp = float(vals[self.exp_index])
        if math.isnan(exp) or math.isinf(exp) or exp <= self.exp_cutoff:
            return sid, site, None
        else:
            return sid, site, obs / exp


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Get site ranks for selected pairs in control dataset"
    )
    parser.add_argument(
        "intsv", metavar="TSV", type=argparse.FileType("r"),
        help="input control dataset"
    )
    parser.add_argument(
        "-p", "--pairs", metavar="LIST", type=argparse.FileType("r"),
        help="input list of pairs to calculate ranks for"
    )
    parser.add_argument(
        "-o", "--out", dest="outsv", metavar="FILE",
        type=argparse.FileType("w"), default=sys.stdout,
        help="output file, default is STDOUT"
    )
    parser.add_argument(
        "--exp-cutoff", metavar="F", type=float, default=15.0,
        help="expected number cutoff, default 15.0"
    )
    index_group_desc = (
        "All column indices are counted from 0 and could be negative\n"
        "(-1 means the last column)."
    )
    index_group = parser.add_argument_group(
        "column index arguments", description=index_group_desc
    )
    index_group.add_argument(
        "-I", "--id-index", metavar="N", type=int, default=0,
        help="sequence ID column index, default 0"
    )
    index_group.add_argument(
        "-S", "--site-index", metavar="N", type=int, default=1,
        help="site column index, default 1"
    )
    index_group.add_argument(
        "-O", "--obs-index", metavar="N", type=int, default=2,
        help="observed number column index, default 2"
    )
    index_group.add_argument(
        "-E", "--exp-index", metavar="N", type=int, default=-3,
        help="expected number column index, default -3"
    )
    args = parser.parse_args(argv)
    indices = (args.id_index, args.site_index,
               args.obs_index, args.exp_index)
    line_parser = LineParser(indices, args.exp_cutoff)
    pairs = set()
    if args.pairs:
        with args.pairs as inprs:
            for line in inprs:
                if line.startswith("#"):
                    continue
                pairs.add(tuple(line.strip().split("\t")))
    selected = dict()
    ratios = dict()
    with args.intsv as intsv:
        _title = intsv.readline()
        for line in intsv:
            if line.startswith("#"):
                continue
            sid, site, ratio = line_parser(line)
            if ratio is None:
                continue
            ratios.setdefault(site, []).append(ratio)
            if (sid, site) in pairs:
                selected.setdefault(site, []).append(ratio)
    with args.outsv as outsv:
        outsv.write("#:Site\tTotal\tRanks\tNormalized ranks, %\n")
        for site in sorted(selected.keys()):
            ranks = dict()
            counter = Counter(ratios[site])
            rank = 0
            for ratio, count in sorted(counter.items()):
                ranks[ratio] = rank + (count + 1.0) / 2
                rank += count
            selected_ranks = []
            for ratio in selected[site]:
                selected_ranks.append(ranks[ratio])
            selected_ranks.sort()
            normed_ranks = [
                (item - 0.5) * 100.0 / rank for item in selected_ranks
            ]
            outsv.write("%s\t%d\t%s\t%s\n" % (
                site, rank,
                ",".join((
                    "%d" if item.is_integer() else "%.1f"
                ) % item for item in selected_ranks),
                ",".join("%.1f" % item for item in normed_ranks)
            ))


if __name__ == "__main__":
    sys.exit(main())
