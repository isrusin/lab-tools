#! /usr/bin/python

import argparse as ap
from collections import Counter
import markdown
import math
from markdown.extensions.tables import TableExtension
import sys

compls = {
        "A": "T", "T": "A", "C": "G", "G": "C",
        "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
        "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
        }

NAN = 0
UNR = 1
ZERO = 2
UNDER = 3
LESS = 4
ONE = 5
MORE = 6
OVER = 7

title_str = "\n\n\t{}:\n"
stats_str = """
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
stats_val_str = "{count:>4s} {percent:>4.1f}"

groups_str = """
      |  NaN  |  Low  |  Zero | Under |  Less |  One  |  More |  Over |
------+-------+-------+-------+-------+-------+-------+-------+-------+
Total |{na_to}|{lo_to}|{ze_to}|{un_to}|{le_to}|{on_to}|{mo_to}|{ov_to}|
------+-------+-------+-------+-------+-------+-------+-------+-------'
Over  |{na_ov}|{lo_ov}|{ze_ov}|{un_ov}|{le_ov}|{on_ov}|{mo_ov}|
------+-------+-------+-------+-------+-------+-------+-------'
More  |{na_mo}|{lo_mo}|{ze_mo}|{un_mo}|{le_mo}|{on_mo}|
------+-------+-------+-------+-------+-------+-------'
One   |{na_on}|{lo_on}|{ze_on}|{un_on}|{le_on}|
------+-------+-------+-------+-------+-------'
Less  |{na_le}|{lo_le}|{ze_le}|{un_le}|
------+-------+-------+-------+-------'
Under |{na_un}|{lo_un}|{ze_un}|
------+-------+-------+-------'
Zero  |{na_ze}|{lo_ze}|
------+-------+-------'
Low   |{na_lo}|
------+-------'
"""
groups_num_str = "{count:>6s} "
groups_prc_str = "{percent:>5.1f}% "

html_seed = """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>get_stat output</title>
    <style type="text/css">
      table {
        border-collapse: collapse;
      }
      td, th {
        padding: 1mm 3mm 1mm 3mm;
        border: 1px solid black;
      }
      th {
        background: #ccffff;
        text-align: center;
      }
    </style>
  </head>
  <body>
@stat
  </body>
