#! /usr/bin/env python

"""Calculate numbers of absent and under-represented sites."""

import argparse
from collections import Counter
import math
#from os.path import basename
import signal
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


def normalize_counts(counts, total):
    zeros = counts["zeros"]
    zeros_f = zeros * 100.0 / total
    good = total - counts["bad"]
    good_f = good * 100.0 / total
    good_zeros = zeros - counts["missed_zeros"]
    good_zeros_f = good_zeros * 100.0 / (good or 1)
    unders = counts["under"]
    unders_f = unders * 100.0 / (good or 1)
    less = unders + counts["less"]
    less_f = less * 100.0 / (good or 1)
    return (
        zeros, zeros_f, good, good_f, good_zeros,
        good_zeros_f, unders, unders_f, less, less_f
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Get numbers of absent and under-represented sites.",
        add_help=False
    )
    io_group = parser.add_argument_group("Input/output arguments")
    io_group.add_argument(
        "intsv", metavar="FILE", type=argparse.FileType("r"),
        help="input file with compositional bias values"
    )
    io_group.add_argument(
        "-o", dest="outsv", metavar="FILE", type=argparse.FileType("w"),
        default=sys.stdout, help="output file name"
    )
    io_group.add_argument(
        "-m", "--group-by", choices=["site", "id"], default="id",
        help="group by sites or sequence IDs, the second is default"
    )
    io_group.add_argument(
        "-c", "--summarize", action="store_true",
        help="calculate grand total"
    )
    filter_group = parser.add_argument_group("Filters")
    filter_group.add_argument(
        "-s", dest="instl", metavar="LIST", type=argparse.FileType("r"),
        help="input list of sites to filter by"
    )
    filter_group.add_argument(
        "-a", dest="inacv", metavar="LIST", type=argparse.FileType("r"),
        help="input list of sequence IDs to filter by"
    )
    cutoff_group = parser.add_argument_group("Cutoffs")
    cutoff_group.add_argument(
        "-e", "--exp-cutoff", metavar="FLOAT", type=float, default=15.0,
        help="reliable expected number cutoff, default 15"
    )
    cutoff_group.add_argument(
        "-z", "--zero-cutoff", metavar="INT", type=int, default=0,
        help="zero observed number cutoff, default 0"
    )
    cutoff_group.add_argument(
        "-u", "--under-cutoff", metavar="FLOAT", type=float, default=0.78,
        help="under-representation cutoff, default 0.78"
    )
    index_group = parser.add_argument_group("Column indices")
    index_group.add_argument(
        "-I", "--id-index", metavar="N", type=int, default=0,
        help="site column index, default 0"
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
    parser.add_argument(
        "-h", "-?", "-help", "--help", action="help",
        help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)
    group_by_id = args.group_by == "id"
    summarize = args.summarize
    metadata = [
        "##### %s\n"
        "##\n"
        "## Count excluded/underrepresented sites, and sites\n"
        "## with decreased frequencies.\n"
        "##\n"
        "## --- Main parameters ---\n"
        "## Source file name: %s\n"
        "## Group by: %s\n"
        "## With summary: %s\n"
        "##\n" % (parser.prog, args.intsv.name, args.group_by, summarize)
    ]
    indices = (args.id_index, args.site_index,
               args.obs_index, args.exp_index)
    metadata.append((
        "## --- Column indices ---\n"
        "## Sequence ID: %d\n"
        "## Site: %d\n"
        "## Observed: %d\n"
        "## Expected: %d\n"
        "##\n"
    ) % indices)
    sids = load_list(args.inacv)
    sites = load_list(args.instl)
    metadata.append((
        "## --- Line filters ---\n"
        "## Sequence ID filter: %s\n"
        "## Site filter: %s\n"
        "##\n"
    ) % (
        args.inacv.name if sids else None,
        args.instl.name if sites else None
    ))
    cutoffs = (args.exp_cutoff, args.zero_cutoff, args.under_cutoff)
    metadata.append((
        "## --- Site groups ---\n"
        "## Reliable: expected > %.1f\n"
        "## Excluded: observed <= %d\n"
        "## Avoided: CB <= %.2f\n"
        "## Decreased: CB < 1.0\n"
        "##\n"
        "#####\n"
    ) % cutoffs)
    line_parser = LineParser(indices, cutoffs)
    values = dict()
    totals = Counter()
    with args.intsv as intsv:
        for line in intsv:
            if line.startswith("#"):
                if line.startswith("##"):
                    metadata.append(line)
                continue
            sid, site, is_zero, status = line_parser(line)
            if sids and sid not in sids:
                continue
            if sites and site not in sites:
                continue
            key = sid if group_by_id else site
            counts = values.setdefault(key, Counter())
            totals[key] += 1
            counts[status] += 1
            if is_zero:
                counts["zeros"] += 1
                if status == "bad":
                    counts["missed_zeros"] += 1
    with args.outsv as outsv:
        outsv.writelines(metadata)
        outsv.write("#:Sequence ID\t" if group_by_id else "#:Site\t")
        outsv.write(
            "Total\tExcluded\tExcluded, %\tReliable\tReliable, %\t"
            "Excluded reliable\tExcluded reliable, %\t"
            "Avoided\tAvoided, %\tDecreased\tDecreased, %\n"
        )
        ouline = "%s\t%d" + "\t%d\t%.1f" * 5 + "\n"
        for key in sorted(values):
            total = totals[key]
            outsv.write(ouline % (
                (key, total) + normalize_counts(values[key], total)
            ))
        if summarize:
            total_counts = Counter()
            for counts in values.values():
                total_counts.update(counts)
            total = sum(totals.values())
            outsv.write(ouline % (
                ("Total:", total) + normalize_counts(total_counts, total)
            ))


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

