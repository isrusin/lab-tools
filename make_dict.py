#! /usr/bin/env python

"""Transform TSV with delimited column into dictionary file."""

import argparse
import signal
import sys

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Transform TSV with delimited column into .dct file."
    )
    parser.add_argument(
        "intsv", metavar="FILE", type=argparse.FileType("r"),
        help="input .tsv file"
    )
    parser.add_argument(
        "-t", "--title", dest="title", action="store_true",
        help="use if input file contains title line"
    )
    parser.add_argument(
        "-K", dest="key_index", metavar="N", type=int, required=True,
        help="index of the delimited 'key' column (from 0)"
    )
    parser.add_argument(
        "-d", dest="delimiter", metavar="CHAR", default=",",
        help="inner delimiter of the column, default comma"
    )
    parser.add_argument(
        "-s", "--skip", dest="skip", metavar="STRING",
        help="which 'key' column values to skip"
    )
    parser.add_argument(
        "-V", dest="value_index", metavar="N", type=int, default=0,
        help="index of 'value' column, default 0"
    )
    parser.add_argument(
        "-o", dest="oudct", metavar="DICT", type=argparse.FileType("w"),
        default=sys.stdout, help="output .dct file, default STDOUT"
    )
    args = parser.parse_args(argv)
    result = dict()
    with args.intsv as intsv:
        if args.title:
            intsv.readline()
        for line in intsv:
            vals = line.strip().split("\t")
            value = vals[args.value_index]
            keys = vals[args.key_index]
            if keys == args.skip:
                continue
            for key in keys.split(args.delimiter):
                if key in result:
                    sys.stderr.write("Repeated key %s with " % key)
                    if result[key] != value:
                        sys.stderr.write("varied values.\n")
                    else:
                        sys.stderr.write("identical values.\n")
                result[key] = value
    with args.oudct as oudct:
        if oudct.name == "<stdout>":
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        for item in sorted(result.items()):
            oudct.write("%s\t%s\n" % item)

if __name__ == "__main__":
    sys.exit(main())