</html>
"""

def raw_table_to_markdown(table):
    lines = table.strip("\n").split("\n")
    tcells = [c.strip() for c in lines.pop(0).strip("\n|").split("|")]
    if not tcells[0]:
        tcells[0] = "  "
    cols_num = len(tcells)
    table_md = "| %s |\n" % " | ".join(tcells)
    table_md += "|:%s:|\n" % ":|-".join("-" * len(c) for c in tcells)
    table_md = table_md.replace(":|-", "-|-", 1)
    for line in lines:
        if "|" in line:
            cells = [c.strip() for c in line.strip("\n|").split("|")]
            appendix = [" "] * (cols_num - len(cells))
            cells.extend(appendix)
            cells[0] = "**%s**" % cells[0]
            table_md += "| %s |\n" % " | ".join(cells)
    table_md += "\n"
    return table_md

def to_ds(site):
    rsite = ""
    for nucl in site[::-1]:
        rsite += compls.get(nucl, "?")
    return (min(site, rsite), max(site, rsite))

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

def format_count(count, extra_space):
    count_str = "{0:.%df}{1:s}"
    rank = ""
    if count >= 1000000:
        rank = "M"
        count /= 1000000.0
    elif count >= 1000:
        rank = "k"
        count /= 1000.0
    precision = 0
    if rank:
        precision = max(0, 2 - len(str(count).split(".")[0]) + extra_space)
    count_str = count_str % precision
    return count_str.format(count, rank or " ")

def get_value_str(count, total, value_str, extra_space):
    percent = (100.0 * count / total) if total else 0
    if extra_space is None:
        count_str = "{:d}".format(count)
    else:
        count_str = format_count(count, extra_space)
    return value_str.format(count=count_str, percent=percent)

def calc_stat(stat_list, tag, value_str, extra_space, joint_groups=None):
    _get_value_str = lambda count, total: get_value_str(
            count, total, value_str, extra_space
            )
    stat = dict()
    total = sum(stat_list)
    nan, unr, zero, under, less, one, more, over = stat_list
    bad = nan + unr
    norm = less + one + more
    under += zero
    less += under
    more += over
    if joint_groups:
        total -= sum(joint_groups.values())
        for (g1, g2), count in joint_groups.items():
            if g1 == NAN or g1 == UNR:
                bad -= count
        under -= joint_groups[(ZERO, UNDER)]
        less -= joint_groups[(ZERO, UNDER)]
        less -= joint_groups[(ZERO, LESS)]
        less -= joint_groups[(UNDER, LESS)]
        more -= joint_groups[(MORE, OVER)]
        norm -= joint_groups[(LESS, ONE)]
        norm -= joint_groups[(LESS, MORE)]
        norm -= joint_groups[(ONE, MORE)]
    stat[tag+"_total"] = total
    good = total - bad
    for abr, count in zip(["nan", "unr", "rel"], [nan, unr, good]):
        stat["%s_%s" % (tag, abr)] = _get_value_str(count, total)
    for abr, count in zip(
            ["zer", "und", "les", "one", "mor", "ove", "nor"],
            [zero, under, less, one, more, over, norm]
            ):
        stat["%s_%s" % (tag, abr)] = _get_value_str(count, good)
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
    io_group.add_argument(
            "--force-short-counts", dest="shorten", action="store_true",
            help="use short number format even in markdown and html"
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
    # cutoff
    EXP_CUTOFF = args.exp_cutoff
    ZERO_CUTOFF = args.zero_cutoff
    UNDER_CUTOFF = args.under_cutoff
    OVER_CUTOFF = args.over_cutoff
    # indices
    site_index = args.site_index
    id_index = args.id_index
    exp_index = args.exp_index
    obs_index = args.obs_index
    if obs_index is None:
        obs_index = exp_index - 1
    # format
    fill = 0
    out_format = args.format
    if not out_format:
        out_name = args.out.name
        if out_name.endswith(".md"):
            out_format = "md"
        elif out_name.endswith(".html"):
            out_format = "html"
        else:
            out_format = "raw"
    md = out_format != "raw"
    if md:
        if not args.shorten:
            fill = None
        title_str = "\n\n##{}##\n\n"
        stats_str = raw_table_to_markdown(stats_str)
        stats_val_str = "{count} ({percent:.1f}%)"
        groups_str = raw_table_to_markdown(groups_str)
        groups_num_str = "{count}"
        groups_prc_str = "{percent:.1f}%"
    # collect stats
    waits = dict()
    p_stat = [0] * 8
    s_stat = [0] * 8
    d_stat = [0] * 8
    d_groups = Counter()
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
                        s_stat[group] += 2
                    else:
                        d_stat[group] += 1
                        d_stat[cgroup] += 1
                        d_groups[tuple(sorted([group, cgroup]))] += 1
                else:
                    waits[pr] = group
            else:
                p_stat[group] += 1
    i_stat = [0] * 8
    for group in waits.values():
        i_stat[group] += 1
    # calculate stats
    #    single-stranded sites
    n_stat = list(map(sum, zip(s_stat, d_stat, i_stat)))
    a_stat = list(map(sum, zip(p_stat, n_stat)))
    stats_dct = dict()
    for abr, stat in zip(
            ["all", "pal", "npl", "sam", "dif", "inc"],
            [a_stat, p_stat, n_stat, s_stat, d_stat, i_stat]
            ):
        stats_dct.update(calc_stat(stat, abr, stats_val_str, fill))
    total = stats_dct["all_total"]
    for abr in ["all", "pal", "npl", "sam", "dif", "inc"]:
        count = stats_dct["%s_total" % abr]
        t_str = get_value_str(count, total, stats_val_str, fill)
        stats_dct["%s_tot" % abr] = t_str
    oustr = title_str.format(
            "Single-stranded site representation statistics"
            )
    oustr += stats_str.format(**stats_dct)
    #    double-stranded sites
    s_stat = [val // 2 for val in s_stat]
    stats_dct.update(calc_stat(s_stat, "sam", stats_val_str, fill))
    n_stat = list(map(sum, zip(s_stat, d_stat, i_stat)))
    a_stat = list(map(sum, zip(p_stat, n_stat)))
    for abr, stat in zip(["all", "npl", "dif"], [a_stat, n_stat, d_stat]):
        stats_dct.update(
                calc_stat(stat, abr, stats_val_str, fill, d_groups)
                )
    total = stats_dct["all_total"]
    for abr in ["all", "pal", "npl", "sam", "dif", "inc"]:
        count = stats_dct["%s_total" % abr]
        t_str = get_value_str(count, total, stats_val_str, fill)
        stats_dct["%s_tot" % abr] = t_str
    oustr += title_str.format(
            "Double-stranded site representation statistics"
            )
    oustr += stats_str.format(**stats_dct)
    #    joint groups for assymetric sites, counts
    if fill is not None:
        fill += 1
    groups_dct = dict()
    total = sum(d_groups.values())
    group_abrs = ["na", "lo", "ze", "un", "le", "on", "mo", "ov"]
    for g1 in range(len(group_abrs)):
        for g2 in range(g1 + 1, len(group_abrs)):
            if (g1, g2) not in d_groups:
                d_groups[(g1, g2)] = 0
    groups_totals = Counter()
    for (g1, g2), count in d_groups.items():
        groups_totals[g1] += count
        groups_totals[g2] += count
        abr = "%s_%s" % (group_abrs[g1], group_abrs[g2])
        groups_dct[abr] = get_value_str(count, total, groups_num_str, fill)
    for g, count in groups_totals.items():
        abr = "%s_to" % group_abrs[g]
        groups_dct[abr] = get_value_str(count, total, groups_num_str, fill)
    oustr += title_str.format(
            "Joint groups statistics for assymetric sites, counts"
            )
    oustr += groups_str.format(**groups_dct)
    #    joint groups for assymetric sites, percents
    for (g1, g2), count in d_groups.items():
        abr = "%s_%s" % (group_abrs[g1], group_abrs[g2])
        groups_dct[abr] = get_value_str(count, total, groups_prc_str, fill)
    for g, count in groups_totals.items():
        abr = "%s_to" % group_abrs[g]
        groups_dct[abr] = get_value_str(count, total, groups_prc_str, fill)
    oustr += title_str.format(
            "Joint groups statistics for assymetric sites, percents"
            )
    oustr += groups_str.format(**groups_dct)
    if not md:
        oustr = oustr.replace("100.0", " 100")
        oustr = oustr.replace("0   0.0", " --    ")
    with args.out as out:
        if out_format == "html":
            html = markdown.markdown(oustr, extensions=[TableExtension()])
            oustr = html_seed.replace("@stat", html)
        out.write(oustr)

