#! /usr/bin/env python2.7

"""Convert HMMER domtbl file into TSV table."""

import argparse
import signal
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert HMMER domtblout into TSV."
    )
    parser.add_argument(
        "infile", metavar="DOMTBL", type=argparse.FileType("r"),
        help="HMMER domtbl output"
    )
    parser.add_argument(
        "-o", "--out", dest="outsv", metavar="TSV",
        type=argparse.FileType("w"), default=sys.stdout,
        help="output file, default STDOUT"
    )
    args = parser.parse_args(argv)
    with args.infile as indom, args.outsv as outsv:
        outsv.write("\t".join((
            "target name", "target accession", "tlen",
            "query name", "query accession", "qlen",
            "E-value", "score", "bias", "#", "ndom",
            "c-Evalue", "i-Evalue", "score", "bias",
            "from (hmm)", "to (hmm)", "from (align)", "to (align)",
            "from (env)", "to (env)", "acc", "description"
        )) + "\n")
        for line in indom:
            if line.startswith("#"):
                continue
            outsv.write("\t".join(line.split(None, 22)))


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        pass # no signal.SIGPIPE on Windows
    sys.exit(main())

