#! /usr/bin/env python

"""Add or remove complement sites."""

import argparse
import signal
import sys

_ADD = 0
_REVERSE = 1
_WATSON = 2
_CRICK = 3
_ISPAL = 4

COMPLS = {
    "A": "T", "T": "A", "C": "G", "G": "C",
    "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
    "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
}

def get_site_versions(site):
    """Get all versions of double-stranded site."""
    rsite = "".join([COMPLS.get(nucl, "?") for nucl in site[::-1]])
    watson = min(site, rsite)
    crick = max(site, rsite)
    ispal = watson == crick
    return site, rsite, watson, crick, ispal

def transform_tsv(intsv, action, sort=True, keep_repeats=False,
                  site_index=0, id_index=None, has_title=False):
    """Read and transform site list from file-like object."""
    if has_title:
        title = intsv.readline()
    lines = []
    uniqs = set()
    split_num = max(site_index, id_index) + 1
    for line in intsv:
        vals = line.strip().split("\t", split_num)
        site = vals[site_index]
        versions = get_site_versions(site)
        if id_index is None:
            uid = tuple(vals[:site_index] + vals[site_index+1:])
        else:
            uid = vals[id_index]
        uids = (versions[_WATSON], uid)
        if not keep_repeats:
            if uids in uniqs:
                continue
            uniqs.add(uids)
        vals[site_index] = versions[action]
        lines.append(vals)
        if action == _ADD and not versions[_ISPAL]:
            rvals = vals[:]
            rvals[site_index] = versions[_REVERSE]
            lines.append(rvals)
    if sort:
        lines = sorted(lines, key=lambda x: x[site_index])
    lines = ["\t".join(line) + "\n" for line in lines]
    if has_title:
        lines.insert(0, title)
    return lines

def main(argv=None):
    """Parse arguments and call transform_stl."""
    parser = argparse.ArgumentParser(
        description="Add or remove complement sites."
    )
    parser.add_argument(
        "intsv", metavar="FILE", type=argparse.FileType("r"),
        help="input table with sites, use '-' for STDIN"
    )
    out_group = parser.add_mutually_exclusive_group(required=False)
    out_group.add_argument(
        "-o", dest="outsv", metavar="FILE", type=argparse.FileType("w"),
        default=sys.stdout, help="output site list, default is STDOUT"
    )
    out_group.add_argument(
        "-i", "--in-place", dest="inplace", action="store_true",
        help="act in-place, STDOUT in case of STDIN"
    )
    parser.add_argument(
        "-t", "--title", dest="has_title", action="store_true",
        help="treat the first line of the input as a title (keep it)"
    )
    parser.add_argument(
        "-k", "--keep-order", dest="keep_order", action="store_true",
        help="keep order of lines, do not sort the output"
    )
    parser.add_argument(
        "-K", "--keep-repeats", dest="keep_repeats", action="store_true",
        help="keep repeated lines and their order"
    )
    parser.add_argument(
        "-s", "--site-index", dest="site_index", metavar="N", type=int,
        default=0, help="index of the site column, default 0"
    )
    parser.add_argument(
        "-u", "--uid-index", dest="id_index", metavar="N", type=int,
        help="index of the ID column, entire line is used as ID by default"
    )
    act_group = parser.add_mutually_exclusive_group(required=False)
    act_group.add_argument(
        "-A", "--add", dest="action", action="store_const",
        const=_ADD, help="add complementary sites to the list, default"
    )
    act_group.add_argument(
        "-R", "--reverse", dest="action", action="store_const",
        const=_REVERSE, help="replace each site with complementary one"
    )
    act_group.add_argument(
        "-W", "--watson", dest="action", action="store_const",
        const=_WATSON, help="""return only the first (alphabetically)
        site for each complementary pair"""
    )
    act_group.add_argument(
        "-C", "--crick", dest="action", action="store_const",
        const=_CRICK, help="""return only the last (alphabetically)
        site for each complementary pair"""
    )
    args = parser.parse_args(argv)
    keep_repeats = args.keep_repeats
    sort = not (args.keep_order or keep_repeats)
    with args.intsv as intsv:
        lines = transform_tsv(
            intsv, args.action or _ADD, has_title=args.has_title,
            sort=sort, keep_repeats=keep_repeats,
            site_index=args.site_index, id_index=args.id_index
        )
    outsv = args.outsv
    if args.inplace and intsv.name != "<stdin>":
        outsv = open(intsv.name, "w")
    with outsv:
        if outsv.name == "<stdout>":
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        outsv.writelines(lines)

if __name__ == "__main__":
    sys.exit(main())

