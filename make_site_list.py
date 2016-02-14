#! /usr/bin/python

import argparse as ap
import sys

nucls = ['A', 'C', 'G', 'T']

def elongate_sites(sites):
	new_sites = []
	for site in sites:
		for nucl in nucls:
			new_sites.append(site+nucl)
	return new_sites

if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        description="Generate list of all sites of the given length."
	        )
	parser.add_argument("length", metavar="N", type=int,
	                    choices=range(1, 9), help="length of sites"
	                    )
	parser.add_argument(
	        "-o", dest="oustl", type=ap.FileType('w'), default=sys.stdout,
	        metavar="FILE", help="output file (.stl extension is prefered)"
	        )
	parser.add_argument(
	        "-n", "-N", dest="with_n", action="store_true",
	        help="use 5-letter alphabet [A, C, G, T, N]"
	        )
	args = parser.parse_args()
	if args.with_n:
		nucls.append("N")
	sites = [""]
	for i in range(args.length):
		sites = elongate_sites(sites)
	if args.with_n:
		sites = sorted(set([site.strip('N') for site in sites]))
		sites.remove("")
	else:
		sites.sort()
	with args.oustl as oustl:
		oustl.write('\n'.join(sites) + '\n')

