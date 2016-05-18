#! /usr/bin/python

import argparse as ap
import sys

compls = {
        "A": "T", "T": "A", "C": "G", "G": "C",
        "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
        "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
        }

_ADD = 0
_REVERSE = 1
_WATSON = 2
_CRICK = 3

def get_site_versions(site):
    rsite = ""
    for nucl in site[::-1]:
        rsite += compls.get(nucl, "?")
    return site, rsite, min(site, rsite), max(site, rsite)

if __name__ == "__main__":
    parser = ap.ArgumentParser(
            description="Add or remove complement sites."
            )
    parser.add_argument(
            "instl", metavar="IN_LIST", type=ap.FileType("r"),
            help="input site list, use '-' for stdin"
            )
    out_group = parser.add_mutually_exclusive_group(required=False)
    out_group.add_argument(
            "-o", dest="oustl", metavar="OU_LIST", type=ap.FileType("w"),
            default=sys.stdout, help="output site list, default stdout"
            )
    out_group.add_argument(
            "-i", "--in-place", dest="inplace", action="store_true",
            help="act in-place, stdout in case of stdin"
            )
    parser.add_argument(
            "-k", "--keep-order", dest="sort", action="store_false",
            help="keep order of sites, do not sort output"
            )
    act_group = parser.add_mutually_exclusive_group(required=False)
    act_group.add_argument(
            "-a", "--add", dest="action", action="store_const",
            const=_ADD, help="add complementary sites to the list, default"
            )
    act_group.add_argument(
            "-r", "--reverse", dest="action", action="store_const",
            const=_REVERSE, help="replace each site with complementary one"
            )
    act_group.add_argument(
            "-w", "--watson", dest="action", action="store_const",
            const=_WATSON, help="return only the first (alphabetically)" +
            " site for each complementary pair"
            )
    act_group.add_argument(
            "-c", "--crick", dest="action", action="store_const",
            const=_CRICK, help="return only the last (alphabetically)" +
            " site for each complementary pair"
            )
    args = parser.parse_args()
    action = args.action or _ADD
    sites = []
    with args.instl as instl:
        for line in instl:
            site_versions = get_site_versions(line.strip())
            sites.append(site_versions[action])
            if action == _ADD and site_versions[0] != site_versions[1]:
                sites.append(site_versions[1])
    if args.sort:
        sites = sorted(set(sites))
    oustl = args.oustl
    if args.inplace and instl.name != "<stdin>":
        oustl = open(instl.name, "w")
    with oustl:
        try:
            oustl.write("\n".join(sites) + "\n")
        except IOError:
            sys.stderr.write("Partial output!\n")
