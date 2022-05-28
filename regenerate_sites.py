#! /usr/bin/env python2

"""Replace degenerate sites with non-degenerate variants."""

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
        description="""Replace degenerate sites in the TSV with
        non-degenerate variants."""
    )
    parser.add_argument(
        "intsv", metavar="FILE", type=argparse.FileType("r"),
        default=sys.stdin, help="""input TSV file with degenerate sites,
        use '-' for STDIN"""
    )
    parser.add_argument(
        "-c", "--index", type=int, default=0,
        help="site column index, default 0"
    )
    parser.add_argument(
        "-t", "--has-title", action="store_true",
        help="treat the first line as title"
    )
    parser.add_argument(
        "-k", "--keep", action="store_true",
        help="keep degenerate sites in the file, default is replacement"
    )
    parser.add_argument(
        "-o", metavar="FILE", dest="outsv", type=argparse.FileType("w"),
        default=sys.stdout, help="output TSV file, default STDOUT"
    )
    args = parser.parse_args(argv)
    index = args.index
    dsites = set()
    with args.intsv as intsv, args.outsv as outsv:
        if args.has_title:
            outsv.write(intsv.readline())
        for line in intsv:
            vals = line.strip().split("\t")
            dsite = vals[index]
            if args.keep:
                outsv.write("\t".join(vals) + "\n")
            for site in regenerate(dsite):
                if site == dsite and args.keep:
                    continue
                vals[index] = site
                outsv.write("\t".join(vals) + "\n")


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

