#! /usr/bin/python

import argparse as ap

from ContrastCalculation.counts import Counts
from ContrastCalculation import contrasts

if __name__ == "__main__":
	parser = ap.ArgumentParser(description="Calculate Markov's ratios")
	parser.add_argument(
	        "-i", dest="incnt", metavar="FILE.cnt", type=ap.FileType('r'),
	        required=True, help="input file with counts (.cnt)"
	        )
	parser.add_argument(
	        "-s", dest="instl", metavar="FILE.stl", type=ap.FileType('r'),
	        required=True, help="input file with sites (.stl)"
	        )
	parser.add_argument(
	        "-o", dest="oucst", metavar="FILE.cst", type=ap.FileType('w'),
	        required=True, help="output file with calculated values (.cst)"
	        )
	args = parser.parse_args()
	counts = Counts(args.incnt)
	with args.instl as instl, args.oucst as oucst:
		oucst.write("Site\tMo\tMe\tMr\tL\n")
		for line in instl:
			site = line.strip()
			Mo, Me, Mr, L = contrasts.get_values(
			        site, counts, contrasts.calc_expected_M, False
			        )
			oucst.write("%s\t%d\t%.2f\t%.2f\t%d\n" % (site, Mo, Me, Mr, L))

