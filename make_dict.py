#! /usr/bin/python

import argparse as ap
import signal as sg
import sys

if __name__ == "__main__":
    sg.signal(sg.SIGPIPE, sg.SIG_DFL)
    parser = ap.ArgumentParser(
            description="Transform .tsv file with delimited column " +
            "into .dict file."
            )
    parser.add_argument(
            "intsv", metavar="IN.tsv", type=ap.FileType("r"),
            help="input .tsv file"
            )
    parser.add_argument(
            "-t", dest="title", action="store_true",
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
            "-s", dest="skip", metavar="STRING",
            help="which 'key' column values to skip"
            )
    parser.add_argument(
            "-V", dest="value_index", metavar="N", type=int, default=0,
            help="index of 'value' column, default 0"
            )
    parser.add_argument(
            "-o", dest="oudct", metavar="OUT.dict", type=ap.FileType("w"),
            default=sys.stdout, help="output .dict file, default stdout"
            )
    args = parser.parse_args()
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
                    sys.stderr.write("Repeated key %s with ")
                    if result[key] != value:
                        sys.stderr.write("varied values.\n")
                    else:
                        sys.stderr.write("identical values.\n")
                result[key] = value
    with args.oudct as oudct:
        for item in sorted(result.items()):
            oudct.write("%s\t%s\n" % item)

