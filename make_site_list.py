#! /usr/bin/python

"""Site list generator.

The tool generates a list of all sites of the given length or all sites
matching the specified template.
"""

import argparse as ap
from itertools import product
import re
import signal as sg
import sys

def mask_type(value):
    """Site template type."""
    length = value.count("X")
    if not 0 < length < 11:
        raise ap.ArgumentTypeError(
            "Bad site mask!\nThere should be 1 to 10 'X's in the mask."
        )
    mask = value.replace("%", "%%").replace("X", "%c")
    mask = mask.replace("{", "{{").replace("}", "}}")
    mask = re.sub(r"\d", lambda x: "{%s}" % x.group(0), mask)
    return mask, length

def generate_sites(length, with_n=False):
    """Return generator of all nucleotide combinations as tuples."""
    return product("ACGTN" if with_n else "ACGT", repeat=length)

def print_site_list(sites, oustl):
    """Write site list into file."""
    oustl.write("\n".join(sorted(sites)) + "\n")

def main():
    """Main function."""
    sg.signal(sg.SIGPIPE, sg.SIG_DFL)
    parser = ap.ArgumentParser(
        description="Make list of all sites of the given length or mask."
    )
    parser.add_argument(
        "-o", dest="oustl", metavar="FILE", type=ap.FileType("w"),
        default=sys.stdout, help="output .stl file, default stdout"
    )
    parser.add_argument(
        "--with-n", dest="with_n", action="store_true",
        help="""use 5-letter alphabet [A, C, G, T, N]; leading and trailing
        N symbols will be removed if LENGTH is specified but will not with
        --mask option"""
    )
    desc_group = parser.add_mutually_exclusive_group(required=True)
    desc_group.add_argument(
        "-m", "--mask", type=mask_type, default=(None, 0),
        help="""site template with X instead of any nucleotide
            (e.g. XXNNXX); digit from 1 to number of 'X's means complement
            to according 'X' position (e.g. XXNN21 is a palindrome)"""
    )
    desc_group.add_argument(
        "length", metavar="LENGTH", type=int, choices=range(1, 11),
        nargs="?", help="site length, from 1 to 10, including both"
    )
    args = parser.parse_args()
    mask = args.mask[0]
    length = args.length or args.mask[1]
    site_gen = generate_sites(length, args.with_n)
    sites = set()
    if mask:
        compls = {"A": "T", "C": "G", "G": "C", "T": "A", "N": "N"}
        for site_tuple in site_gen:
            site = mask % site_tuple
            if "{" in site:
                site = site.format("", *(compls[x] for x in site_tuple))
            sites.add(site)
    else:
        sites = set("".join(site).strip("N") for site in site_gen)
        sites.discard("")
    with args.oustl:
        print_site_list(sites, args.oustl)

if __name__ == "__main__":
    main()
