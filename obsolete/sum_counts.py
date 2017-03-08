#! /usr/bin/env python

"""Sum counts from several files.

Only contiguous, only CNT files with single block of counts.
Uses obsolete format of CNT files, which are out-of-use by themselves.
"""

import argparse
import signal
import sys

def main(argv):
    parser = argparse.ArgumentParser(
        description="Sum counts from several inputs."
    )
    parser.add_argument(
        "incnt", metavar="IN.cnt", nargs="+", type=argparse.FileType("r"),
        help="input file with counts"
    )
    parser.add_argument(
        "-o", dest="oucnt", metavar="OUT.cnt",
        type=argparse.FileType("w"), default=sys.stdout,
        help="output file with sum of counts, default STDOUT"
    )
    args = parser.parse_args(argv)
    sites = []
    counts = []
    with args.incnt[0] as incnt:
        length = int(incnt.readline())
        for line in incnt:
            site, count = line.split("\t")
            sites.append(site)
            counts.append(int(count))
    for incnt in args.incnt[1:]:
        with incnt:
            if int(incnt.readline()) != length:
                print "Wrong site length in %s, skipped!" % incnt.name
                continue
            for index, line in enumerate(incnt):
                counts[index] += int(line.split("\t")[-1])
    with args.oucnt as oucnt:
        oucnt.name == "<stdout>":
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        oucnt.write("%d\n" % length)
        for site, count in zip(sites, counts):
            oucnt.write("%s\t%d\n" % (site, count))

if __name__ == "__main__":
    sys.exit(main())

