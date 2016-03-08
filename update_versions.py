#! /usr/bin/python

import argparse as ap
import sys

if __name__ == "__main__":
	parser = ap.ArgumentParser(description="Add/update version of ACvs.")
	parser.add_argument(
	        "infile", metavar="IN_FILE", type=ap.FileType('r'),
	        help="input file containing AC(v)s"
	        )
	parser.add_argument(
	        "-t", "--with-title", dest="title", action="store_true",
	        help="input file has title"
	        )
	parser.add_argument(
	        "-c", dest="column", metavar="N", type=int, default=0,
	        help="index of AC(v) column in the input file"
	        )
	parser.add_argument(
	        "-s", dest="source", metavar="LIST.acv", type=ap.FileType('r'),
	        required=True, help="list of ACvs to get versions from"
	        )
	ougroup = parser.add_mutually_exclusive_group()
	ougroup.add_argument(
	        "-i", "--in-place", dest="inplace", action="store_true",
	        help="Add/update AC versions in-place"
	        )
	ougroup.add_argument(
	        "-o", dest="oufile", metavar="OU_FILE", type=ap.FileType('w'),
	        default=sys.stdout, help="output file"
	        )
	args = parser.parse_args()
	keep = False
	ac2acv = dict()
	with args.source as source:
		for line in source:
			acv = line.strip()
			ac = acv.split('.')[0]
			ac2acv[ac] = acv
	lines = []
	with args.infile as infile:
		if args.title:
			lines.append(infile.readline().strip())
		for line in infile:
			vals = line.strip().split('\t')
			ac = vals[args.column].split('.')[0]
			if ac in ac2acv:
				vals[args.column] = ac2acv[ac]
				lines.append('\t'.join(vals))
			elif keep:
				lines.append('\t'.join(vals))
	oufile = open(infile.name, 'w') if args.inplace else args.oufile
	with oufile:
		oufile.write('\n'.join(lines) + '\n')

