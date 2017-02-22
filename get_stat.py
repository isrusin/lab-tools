#! /usr/bin/env python

import argparse
from collections import Counter
import markdown
import math
from markdown.extensions.tables import TableExtension
from os.path import splitext
import sys


NAN = 0
UNR = 1
ZERO = 2
UNDER = 3
LESS = 4
ONE = 5
MORE = 6
OVER = 7

CBSTAT_STUB = """
      |    All   |Palindrome|Asymmetric| Coinside |  Differ  |Incomplete
------+----------+----------+----------+----------+----------+----------
Total | {all_tot}| {pal_tot}| {npl_tot}| {sam_tot}| {dif_tot}| {inc_tot}
------+----------+----------+----------+----------+----------+----------
NaN   | {all_nan}| {pal_nan}| {npl_nan}| {sam_nan}| {dif_nan}| {inc_nan}
Low   | {all_unr}| {pal_unr}| {npl_unr}| {sam_unr}| {dif_unr}| {inc_unr}
Good  | {all_rel}| {pal_rel}| {npl_rel}| {sam_rel}| {dif_rel}| {inc_rel}
------+----------+----------+----------+----------+----------+----------
 <1   | {all_les}| {pal_les}| {npl_les}| {sam_les}| {dif_les}| {inc_les}
  1   | {all_one}| {pal_one}| {npl_one}| {sam_one}| {dif_one}| {inc_one}
 >1   | {all_mor}| {pal_mor}| {npl_mor}| {sam_mor}| {dif_mor}| {inc_mor}
------+----------+----------+----------+----------+----------+----------
  0   | {all_zer}| {pal_zer}| {npl_zer}| {sam_zer}| {dif_zer}| {inc_zer}
Under | {all_und}| {pal_und}| {npl_und}| {sam_und}| {dif_und}| {inc_und}
Norm  | {all_nor}| {pal_nor}| {npl_nor}| {sam_nor}| {dif_nor}| {inc_nor}
Over  | {all_ove}| {pal_ove}| {npl_ove}| {sam_ove}| {dif_ove}| {inc_ove}
"""

JGSTAT_STUB = """
      |  NaN  |  Low  |   0   | Under |   <1  |   1   |   >1  |  Over |
------+-------+-------+-------+-------+-------+-------+-------+-------+
Total |{na_to}|{lo_to}|{ze_to}|{un_to}|{le_to}|{on_to}|{mo_to}|{ov_to}|
------+-------+-------+-------+-------+-------+-------+-------+-------'
Over  |{na_ov}|{lo_ov}|{ze_ov}|{un_ov}|{le_ov}|{on_ov}|{mo_ov}|
------+-------+-------+-------+-------+-------+-------+-------'
 >1   |{na_mo}|{lo_mo}|{ze_mo}|{un_mo}|{le_mo}|{on_mo}|
------+-------+-------+-------+-------+-------+-------'
  1   |{na_on}|{lo_on}|{ze_on}|{un_on}|{le_on}|
------+-------+-------+-------+-------+-------'
 <1   |{na_le}|{lo_le}|{ze_le}|{un_le}|
------+-------+-------+-------+-------'
Under |{na_un}|{lo_un}|{ze_un}|
------+-------+-------+-------'
  0   |{na_ze}|{lo_ze}|
------+-------+-------'
Low   |{na_lo}|
------+-------'
"""

