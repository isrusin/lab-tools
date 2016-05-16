#! /usr/bin/python

import argparse as ap
import sys

if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        description="Join files with contrasts into single .tsv file."
	        )
	parser.add_argument(
	        "-a", dest="inacv", metavar="IN.acv", type=ap.FileType('r'),
	        required=True, help="input file with ACv (any ID) list (.acv)"
	        )
	parser.add_argument(
	        "-s", dest="instl", metavar="IN.stl", type=ap.FileType('r'),
	        required=True, help="input file with list of sites (.stl)"
	        )
	parser.add_argument(
	        "-d", dest="nspath", metavar="PATH", required=True,
	        help="path to .ns files, use %s placeholder for ACv (ID)."
	        )
	parser.add_argument(
	        "-o", dest="outsv", metavar="OUT.tsv", type=ap.FileType('w'),
	        default=sys.stdout, help="output .tsv file"
	        )
	args = parser.parse_args()
	with args.inacv as inacv:
		acvs = set(inacv.read().strip().split('\n'))
	with args.instl as instl:
		sites = set(instl.read().strip().split('\n'))
	acvs = sorted(acvs)
	nspath = args.nspath
	if "%" not in nspath:
		nspath += "/%s.ns"
	with args.outsv as outsv:
		is_first = True
		for acv in acvs:
			with open(nspath % acv) as intab:
				title = intab.readline()
				if is_first:
					is_first = False
					outsv.write("ID\t" + title)
				for line in intab:
					site, etc = line.split('\t', 1)
					if site in sites:
						outsv.write(acv+'\t'+line.strip()+'\n')

