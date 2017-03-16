#! /usr/bin/env python

"""Extract CBStat groups from TSV table."""

import argparse
import signal
import sys


NAN, UNR, ZERO, UNDER, OVER, LESS, MORE, ONE = (0, 1, 2, 3, 4, 5, 6, 7)

COMPLS = {"A": "T", "T": "A", "C": "G", "G": "C",
          "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
          "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"}


class LineParser(object):
    def __init__(self, indices, cutoffs):
        id_index, site_index, obs_index, exp_index = indices
        self.id_index = id_index
        self.site_index = site_index
        self.obs_index = obs_index
        self.exp_index = exp_index
        exp_cutoff, zero_cutoff, under_cutoff, over_cutoff = cutoffs
        self.exp_cutoff = exp_cutoff
        self.zero_cutoff = zero_cutoff
        self.under_cutoff = under_cutoff
        self.over_cutoff = over_cutoff

    def __call__(self, line):
        vals = line.strip().split("\t")
        sid = None if self.id_index is None else vals[self.id_index]
        site = vals[self.site_index]
        rsite = "".join(COMPLS.get(nucl, "?") for nucl in site[::-1])
        site_ds = (site, rsite) if site < rsite else (rsite, site)
        obs = float(vals[self.obs_index])
        exp = float(vals[self.exp_index])
        group = ONE
        if math.isnan(exp) or math.isinf(exp) or exp == 0:
            group = NAN
        elif exp <= self.exp_cutoff:
            group = UNR
        else:
            ratio = obs / exp
            if ratio < 1.0:
                group = LESS
                if ratio <= self.under_cutoff:
                    group = UNDER if ratio > self.zero_cutoff else ZERO
            elif ratio > 1.0:
                group = MORE if ratio < self.over_cutoff else OVER
        return sid, site_ds, group


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Extract CBStat groups from TSV table."
    )
    io_group = parser.add_argument_group("input/output arguments")
    io_group.add_argument(
        "intsv", metavar="INPUT", type=argparse.FileType("r"),
        help="input file with observed and expected numbers"
    )
    io_group.add_argument(
        "-o", "--out", metavar="OUTPUT", type=argparse.FileType("w"),
        default=sys.stdout, help="output TSV file, default stdout"
    )
    cutoff_group = parser.add_argument_group("cutoff arguments")
    cutoff_group.add_argument(
        "--exp-cutoff", metavar="F", type=float, default=15.0,
        help="expected number cutoff (less or equal), default 15.0"
    )
    cutoff_group.add_argument(
        "--zero-cutoff", metavar="F", type=float, default=0.0,
        help="zero value cutoff (less or equal), default 0.0"
    )
    cutoff_group.add_argument(
        "--under-cutoff", metavar="F", type=float, default=0.78,
        help="""under-representation cutoff (less or equal),
        default 0.78"""
    )
    cutoff_group.add_argument(
        "--over-cutoff", metavar="F", type=float, default=1.23,
        help="""over-representation cutoff (greater or equal),
        default 1.23"""
    )
    index_group = parser.add_argument_group(
        "column index arguments", description="""All column
        indices are counted from 0 and could be negative
        (-1 for the last column)."""
    )
    index_group.add_argument(
        "-I", "--id-index", metavar="N", type=int,
        help="sequence ID column index, default 0"
    )
    index_group.add_argument(
        "-S", "--site-index", metavar="N", type=int,
        help="site column index, default 1"
    )
    index_group.add_argument(
        "-E", "--exp-index", metavar="N", type=int,
        help="expected number column index, default -3"
    )
    index_group.add_argument(
        "-O", "--obs-index", metavar="N", type=int,
        help="observed number column index, default 2"
    )
    index_group.add_argument(
        "--no-id", action="store_true", help="""input table has no ID
        column, shift default column indices"""
    )
    args = parser.parse_args(argv)
    # indices
    no_id = int(args.no_id)
    apply_default = lambda x, default: default if x is None else x
    id_index = apply_default(args.id_index, None if no_id else 0)
    site_index = apply_default(args.site_index, 1-no_id)
    obs_index = apply_default(args.obs_index, 2-no_id)
    exp_index = apply_default(args.exp_index, -3)
    indices = (id_index, site_index, obs_index, exp_index)
    # cutoffs
    cutoffs = (
        args.exp_cutoff, args.zero_cutoff,
        args.under_cutoff, args.over_cutoff
    )
    line_parser = LineParser(indices, cutoffs)
    group = make_group(#TODO)
    get_group(args.intsv, args.outsv, line_parser, group) #TODO


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

