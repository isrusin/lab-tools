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

blank_raw = """
      |    All   |Palindrome|Asymmetric| Coinside |  Differ  |Incomplete
------+----------+----------+----------+----------+----------+----------
Total | {all_tot}| {pal_tot}| {npl_tot}| {sam_tot}| {dif_tot}| {inc_tot}
------+----------+----------+----------+----------+----------+----------
NaN   | {all_nan}| {pal_nan}| {npl_nan}| {sam_nan}| {dif_nan}| {inc_nan}
Low   | {all_unr}| {pal_unr}| {npl_unr}| {sam_unr}| {dif_unr}| {inc_unr}
Good  | {all_rel}| {pal_rel}| {npl_rel}| {sam_rel}| {dif_rel}| {inc_rel}
------+----------+----------+----------+----------+----------+----------
<1    | {all_les}| {pal_les}| {npl_les}| {sam_les}| {dif_les}| {inc_les}
 1    | {all_one}| {pal_one}| {npl_one}| {sam_one}| {dif_one}| {inc_one}
>1    | {all_mor}| {pal_mor}| {npl_mor}| {sam_mor}| {dif_mor}| {inc_mor}
------+----------+----------+----------+----------+----------+----------
0     | {all_zer}| {pal_zer}| {npl_zer}| {sam_zer}| {dif_zer}| {inc_zer}
Under | {all_und}| {pal_und}| {npl_und}| {sam_und}| {dif_und}| {inc_und}
Norm  | {all_nor}| {pal_nor}| {npl_nor}| {sam_nor}| {dif_nor}| {inc_nor}
Over  | {all_ove}| {pal_ove}| {npl_ove}| {sam_ove}| {dif_ove}| {inc_ove}
"""
blank_md = blank_raw.strip("\n").replace("+", "|", 6).replace("+", "-")
blank_md = "|" + blank_md.replace("|", " | ").replace("-" * 72, "")

value_raw = "{0:>4} {1:>4.1f}"
def count_to_str(count, total):
    percent = (100.0 * count / total) if total else 0
    tag = ""
    if count >= 1000000:
        tag = "M"
        count /= 1000000.0
    elif count >= 1000:
        tag = "k"
        count /= 1000.0
    count_str_blank = "{:.0f}{}"
    if count < 10.0 and tag:
        count_str_blank = "{:.1f}{}"
    count_str = count_str_blank.format(count, tag)
    return value_raw.format(count_str, percent)

def calc_stat(stat_list, tag):
    stat = dict()
    total = sum(stat_list)
    stat[tag+"_total"] = total
    reliable = sum(stat_list[ZERO:])
    stat[tag+"_nan"] = count_to_str(stat_list[NAN], total)
    stat[tag+"_unr"] = count_to_str(stat_list[UNR], total)
    stat[tag+"_rel"] = count_to_str(reliable, total)
    stat[tag+"_zer"] = count_to_str(stat_list[ZERO], reliable)
    stat[tag+"_und"] = count_to_str(sum(stat_list[ZERO:LESS]), reliable)
    stat[tag+"_les"] = count_to_str(sum(stat_list[ZERO:ONE]), reliable)
    stat[tag+"_one"] = count_to_str(stat_list[ZERO], reliable)
    stat[tag+"_mor"] = count_to_str(sum(stat_list[MORE:]), reliable)
    stat[tag+"_ove"] = count_to_str(stat_list[OVER], reliable)
    stat[tag+"_nor"] = count_to_str(sum(stat_list[LESS:OVER]), reliable)
    return stat

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
            "-f", "--format", choices=["raw", "md", "html"],
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
    stats_same = [0] * 8
    stats_diff = [0] * 8
    groups_diff = Counter()
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
                        stats_same[group] += 2
                    else:
                        stats_diff[cgroup] += 1
                        groups_diff[tuple(sorted([group, cgroup]))] += 1
                else:
                    waits[pr] = group
            else:
                stats_pal[group] += 1
    
    stats_inc = [0] * 8
    for group in waits.values():
        stats_inc[group] += 1
    
    out_format = args.format
    if not out_format:
        out_name = args.out.name
        if out_name.endswith(".md"):
            out_format = "md"
        elif out_name.endswith(".html"):
            out_format = "html"
        else:
            out_format = "raw"
    stats_npl = list(map(sum, zip(stats_same, stats_diff, stats_inc)))
    stats_all = list(map(sum, zip(stats_pal, stats_npl)))
    stat_glob = dict()
    stat_glob.update(calc_stat(stats_all, "all"))
    stat_glob.update(calc_stat(stats_pal, "pal"))
    stat_glob.update(calc_stat(stats_npl, "npl"))
    stat_glob.update(calc_stat(stats_same, "sam"))
    stat_glob.update(calc_stat(stats_diff, "dif"))
    stat_glob.update(calc_stat(stats_inc, "inc"))
    total = stat_glob["all_total"]
    for tag in ["all", "pal", "npl", "sam", "dif", "inc"]:
        total_str = count_to_str(stat_glob[tag + "_total"], total)
        stat_glob[tag + "_tot"] = total_str
    output = blank_raw.format(**stat_glob).replace("100.0", " 100")
    with args.out as out:
        out.write(output.replace("0  0.0", "--    ") + "\n")
