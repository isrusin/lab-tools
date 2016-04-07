#! /usr/bin/python

import argparse as ap
import sys

import ContrastCalculation.counts as cnt
import ContrastCalculation.sites as st


def load_sites(instl, len_cutoff=8):
	sites = set()
	len_max = 0
	with instl:
		for line in instl:
			site = line.strip("\n\t\r Nn-.")
			length = len(site)
			if length > len_cutoff:
				sys.stderr.write("%s is too long, skipped.\n" % site)
				continue
			len_max = max(len_max, length)
			sites.add(site)
	return sorted(sites), len_max

if __name__ == "__main__":
	parser = ap.ArgumentParser(description="Contrast calculation")
	parser.add_argument(
	        "-f", "--fasta", dest="inseq", metavar="file", required=True,
	        help="Input fasta file, may be gzipped."
	        )
	parser.add_argument(
	        "-s", "--sites", dest="instl", metavar="file",
	        type=ap.FileType('r'), default=sys.stdin,
	        help="Input list of sites, one-per-line."
	        )
	parser.add_argument(
	        "-m", "--method", dest="method", default="karlin",
	        choices=["mmax", "pevzner", "karlin"],
	        help="Method of expected frequency calculation, " +
	        "Karlin's method is default."
	        )
	parser.add_argument(
	        "-o", "--out", dest="outsv", metavar="file",
	        type=ap.FileType('w'), default=sys.stdout,
	        help="Output tabular (.tsv) file, default is stdout"
	        )
	args = parser.parse_args()
	sites, len_max = load_sites(args.instl)
	counts = cnt.calculate_counts(args.inseq, len_max)
	wrapper = {"mmax": st.MarkovSite, "pevzner": st.PevznerSite,
	           "karlin": st.KarlinSite}[args.method]
	with args.outsv as outsv:
		outsv.write(
		        "Site\tObserved number\tExpected number (%s)\t" +
		        "Contrast ratio\tSequence length\n"
		        )
		ouline = "{Site}\t{No:d}\t{Ne:.2f}\t{Ratio:.3f}\t{Length:.0f}\n"
		for site in sites:
			wrapped = wrapper(site)
			vals = dict()
			vals["Site"] = wrapped.str_site
			vals["Length"] = counts.get_total(wrapped.L)
			vals["No"] = counts.get_count(wrapped.dsite)
			vals["Ne"] = wrapped.calc_expected(counts)
			vals["Ratio"] = vals["No"] / (vals["Ne"] or float("NaN"))
			outsv.write(ouline.format(**vals))

