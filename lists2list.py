#! /usr/bin/env python

import argparse
import signal
import sys


class SymmetricDifference(object):
    def __init__(self):
        self.toremove = set()

    def __call__(self, fset, sset):
        self.toremove.update(fset.intersection(sset))
        fset.symmetric_difference_update(sset)
        fset.difference_update(self.toremove)


def read_acvs(inlist, verbose, return_header=False):
    idset = set()
    header = None
    with inlist:
        for line in inlist:
            if line.startswith("#"):
                if return_header and header is None and line.startswith("#:"):
                    header = line[2:].strip("\n")
                continue
            idset.add(line.strip("\n"))
    idset.discard("")
    if verbose:
        sys.stderr.write("%s: %d\n" % (inlist.name, len(idset)))
    if return_header:
        return idset, header
    return idset


def _verbose_sigpipe_handler(signum, frame):
    sys.stderr.write("The output set is incomplete!\n")
    sys.exit(1)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="""Get ID-sets and return their union (default),
        intersection or difference."""
    )
    parser.add_argument(
        "sets", metavar="FILE", type=argparse.FileType("r"), nargs="+",
        help="input ID-set file, one ID per line"
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-u", "--union", dest="action", action="store_const",
        const=set.update, help="union (in either list)"
    )
    group.add_argument(
        "-i", "--intersection", dest="action", action="store_const",
        const=set.intersection_update,
        help="intersection (in every list)"
    )
    group.add_argument(
        "-d", "--difference", dest="action", action="store_const",
        const=set.difference_update,
        help="difference (only in the first list)"
    )
    group.add_argument(
        "-s", "--symmetric", dest="action", action="store_const",
        const=SymmetricDifference(),
        help="symmetric difference (only in one list)"
    )
    parser.add_argument(
        "-o", "--output", dest="oulist", metavar="FILE",
        type=argparse.FileType("w"), default=sys.stdout,
        help="output file, default STDOUT"
    )
    parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true",
        help="verbose mode, print every set size to STDERR"
    )
    args = parser.parse_args(argv)
    action = args.action or set.update
    verbose = args.verbose
    stderr = sys.stderr
    if verbose:
        signal.signal(signal.SIGPIPE, _verbose_sigpipe_handler)
    current_set, header = read_acvs(args.sets.pop(0), verbose, True)
    for next_set in args.sets:
        action(current_set, read_acvs(next_set, verbose))
    with args.oulist as oulist:
        if verbose:
            stderr.write("%s: %d\n" % (oulist.name, len(current_set)))
        if header is not None:
            oulist.write("#:%s\n" % header)
        oulist.write("\n".join(sorted(current_set) + [""]))


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

