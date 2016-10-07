#! /usr/bin/python

"""Add or remove complement sites."""

import argparse as ap
import signal as sg
import sys

_ADD = 0
_REVERSE = 1
_WATSON = 2
_CRICK = 3

COMPLS = {
    "A": "T", "T": "A", "C": "G", "G": "C",
    "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
    "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
}

def get_site_versions(site):
    """Get all versions of double-stranded site."""
    rsite = "".join([COMPLS.get(nucl, "?") for nucl in site[::-1]])
    return site, rsite, min(site, rsite), max(site, rsite)

def transform_stl(instl, action, sort):
    """Read and transform site list from file-like object."""
    sites = []
    for line in instl:
        versions = get_site_versions(line.strip())
        sites.append(versions[action])
        if action == _ADD and versions[_WATSON] != versions[_CRICK]:
            sites.append(versions[_REVERSE])
    if sort:
        sites = sorted(set(sites))
    return sites

def main(args=None):
    """Parse arguments and call transform_stl."""
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
    params = parser.parse_args(args)
    action = params.action or _ADD
    sites = []
    with params.instl as instl:
        sites = transform_stl(instl, action, params.sort)
    oustl = params.oustl
    if params.inplace and instl.name != "<stdin>":
        oustl = open(instl.name, "w")
    with oustl:
        if oustl.name == "<stdout>":
            sg.signal(sg.SIGPIPE, sg.SIG_DFL)
        oustl.write("\n".join(sites) + "\n")

if __name__ == "__main__":
    sys.exit(main())

