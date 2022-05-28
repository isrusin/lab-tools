#! /usr/bin/env python2

"""Extract CBStat groups from TSV table."""

import argparse
import math
import signal
import sys


NAN, UNR, ZERO, UNDER, OVER, LESS, MORE, ONE = (0, 1, 2, 3, 4, 5, 6, 7)

COMPLS = {
    "A": "T", "T": "A", "C": "G", "G": "C",
    "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
    "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
}

SITE_ABBRS = {
    "*": "ALL", "a": "ALL", "A": "ALLC", "n": "NPL", "N": "NPLC",
    "p": "PAL", "s": "SYM", "d": "DIF", "i": "INC",
}

CB_ABBRS = {
    "*": "ALL", "#": "NAN", "~": "LOW", "-": "BAD",
    "+": "GOOD", "0": "ZERO", "U": "UND", "u": "UNDER",
    "<": "LESS", "L": "LNORM", "1": "ONE", "n": "NORM",
    ">": "MORE", "M": "MNORM", "o": "OVER", "a": "ALL"
}

SITE_GROUPS = {
    "ALL": ["PAL", "SYM", "DIF", "INC"], "ALLC": ["PAL", "SYM", "DIF"],
    "NPL": ["SYM", "DIF", "INC"], "NPLC": ["SYM", "DIF"],
    "PAL": ["PAL"], "SYM": ["SYM"], "DIF": ["DIF"], "INC": ["INC"]
}

CB_GROUPS = {
    "NAN": [NAN], "LOW": [UNR], "BAD": [NAN, UNR],
    "GOOD": [ZERO, UNDER, OVER, LESS, MORE, ONE],
    "ZERO": [ZERO], "UND": [UNDER], "UNDER": [ZERO, UNDER],
    "LESS": [ZERO, UNDER, LESS], "LNORM": [LESS],
    "NORM": [LESS, ONE, MORE], "ONE": [ONE],
    "MORE": [MORE, OVER], "MNORM": [MORE], "OVER": [OVER],
    "ALL": [NAN, UNR, ZERO, UNDER, OVER, LESS, MORE, ONE]
}


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
        site = vals[self.site_index]
        rsite = "".join(COMPLS.get(nucl, "?") for nucl in site[::-1])
        watson = site if site < rsite else rsite
        is_pal = site == rsite
        if self.id_index is None:
            pair = (site,)
            pair_id = (watson,)
        else:
            sid = vals[self.id_index]
            pair = (sid, site)
            pair_id = (sid, watson)
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
        return pair, pair_id, is_pal, group


class DoubleStrandedGroups(object):
    def __init__(self, lines, line_parser, join_strands=False):
        self.lines = lines
        self.line_parser = line_parser
        self.join_strands = join_strands
        self.waits = dict()

    def __iter__(self):
        waits = self.waits
        for line in self.lines:
            pair, pair_id, is_pal, group = self.line_parser(line)
            if is_pal:
                yield ("PAL", group), pair
            else:
                if pair_id in waits:
                    cpair, cgroup = waits.pop(pair_id)
                    site_group = "SYM" if cgroup == group else "DIF"
                    yield (site_group, group), pair
                    yield (site_group, cgroup), cpair
                else:
                    waits[pair_id] = (pair, group)
        for pair, group in waits.values():
            yield ("INC", group), pair


def get_groups(group_desc):
    groups = set()
    for desc in group_desc:
        if "," in desc:
            sg_tag, cbg_tag = desc.upper().split(",")
        else:
            sg_tag = SITE_ABBRS[desc[0]]
            cbg_tag = CB_ABBRS[desc[1]]
        for site_group in SITE_GROUPS[sg_tag]:
            for cb_group in CB_GROUPS[cbg_tag]:
                groups.add((site_group, cb_group))
    return groups


def main(argv=None):
    group_designation_help = (
        "Group designation can be either (COL,ROW) or CR. COL and ROW\n"
        "values are case insensitive, while C and R values are not.\n\n"
        "Available COL/C values incude:\n"
        "  all/a (all sites), allc/A (all complete),\n"
        "  npl/n (asymmetric),  nplc/N (asymmetric and complete),\n"
        "  pal/p (palindromes), sym/s (coiside),\n"
        "  dif/d (differing), inc/i (incomplete).\n\n"
        "Available ROW/R values include:\n"
        "  all/a (all), nan/# (NAN), low/~ (unreliable),\n"
        "  bad/- (unreliable or NAN), good/+ (reliable),\n"
        "  zero/0 (equal 0), under/u (under-represented),\n"
        "  und/U (under-represented without 0),\n"
        "  norm/n (normally presented), less/l (less than 1),\n"
        "  more/m (greater than 1), one/1 (equal 1),\n"
        "  lnorm/L (less than 1 and normally presented),\n"
        "  mnorm/M (greater than 1 and normally represented),\n"
        "  over/o (over-represented).\n"
    )
    parser = argparse.ArgumentParser(
        description="Extract CBStat groups from TSV table.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=group_designation_help
    )
    io_group = parser.add_argument_group("input/output arguments")
    io_group.add_argument(
        "intsv", metavar="INPUT", type=argparse.FileType("r"),
        help="input file with observed and expected numbers"
    )
    io_group.add_argument(
        "-o", "--out", metavar="OUTPUT", type=argparse.FileType("w"),
        default=sys.stdout, help="""output file with extracted pairs,
        default STDOUT"""
    )
    io_group.add_argument(
        "-g", "--group", dest="groups", metavar="(C,R) or CR",
        action="append", help="""designation of group to return
        pairs for, possible designations are listed below;
        default is 'a+'"""
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
    index_group_desc = (
        "All column indices are counted from 0 and could be negative\n"
        "(-1 means the last column)."
    )
    index_group = parser.add_argument_group(
        "column index arguments", description=index_group_desc
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
    with args.intsv as intsv:
        _title = intsv.readline()
        ds_groups = DoubleStrandedGroups(intsv, line_parser)
        groups = get_groups(args.groups or ["a+"])
        with args.out as ouprs:
            for group, pair in ds_groups:
                if group in groups:
                    ouprs.write("\t".join(pair) + "\n")


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

