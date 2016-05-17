#! /usr/bin/python

import argparse as ap
import sys

nucls = ["A", "C", "G", "T"]

def elongate_sites(sites):
    new_sites = []
    for site in sites:
        for nucl in nucls:
            new_sites.append(site+nucl)
    return new_sites

if __name__ == "__main__":
    parser = ap.ArgumentParser(
            description="Generate list of all sites of the given length."
            )
    parser.add_argument(
            "-o", dest="oustl", metavar="FILE", type=ap.FileType("w"),
            default=sys.stdout, help="output .stl file, default stdout"
            )
    parser.add_argument(
            "--with-n", dest="with_n", action="store_true",
            help="use 5-letter alphabet [A, C, G, T, N]"
            )
    parser.add_argument(
            "length", metavar="LENGTH", type=int, choices=range(1, 11),
            help="length of sites, from 1 to 10, including both"
            )
    args = parser.parse_args()
    if args.with_n:
        nucls.append("N")
    sites = [""]
    for i in range(args.length):
        sites = elongate_sites(sites)
    if args.with_n:
        sites = sorted(set([site.strip("N") for site in sites]))
        sites.remove("")
    else:
        sites.sort()
    with args.oustl as oustl:
        oustl.write("\n".join(sites) + "\n")

