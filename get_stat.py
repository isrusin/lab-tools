#! /usr/bin/env python

import argparse
import markdown
import math
import sys

from collections import Counter
from markdown.extensions.tables import TableExtension
from os.path import splitext


NAN, UNR, ZERO, UNDER, OVER, LESS, MORE, ONE = (0, 1, 2, 3, 4, 5, 6, 7)
ABBRS = ["nan", "low", "zer", "und", "ove", "les", "mor", "one"]

COMPLS = {"A": "T", "T": "A", "C": "G", "G": "C",
          "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
          "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"}

CBCOLS = {
    "A": ("All", "all"), "P": ("Palindrome", "pal"),
    "N": ("Asymmetric", "npl"), "C": ("Coinside", "sam"),
    "D": ("Differ", "dif"), "I": ("Incomplete", "inc")
}

CBROWS = {
    "T": [("Total", "tot")],
    "R": [("NaN", "nan"), ("Low", "low"), ("Good", "rel")],
    "O": [("<1", "les"), ("1", "one"), (">1", "mor")],
    "N": [("0", "zer"), ("Under", "und"), ("Norm", "nor"),("Over", "ove")]
}

def get_rows_by_abbrs(abbrs):
    rows = []
    for abbr in abbrs:
        rows.extend(CBROWS[abbr])
        rows.append(None)
    return rows[:-1]

JGCOLS = (("NaN", "nan"), ("Low", "low"), ("0", "zer"), ("Under", "und"),
          ("<1", "les"), ("1", "one"), (">1", "mor"), ("Over", "ove"))

JGROWS = JGCOLS + (None, ("Total", "tot"))

HTML_SEED = """\
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>CBstat</title>
    <style type="text/css">
      table {{
        border-collapse: collapse;
      }}
      td, th {{
        padding: 1mm 3mm 1mm 3mm;
        border: 1px solid black;
      }}
      th {{
        background: #ccffff;
        text-align: center;
      }}
    </style>
  </head>
  <body>@stat
  </body>
</html>
"""

TITLE_STUBS = {"raw": "\n\t{}:\n\n", "tsv": "##\n##{}\n",
               "md": "##{}##\n\n", "html": "\n    <h2>{}</h2>\n"}

def make_raw_table_stub(columns, rows, spacer="_",
                        lab_width=6, cell_width=10):
    cell = "{{%s{spacer}{abbr}:>%d}}"
    title = [" " * lab_width]
    row_stub = ["{name:<%d}" % lab_width]
    empty = ["-" * lab_width]
    for name, abbr in columns:
        title.append(name.center(cell_width))
        row_stub.append(cell % (abbr, cell_width))
        empty.append("-" * cell_width)
    empty = "+".join(empty) + "\n"
    row_stub = "|".join(row_stub) + "\n"
    table = ["|".join(title), "\n", empty]
    for row in rows:
        if row:
            name, abbr = row
            table.append(row_stub.format(
                name=name, abbr=abbr, spacer=spacer
            ))
        else:
            table.append(empty)
    return "".join(table)

def make_tsv_table_stub(columns, rows, spacer="_",
                        lab_width=None, cell_width=None):
    title = ["#"]
    row_stub = ["{name}"]
    for name, abbr in columns:
        title.append(name)
        row_stub.append("{{%s%s{abbr}}}" % (abbr, spacer))
    row_stub = "\t".join(row_stub) + "\n"
    table = ["\t".join(title), "\n"]
    for row in rows:
        if not row:
            continue
        name, abbr = row
        table.append(row_stub.format(name=name, abbr=abbr))
    return "".join(table)

def make_md_table_stub(columns, rows, spacer="_",
                       lab_width=None, cell_width=None):
    cell = " {%s" + spacer + "%s} |"
    table = ["| | ", " | ".join(name for name, abbr in columns), " |\n"]
    table.extend(
        ["|:-|-", ":|-".join("-" * len(col) for col, _ in columns), ":|\n"]
    )
    for row in rows:
        if row:
            name, abbr = row
            table.append("| **%s** |" % name)
            table.extend(cell % (cabbr, abbr) for _, cabbr in columns)
            table.append("\n")
    table.append("\n\n")
    return "".join(table)

def make_html_table_stub(columns, rows, spacer="_",
                         lab_width=None, cell_width=None):
    md_stub = make_md_table_stub(
        columns, rows, spacer=spacer,
        lab_width=lab_width, cell_width=cell_width
    )
    return markdown.markdown(md_stub, extensions=[TableExtension()])

TABLE_MAKERS = {"raw": make_raw_table_stub, "tsv": make_tsv_table_stub,
               "md": make_md_table_stub, "html": make_html_table_stub}

