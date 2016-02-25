#! /usr/bin/python

import argparse as ap
import sys

if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        description=""
	        )
	parser.add_argument(
	        "-a", dest="inacv", metavar="IN.acv", type=ap.FileType('r'),
	        required=True, help="input file with ACv list (.acv)"
	        )
	parser.add_argument(
	        "-s", dest="instl", metavar="IN.stl", type=ap.FileType('r'),
	        required=True, help="input file with list of sites (.stl)"
	        )
	parser.add_argument(
	        "-d", dest="nsdir", metavar="DIR", required=True,
	        help="folder with .ns files"
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
	nspath = args.nsdir + "/%s.ns"
	with args.outsv as outsv:
		outsv.write(
		        "ACv\tSite\tMo\tMe\tMr\tPo\tPe\tPr\tKo\tKe\tKr\tLength\n"
		        )
		for acv in acvs:
			with open(nspath % acv) as intab:
				intab.readline()
				for line in intab:
					site, etc = line.split('\t', 1)
					if site in sites:
						outsv.write(acv+'\t'+line.strip()+'\n')