HTML_SEED = """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>CBstat</title>
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

def table_to_markdown(table):
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

def fill_value_str(count, total, value_str, extra_space=None):
    percent = (100.0 * count / total) if total else 0
    if extra_space is None:
        count_str = "{:d}".format(count)
    else:
        count_str_stub = "{0:.%df}"
        rank = ""
        if count >= 1000000:
            rank = "M"
            count /= 1000000.0
        elif count >= 1000:
            rank = "k"
            count /= 1000.0
        precision = 0
        if rank:
            precision = max(0, 2 - len(str(int(count))) + extra_space)
        count_str_stub = count_str_stub % precision
        count_str = count_str_stub.format(count)
        if len(count_str) > 3 + extra_space:
            count_str = count_str[:-1].strip(".")
        count_str += (rank or " ")
    return value_str.format(count=count_str, percent=percent)

def to_ds(site):
    compls = {
        "A": "T", "T": "A", "C": "G", "G": "C",
        "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
        "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
    }
    rsite = ""
    for nucl in site[::-1]:
        rsite += compls.get(nucl, "?")
    return min(site, rsite), max(site, rsite)

def parse_line(line, indices):
    id_index, site_index, obs_index, exp_index = indices
    vals = line.strip().split("\t")
    sid = vals[id_index]
    site = to_ds(vals[site_index])
    obs = float(vals[obs_index])
    exp = float(vals[exp_index])
    return sid, site, obs, exp

def classify(obs, exp, cutoffs):
    exp_cutoff, zero_cutoff, under_cutoff, over_cutoff = cutoffs
    group = ONE
    if math.isnan(exp) or math.isinf(exp) or exp == 0:
        group = NAN
    elif exp <= exp_cutoff:
        group = UNR
    else:
        ratio = obs / exp
        if ratio < 1.0:
            if ratio <= zero_cutoff:
                group = ZERO
            elif ratio <= under_cutoff:
                group = UNDER
            else:
                group = LESS
        elif ratio > 1.0:
            if ratio >= over_cutoff:
                group = OVER
            else:
                group = MORE
    return group

def collect_stat(intsv, line_parser_func, classify_func):
    stats = {
        "pal": [0] * 8, # palindromes
        "sam": [0] * 8, # coinside
        "dif": [0] * 8, # differ
        "inc": [0] * 8, # incomplete
    }
    waits = dict()
    jg_stat = Counter()
    with intsv:
        intsv.readline()
        for line in intsv:
            sid, site, obs, exp = line_parser_func(line)
            wsite, csite = site
            group = classify_func(obs, exp)
            if wsite != csite:
                pr = (sid, site)
                if pr in waits:
                    cgroup = waits.pop(pr)
                    if cgroup == group:
                        stats["sam"][group] += 2
                    else:
                        stats["dif"][group] += 1
                        stats["dif"][cgroup] += 1
                        jg_stat[tuple(sorted([group, cgroup]))] += 1
                else:
                    waits[pr] = group
            else:
                stats["pal"][group] += 1
    for group in waits.values():
        stats["inc"][group] += 1
    stats["npl"] = [
        sum(v) for v in zip(stats["sam"], stats["dif"], stats["inc"])
    ]
    stats["all"] = [sum(v) for v in zip(stats["pal"], stats["npl"])]
    return stats, jg_stat

def calc_stat(stat_list, tag, value_str, extra_space, joint_groups=None):
    stat = dict()
    stat_key = tag + "_%s"
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
    stat[stat_key % "total"] = total
    good = total - bad
    abbrs = ("nan", "unr", "rel")
    counts = (nan, unr, good)
    for abr, count in zip(abbrs, counts):
        key = stat_key % abr
        stat[key] = fill_value_str(count, total, value_str, extra_space)
    abbrs = ("zer", "und", "les", "one", "mor", "ove", "nor")
    counts = (zero, under, less, one, more, over, norm)
    for abr, count in zip(abbrs, counts):
        key = stat_key % abr
        stat[key] = fill_value_str(count, good, value_str, extra_space)
    return stat

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Get site compositional bias statistics."
    )
    io_group = parser.add_argument_group("input/output arguments")
    io_group.add_argument(
        "intsv", metavar="INPUT", type=argparse.FileType("r"),
        help="input file with observed and expected numbers"
    )
    io_group.add_argument(
        "-o", "--out", metavar="OUTPUT", type=argparse.FileType("w"),
        default=sys.stdout, help="""output file, default stdout;
        note: .md and .html extensions will alter output format"""
    )
    io_group.add_argument(
        "-f", "--format", choices=["raw", "md", "html"],
        help="""output format: 'raw' - raw text, default; 'md' - markdown
        (GitHub dialect); 'html' - HTML, through markdown"""
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
        "column index arguments", description="""All column
        indices are counted from 0 and could be negative
        (-1 for the last column)."""
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
        "-O", "--obs-index", metavar="N", type=int, default=2,
        help="observed number column index, default 2"
    )
#   parser.add_argument("--no-id")
    args = parser.parse_args(argv)
    cutoffs = (
        args.exp_cutoff, args.zero_cutoff,
        args.under_cutoff, args.over_cutoff
    )
    cb_classifier = lambda obs, exp: classify(obs, exp, cutoffs)
    indices = (
        args.id_index, args.site_index, args.obs_index, args.exp_index
    )
    line_parser = lambda line: parse_line(line, indices)
    out_format = args.format
    if not out_format:
        out_format = "raw"
        out_ext = splitext(args.out.name)[-1]
        if out_ext in [".md", ".html"]:
            out_format = out_ext[1:]
    fill = 0 if out_format == "raw" or args.shorten else None
    return (args.intsv, line_parser, cb_classifier, fill,
            out_format, args.out)

def main(argv=None):
    intsv, parser, classifier, fill, out_format, out = parse_args(argv)
    title_str = "\n\n\t{}:\n"
    stats_str = CBSTAT_STUB
    stats_val_str = "{count:>4s} {percent:>4.1f}"
    make_markdown = out_format != "raw"
    if make_markdown:
        title_str = "\n\n##{}##\n\n"
        stats_str = table_to_markdown(stats_str)
        stats_val_str = "{count} ({percent:.1f}%)"
    # collect stats
    stats, jg_stat = collect_stat(intsv, parser, classifier)
    #    single-stranded sites
    stats_dct = dict()
    for abbr, stat in stats.items():
        stats_dct.update(calc_stat(stat, abbr, stats_val_str, fill))
    total = stats_dct["all_total"]
    for abbr in stats.keys():
        count = stats_dct["%s_total" % abbr]
        t_str = fill_value_str(count, total, stats_val_str, fill)
        stats_dct["%s_tot" % abbr] = t_str
    oustr = title_str.format(
        "Compositional bias statistics, single-stranded sites"
    )
    oustr += stats_str.format(**stats_dct)
    #    double-stranded sites
    stats["sam"] = [val // 2 for val in stats["sam"]]
    stats_dct.update(calc_stat(stats["sam"], "sam", stats_val_str, fill))
    stats["npl"] = [
        sum(v) for v in zip(stats["sam"], stats["dif"], stats["inc"])
    ]
    stats["all"] = [sum(v) for v in zip(stats["pal"], stats["npl"])]
    for abbr in ["all", "npl", "dif"]:
        stats_dct.update(
            calc_stat(stats[abbr], abbr, stats_val_str, fill, jg_stat)
        )
    total = stats_dct["all_total"]
    for abbr in stats.keys():
        count = stats_dct["%s_total" % abbr]
        t_str = fill_value_str(count, total, stats_val_str, fill)
        stats_dct["%s_tot" % abbr] = t_str
    oustr += title_str.format(
        "Compositional bias statistics, double-stranded sites"
    )
    oustr += stats_str.format(**stats_dct)
    if not make_markdown:
        oustr = oustr.replace("100.0", " 100")
        oustr = oustr.replace("0   0.0", " --    ")
    #    joint groups for assymetric sites
    oustr += joint_groups_statistics(jg_stat, fill, make_markdown)
    with out:
        if out_format == "html":
            html_seed = HTML_SEED
            html = markdown.markdown(oustr, extensions=[TableExtension()])
            oustr = html_seed.replace("@stat", html)
        out.write(oustr)

def joint_groups_statistics(d_groups, fill, markdown=False, which="both"):
    stub = "\n\n\t{title}:\n" + JGSTAT_STUB
    num_str = "{count:>6s} "
    prc_str = "{percent:>5.1f}% "
    if markdown:
        stub = "\n\n##{title}##\n\n" + table_to_markdown(JGSTAT_STUB)
        num_str = "{count}"
        prc_str = "{percent:.1f}%"
    if fill is not None:
        fill += 1
    total = sum(d_groups.values())
    group_abbrs = ["na", "lo", "ze", "un", "le", "on", "mo", "ov", "to"]
    total_index = len(group_abbrs) - 1
    for g1 in range(total_index):
        for g2 in range(g1 + 1, total_index):
            if (g1, g2) not in d_groups:
                d_groups[(g1, g2)] = 0
            d_groups[(g1, total_index)] += d_groups[(g1, g2)]
            d_groups[(g2, total_index)] += d_groups[(g1, g2)]
    oustr = ""
    if which != "percents":
        oustr += group_statistics_str(
            d_groups, group_abbrs, stub,
            lambda val: fill_value_str(val, total, num_str, fill)
        )
    if which != "counts":
        oustr += group_statistics_str(
            d_groups, group_abbrs, stub,
            lambda val: fill_value_str(val, total, prc_str, fill)
        )
    if not markdown:
        oustr = oustr.replace("100.0", "  100")
    return oustr

def group_statistics_str(d_groups, abbrs, stub, str_value):
    vals_dct = {"title": "Joint groups statistics for assymetric sites"}
    for groups, count in d_groups.items():
        abbr = "_".join(abbrs[group] for group in groups)
        vals_dct[abbr] = str_value(count)
    return stub.format(**vals_dct)


if __name__ == "__main__":
    sys.exit(main())
