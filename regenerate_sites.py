#! /usr/bin/env python

"""Make list of non-degenerate variants of given degenerate sites."""

import argparse
import signal
import sys

NUCLS = {
    "N": ["A", "C", "G", "T"],
    "A": ["A"], "B": ["C", "G", "T"],
    "C": ["C"], "D": ["A", "G", "T"],
    "G": ["G"], "H": ["A", "C", "T"],
    "T": ["T"], "V": ["A", "C", "G"],
    "M": ["A", "C"], "K": ["G", "T"],
    "R": ["A", "G"], "Y": ["C", "T"],
    "W": ["A", "T"], "S": ["C", "G"]
}

def regenerate(dsite):
    """Get non-degenerate version of the site."""
    regenerated = [""]
    for dnucl in dsite:
        elongated = []
        for nucl in NUCLS[dnucl]:
            for primer in regenerated:
                elongated.append(primer + nucl)
        regenerated = elongated
    return regenerated

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Make list of non-degenerate variants of given sites."
    )
    parser.add_argument(
        "instl", metavar="FILE", type=argparse.FileType("r"),
        default=sys.stdin, help="input .stl file, use '-' for STDIN"
    )
    parser.add_argument(
        "-o", metavar="FILE", dest="oustl", type=argparse.FileType("w"),
        default=sys.stdout, help="output .stl file, default STDOUT"
    )
    parser.add_argument(
        "-k", "--keep", dest="keep", action="store_true",
        help="keep degenerate sites in the list, default replacement"
    )
    args = parser.parse_args(argv)
    with args.instl as instl:
        dsites = set(instl.read().strip().split())
    sites = set()
    for dsite in dsites:
        sites.update(regenerate(dsite))
    if args.keep:
        sites.update(dsites)
    with args.oustl as oustl:
        if oustl.name == "<stdout>":
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        oustl.write("\n".join(sorted(sites)) + "\n")

if __name__ == "__main__":
    sys.exit(main())

