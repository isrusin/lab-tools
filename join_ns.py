#! /usr/bin/python

"""Join files with compositional biases.

Join a set of files with compositional biases without "Sequence ID" column
into a single TSV table with the column.

More generally, you could use the tool to join text files into a single
TSV by a list of IDs that will be placed into the first column, with
additional option to filter inputs by their first column (-s option).
"""

import argparse as ap
import sys

if __name__ == "__main__":
    parser = ap.ArgumentParser(
        description="Join files with contrasts into single .tsv file."
    )
    parser.add_argument(
        "nspath", metavar="PATH",
        help="path to .ns files, use {} placeholder for ACv (ID)."
    )
    parser.add_argument(
        "-a", dest="inacv", metavar="IN.acv", type=ap.FileType("r"),
        default=sys.stdin, help="""input file with a list of ACvs (any ID)
        (.acv); default is STDIN"""
    )
    parser.add_argument(
        "-s", dest="instl", metavar="IN.stl", type=ap.FileType("r"),
        help="""input file with a list of sites (.stl); default is not
        to filter by sites"""
    )
    parser.add_argument(
        "-o", dest="outsv", metavar="OUT.tsv", type=ap.FileType("w"),
        default=sys.stdout, help="output .tsv file, default stdout"
    )
    args = parser.parse_args()
    with args.inacv as inacv:
        acvs = set(inacv.read().strip().split())
    all_sites = args.instl is None
    if not all_sites:
        with args.instl as instl:
            sites = set(instl.read().strip().split())
    acvs = sorted(acvs)
    nspath = args.nspath
    if "{}" not in nspath:
        nspath += "/{}.ns"
    with args.outsv as outsv:
        is_first = True
        for acv in acvs:
            with open(nspath.format(acv)) as intab:
                title = intab.readline()
                if is_first:
                    is_first = False
                    outsv.write("ID\t" + title)
                for line in intab:
                    site, etc = line.split("\t", 1)
                    if all_sites or site in sites:
                        outsv.write(acv + "\t" + line.strip() + "\n")