def compress(num, width=4, suffix=" "):
    rank = 0
    while num >= 1000:
        num = num / 1000.0
        rank += 1
    suffixes = [suffix, "k", "M", "G", "T", "P", "E", "Z", "Y"]
    prec = max(0, width - len("%.0f" % num) - 1)
    stub = "{:>%d.%df}%s" % (width, prec, suffixes[rank])
    return stub.format(num)

def formatter(count, total, skip_zeros=False,
              keep_count=True, count_width=None, count_suffix=" ",
              keep_perc=True, perc_width=None, perc_suffix=""):
    vals = []
    if keep_count:
        count_str = "%d" % count
        if count_width:
            count_str = compress(count, count_width, count_suffix)
        vals.append(count_str)
    if keep_perc:
        perc = (count * 100.0 / total) if total else 0
        perc_str = "(%.1f%%)" % perc
        if perc_width:
            perc_str = compress(perc, perc_width, perc_suffix)
        vals.append(perc_str)
    answer = " ".join(vals)
    if skip_zeros and set(answer).issubset({" ", "0", ".", "%", "(", ")"}):
        answer = " " * len(answer)
    return answer

class FormatManager(object):
    def __init__(self, out_format, cbsection="both", jgsection="both",
                 cbcols="PSD", cbrows="TRON", shorten_vals=True):
        title_stub = TITLE_STUBS[out_format]
        stub_maker = TABLE_MAKERS[out_format]
        self.shorten_vals = shorten_vals or out_format == "raw"
        if jgsection == "both" and self.shorten_vals:
            jgsection = "counts"
        self.jgsection = jgsection
        cbrows = get_rows_by_abbrs(cbrows)
        cbstat_ss_stub = stub_maker(
            [CBCOLS[abbr] for abbr in cbcols], cbrows
        )
        cbstat_ds_stub = stub_maker(
            [CBCOLS[abbr] for abbr in cbcols if abbr != "I"],
            cbrows, spacer="2"
        )
        jgstat_stub = stub_maker(JGCOLS, JGROWS, cell_width=7)
        output_stub = ""
        if cbsection:
            if cbsection != "ds":
                output_stub += title_stub.format(
                    "Compositional bias statistics, single-stranded sites"
                ) + cbstat_ss_stub
            if cbsection != "ss":
                output_stub += title_stub.format(
                    "Compositional bias statistics, double-stranded sites"
                ) + cbstat_ds_stub
        if jgsection:
            output_stub += title_stub.format(
                "Joint groups statistics for assymetric sites"
            ) + jgstat_stub
        if out_format == "html":
            output_stub = HTML_SEED.replace("@stat", output_stub)
        self.output_stub = output_stub
        self.prepare_formatters()

    def prepare_formatters(self):
        self.cbformatter = formatter
        self.jgformatter = lambda count, total: formatter(
            count, total,
            keep_count=(self.jgsection != "percents"),
            keep_perc=(self.jgsection != "counts")
        )
        if self.shorten_vals:
            self.cbformatter = lambda count, total: formatter(
                count, total, count_width=3, perc_width=4, skip_zeros=True
            )
            self.jgformatter = lambda count, total: formatter(
                count, total, count_width=1, perc_width=4,
                keep_count=(self.jgsection != "percents"),
                keep_perc=(self.jgsection != "counts"),
                perc_suffix="%", skip_zeros=True
            ) + " "

    def make_output(self, cbvals, jgvals):
        prepared_vals = dict(
            (k, self.cbformatter(*v)) for k, v in cbvals.items()
        )
        prepared_vals.update(
            (k, self.jgformatter(*v)) for k, v in jgvals.items()
        )
        return self.output_stub.format(**prepared_vals)

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

