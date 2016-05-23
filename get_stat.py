#! /usr/bin/python

import argparse as ap
import math
import sys
from collections import Counter

compls = {
        "A": "T", "T": "A", "C": "G", "G": "C",
        "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
        "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
        }

def to_ds(site):
    rsite = ""
    for nucl in site[::-1]:
        rsite += compls.get(nucl, "?")
    return (min(site, rsite), max(site, rsite))

NAN = 0
UNR = 1
ZERO = 2
UNDER = 3
LESS = 4
ONE = 5
MORE = 6
OVER = 7

def classify(obs, exp):
    group = ONE
    if math.isnan(exp) or math.isinf(exp) or exp == 0:
        group = NAN
    elif exp <= EXP_CUTOFF:
        group = UNR
    else:
        ratio = obs / exp
        if ratio < 1.0:
            if ratio <= ZERO_CUTOFF:
                group = ZERO
            elif ratio <= UNDER_CUTOFF:
                group = UNDER
            else:
                group = LESS
        elif ratio > 1.0:
            if ratio >= OVER_CUTOFF:
                group = OVER
            else:
                group = MORE
    return group

if __name__ == "__main__":
    parser = ap.ArgumentParser(
            description="Get site representation statistics."
            )
    io_group = parser.add_argument_group("input/output arguments")
    io_group.add_argument(
            "intsv", metavar="INPUT", type=ap.FileType("r"),
            help="input file with observed and expected numbers"
            )
    io_group.add_argument(
            "-o", "--out", metavar="OUTPUT", type=ap.FileType("w"),
            default=sys.stdout, help="""output file, default stdout; note:
            .md and .html extensions will alter output format"""
            )
    io_group.add_argument(
            "-f", "--format", choices=["raw", "md", "html"], default="raw",
            help="""output format: 'raw' - raw text, default;
            'md' - markdown (GitHub dialect); 'html' - HTML,
            through markdown"""
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
            title="column index arguments", description="""All column
            indices are counted from 0 and could be negative
            (-1 for last column)."""
            )
    index_group.add_argument(
            "-S", "--site-index", metavar="N", type=int, default=1,
            help="site column index, default 1"
            )
    index_group.add_argument(
            "-I", "--id-index", metavar="N", type=int, default=0,
            help="sequence ID column index, default 0"
            )
    index_group.add_argument(
            "-E", "--exp-index", metavar="N", type=int, default=-3,
            help="expected number column index, default -3"
            )
    index_group.add_argument(
            "-O", "--obs-index", metavar="N", type=int,
            help="""observed number column index, default expected number
            column index - 1"""
            )
#   parser.add_argument("--no-id")
    args = parser.parse_args()
    
    EXP_CUTOFF = args.exp_cutoff
    ZERO_CUTOFF = args.zero_cutoff
    UNDER_CUTOFF = args.under_cutoff
    OVER_CUTOFF = args.over_cutoff
    
    site_index = args.site_index
    id_index = args.id_index
    exp_index = args.exp_index
    obs_index = args.obs_index
    if obs_index is None:
        obs_index = exp_index - 1
    
    waits = dict()
    stats_pal = [0] * 8
    stats_npl = [0] * 8
    stats_diff = Counter()
    with args.intsv as intsv:
        intsv.readline()
        for line in intsv:
            vals = line.strip().split('\t')
            sid = vals[id_index]
            exp = float(vals[exp_index])
            obs = float(vals[obs_index])
            group = classify(obs, exp)
            site = to_ds(vals[site_index])
            wsite, csite = site
            if wsite != csite:
                pr = (sid, site)
                if pr in waits:
                    cgroup = waits.pop(pr)
                    if cgroup == group:
                        stats_npl[group] += 1
                    else:
                        stats_diff[tuple(sorted([group, cgroup]))] += 1
                else:
                    waits[pr] = group
            else:
                stats_pal[group] += 1
    
    print stats_pal
    print stats_npl
    print stats_diff.items()
    print len(waits)
