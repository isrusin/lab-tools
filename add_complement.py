#! /usr/bin/python

import argparse as ap
import sys

compls = {
        "A": "T", "T": "A", "C": "G", "G": "C",
        "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
        "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
        }

def to_ds(site):
    c_site = ""
    for nucl in site[::-1]:
        c_site += compls.get(nucl, "?")
    return min(site, c_site), max(site, c_site)

if __name__ == "__main__":
    parser = ap.ArgumentParser(
            description="Add or remove complement sites."
            )
    parser.add_argument(
            "-i", dest="instl", metavar="IN_LIST", type=ap.FileType("r"),
            default=sys.stdin, help="input site list, default stdin"
            )
    parser.add_argument(
            "-o", dest="oustl", metavar="OU_LIST", type=ap.FileType("w"),
            default=sys.stdout, help="output site list, default stdout"
            )
    parser.add_argument(
            "-r", dest="reverse", action="store_true",
            help="return only the lowest site for each complementary pair"
            )
    args = parser.parse_args()
    sites = set()
    with args.instl as instl:
        for line in instl:
            site, c_site = to_ds(line.strip())
            sites.add(site)
            if not args.reverse:
                sites.add(c_site)
    with args.oustl as oustl:
        oustl.write("\n".join(sorted(sites)) + "\n")