def collect_stat(intsv, line_parser):
    cbstat_ss = {
        "pal": [0] * len(ABBRS), # palindromes
        "sam": [0] * len(ABBRS), # coinside
        "dif": [0] * len(ABBRS), # differ
        "inc": [0] * len(ABBRS), # incomplete
    }
    waits = dict()
    jgstat = Counter()
    with intsv:
        intsv.readline()
        for line in intsv:
            sid, site, group = line_parser(line)
            wsite, csite = site
            if wsite != csite:
                pr = (sid, site)
                if pr in waits:
                    cgroup = waits.pop(pr)
                    if cgroup == group:
                        cbstat_ss["sam"][group] += 2
                    else:
                        cbstat_ss["dif"][group] += 1
                        cbstat_ss["dif"][cgroup] += 1
                        if group < cgroup:
                            jgstat[(group, cgroup)] += 1
                        else:
                            jgstat[(cgroup, group)] += 1
                else:
                    waits[pr] = group
            else:
                cbstat_ss["pal"][group] += 1
    for group in waits.values():
        cbstat_ss["inc"][group] += 1
    cbstat_ds = dict()
    cbstat_ds["pal"] = cbstat_ss["pal"]
    cbstat_ds["sam"] = [val//2 for val in cbstat_ss["sam"]]
    cbstat_ds_dif = [0] * len(ABBRS)
    for (group, _group), count in jgstat.items():
        cbstat_ds_dif[group] += count # difs counted into major group
    cbstat_ds["dif"] = cbstat_ds_dif
    return cbstat_ss, cbstat_ds, jgstat

def summarize_cbstat(cbstat, spacer="_"):
    vals = dict()
    clusters = dict()
    for group_abbr, counts in cbstat.items():
        counter = Counter()
        for count, abbr in zip(counts, ABBRS):
            counter[abbr] += count
        counter["tot"] = sum(counter.values())
        counter["rel"] = counter["tot"] - (counter["nan"] + counter["low"])
        counter["nor"] = counter["les"] + counter["one"] + counter["mor"]
        counter["und"] += counter["zer"]
        counter["les"] += counter["und"]
        counter["mor"] += counter["ove"]
        clusters[group_abbr] = counter
    clusters["npl"] = clusters["sam"].copy()
    clusters["npl"].update(clusters["dif"])
    if "inc" in clusters:
        clusters["npl"].update(clusters["inc"])
    clusters["all"] = clusters["pal"].copy()
    clusters["all"].update(clusters["npl"])
    total = clusters["all"]["tot"]
    for group_abbr, counter in clusters.items():
        group_total = counter["tot"]
        group_good = counter["rel"]
        for abbr, count in counter.items():
            key = spacer.join([group_abbr, abbr])
            if abbr == "tot":
                vals[key] = (count, total)
            elif abbr in ["nan", "low", "rel"]:
                vals[key] = (count, group_total)
            else:
                vals[key] = (count, group_good)
    return vals

def summarize_jgstat(jgstat, spacer="_"): # jgstat is a Counter instance
    total = sum(jgstat.values()) * 2
    group_totals = Counter()
    for (group1, group2), count in jgstat.items():
        group_totals[ABBRS[group1]] += count
        group_totals[ABBRS[group2]] += count
    vals = dict()
    for i, abbr1 in enumerate(ABBRS):
        group_total = group_totals[abbr1]
        vals[abbr1 + spacer + "tot"] = (group_total, total)
        for j, abbr2 in enumerate(ABBRS):
            value = jgstat[(i, j) if i < j else (j, i)]
            vals[abbr1 + spacer + abbr2] = (value, group_total)
    return vals

def main(argv=None):
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
        "-f", "--format", choices=["raw", "tsv", "md", "html"],
        help="""output format: 'raw' - raw text, default; 'tsv' - TSV;
        'md' - markdown (GitHub dialect); 'html' - HTML, through md"""
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
    struct_group = parser.add_argument_group("output structure arguments")
    struct_group.add_argument(
        "--cb-stat", choices=["ss", "ds", "both", "none"], default="both",
        help="""which compositional bias statistics to provide:
        ss (single-stranded), ds (double-stranded), or both (default)"""
    )
    struct_group.add_argument(
        "--jg-stat", choices=["counts", "percents", "both", "none"],
        default="both", help="""which joint-group statistics to provide:
        counts, percents, both (default, counts in case of raw output)"""
    )
    struct_group.add_argument(
        "--cols", "--columns", dest="cbcols", metavar="ABBRS",
        default="APNCDI", help="""columns of CBstat table: A - all,
        P - palindromes, N - assymetric, C - coinside, D - differ,
        I - incomplete (only is 'ss' mode); default is APNCDI"""
    )
    struct_group.add_argument(
        "--rows", dest="cbrows", metavar="ABBRS", default="TRON",
        help="""row groups of CBstat table: T - total, R - reliability
        group, O - 'compare with 1' group, N - normal (zero, under, normal,
        over) group; default is TRON"""
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
    # output format
    out_format = args.format
    if not out_format:
        out_format = "raw"
        out_ext = splitext(args.out.name)[-1]
        if out_ext in [".md", ".tsv", ".html"]:
            out_format = out_ext[1:]
    # output sections
    cbsection = args.cb_stat
    if cbsection == "none":
        cbsection = None
    jgsection = args.jg_stat
    if jgsection == "none":
        jgsection = None
    format_manager = FormatManager(
        out_format, shorten_vals=args.shorten,
        cbsection=cbsection, jgsection=jgsection,
        cbcols=args.cbcols, cbrows=args.cbrows
    )
    # collect stats
    cbstat_ss, cbstat_ds, jgstat = collect_stat(args.intsv, line_parser)
    cbvals = summarize_cbstat(cbstat_ss)
    cbvals.update(summarize_cbstat(cbstat_ds, spacer="2"))
    jgvals = summarize_jgstat(jgstat)
    with args.out as out:
        out.write(format_manager.make_output(cbvals, jgvals))

if __name__ == "__main__":
    sys.exit(main())
