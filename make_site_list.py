#! /usr/bin/python

import argparse as ap
import signal as sg
import sys

nucls = ["A", "C", "G", "T"]

def elongate_sites(sites):
    new_sites = []
    for site in sites:
        for nucl in nucls:
            new_sites.append(site+nucl)
    return new_sites

def _mask(value):
    length = value.count("X")
    if not 0 < length < 11:
        raise ap.ArgumentTypeError(
            "Bad site mask!\nThere should be 1 to 10 'X's in the mask."
        )
    return value

if __name__ == "__main__":
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
        "-m", "--mask", dest="mask", type=_mask,
        help="site blank with X instead of any nucleotide, e.g. XXNNXX"
        )
    desc_group.add_argument(
        "length", metavar="LENGTH", type=int, choices=range(1, 11),
        nargs="?", help="site length, from 1 to 10, including both"
    )
    args = parser.parse_args()
    if args.with_n:
        nucls.append("N")
    sites = [""]
    length = args.length or args.mask.count("X")
    for i in range(length):
        sites = elongate_sites(sites)
    if args.with_n and not args.mask:
        sites = sorted(set([site.strip("N") for site in sites]))
        sites.remove("")
    else:
        sites.sort()
    if args.mask:
        mask = args.mask.replace("%", "%%").replace("X", "%c")
        sites = [mask % tuple(site) for site in sites]
    with args.oustl as oustl:
        oustl.write("\n".join(sites) + "\n")

