#! /usr/bin/python

import sys
import argparse as ap

nucls = {'N':['A','C','G','T'],
        'A':['A'], 'B':['C','G','T'],
        'C':['C'], 'D':['A','G','T'],
        'G':['G'], 'H':['A','C','T'],
        'T':['T'], 'V':['A','C','G'],
        'M':['A','C'], 'K':['G','T'],
        'R':['A','G'], 'Y':['C','T'],
        'W':['A','T'], 'S':['C','G']}

def regenerate(dsite):
	regenerated = [""]
	for dnucl in dsite:
		elongated = []
		for nucl in nucls[dnucl]:
			for primer in regenerated:
				elongated.append(primer + nucl)
		regenerated = elongated
	return regenerated

if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        prog="regenerate_sites", description="Make list of " +
	        "non-degenerate variants of degenerate sites."
	        )
	parser.add_argument(
	        "-i", metavar="FILE", dest="instl", type=ap.FileType('r'),
	        default=sys.stdin, help="input .stl file (default is stdin)"
	        )
	parser.add_argument(
	        "-o", metavar="FILE", dest="oustl", type=ap.FileType('w'),
	        default=sys.stdout, help="output .stl file (default is stdout)"
	        )
	parser.add_argument(
	        "-a", "-k", dest="keep", action="store_true",
	        help="add non-degenerate variant to initial site list " +
	        "and keep degenerate sites (default is replacement)"
	        )
	args = parser.parse_args()
	with args.instl as instl:
		dsites = set(instl.read().strip().split('\n'))
	sites = set()
	for dsite in dsites:
		sites.update(regenerate(dsite))
	if args.keep:
		sites.update(dsites)
	with args.oustl as oustl:
		try:
			oustl.write('\n'.join(sorted(sites))+'\n')
		except IOError:
			sys.stderr.write("Partial output!\n")

