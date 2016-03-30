#! /usr/bin/python

import argparse as ap

import ContrastCalculation.counts as cnt
import ContrastCalculation.sites as st

if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        description="Calculate contrasts for prepared sites"
	        )
	parser.add_argument(
	        "-i", dest="incnt", metavar="FILE.cnt", type=ap.FileType('r'),
	        required=True, help="input file with counts (.cnt)"
	        )
	parser.add_argument(
	        "-s", dest="innsl", metavar="FILE.*sl", type=ap.FileType('rb'),
	        required=True, help="input file with prepared sites (.*sl)"
	        )
	parser.add_argument(
	        "-o", dest="oucst", metavar="FILE.cst", type=ap.FileType('w'),
	        required=True, help="output file with calculated values (.cst)"
	        )
	parser.add_argument(
	        "-t", dest="tag", metavar="TAG", default="",
	        help="title tag of the output file"
	        )
	args = parser.parse_args()
	counts = cnt.load_counts(args.incnt)
	sites = st.load_sl(args.innsl)
	with args.oucst as oucst:
		oucst.write("Site\t{0}o\t{0}e\t{0}r\tL\n".format(args.tag))
		for site in sites:
			expected = site.calc_expected(counts)
			observed = counts.get_count(site.dsite)
			ratio = observed / expected
			total = counts.get_total(site.L)
			vals = (site.str_site, observed, expected, ratio, total)
			oucst.write("%s\t%d\t%.2f\t%.3f\t%d\n" % vals)

