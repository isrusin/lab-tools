#! /usr/bin/env python

"""Calculate cutoff for the given level of significance."""

import argparse
import math
import signal
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Calculate cutoff for the given significance level.",
    )
    parser.add_argument(
        "intsv", metavar="INPUT", type=argparse.FileType("r"),
        help="input file with observed and expected numbers"
    )
    parser.add_argument(
        "-l", "--level", dest="sig_level", metavar="F", default="5%",
        help="level of significance, default 5%%"
    )
    cutoff_group = parser.add_mutually_exclusive_group()
    cutoff_group.add_argument(
        "-u", "--under-cutoff", dest="under_cutoff", action="store_true",
        default=True, help="return under-representation cutoff, default"
    )
    cutoff_group.add_argument(
        "-o", "--over-cutoff", dest="under_cutoff", action="store_false",
        help="return over-representation cutoff"
    )
    parser.add_argument(
        "-e", "--exp-cutoff", metavar="F", type=float, default=15.0,
        help="expected number cutoff (less or equal), default 15.0"
    )
    parser.add_argument(
        "-E", "--exp-index", metavar="N", type=int, default=-3,
        help="expected number column index, default -3"
    )
    index_group = parser.add_mutually_exclusive_group()
    index_group.add_argument(
        "-O", "--obs-index", metavar="N", type=int, default=2,
        help="observed number column index, default 2"
    )
    index_group.add_argument(
        "--no-id", dest="obs_index", action="store_const", const=1,
        help="""input table has no ID column, set the default observed
        number column index to 1"""
    )
    args = parser.parse_args(argv)
    under_cutoff = args.under_cutoff
    level_str = args.sig_level
    multiplier = 1
    if level_str.endswith("%"):
        multiplier = 0.01
    try:
        sig_level = float(level_str.rstrip("%")) * multiplier
    except ValueError:
        parser.error(
            "bad significance level value!\n"
            "Valid examples: 1.5%, 0.005, .01, 1e-5, .5E-1%"
        )
    if sig_level < 0 or sig_level > 1:
        parser.error(
            "bad significance level value!\n"
            "It should be in range [0; 1]"
        )
    obs_index = args.obs_index
    exp_index = args.exp_index
    exp_cutoff = args.exp_cutoff
    ratios = []
    with args.intsv as intsv:
        _title = intsv.readline()
        for line in intsv:
            vals = line.strip().split("\t")
            obs = float(vals[obs_index])
            exp = float(vals[exp_index])
            if math.isnan(exp) or math.isinf(exp) or exp <= exp_cutoff:
                continue
            ratios.append(obs / exp)
    ratios.sort()
    index = int(sig_level * len(ratios))
    if under_cutoff:
        index = max(0, index-1)
    else:
        index = min(-1, -index)
    print "%.2f" % ratios[index]


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

