#! /usr/bin/python

import argparse as ap
import math

cmpls = {
    'A': 'T', 'B': 'V', 'T': 'A', 'V': 'B', 'W': 'W',
    'C': 'G', 'D': 'H', 'G': 'C', 'H': 'D', 'S': 'S',
    'K': 'M', 'M': 'K', 'R': 'Y', 'Y': 'R', 'N': 'N'
}

def ds(site):
	compl = ""
	for nucl in site:
		compl = cmpls[nucl] + compl
	return min([site, compl])


if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        description="Make histrogram of representation mark"
	        )
	parser.add_argument(
	        "intab", metavar="IN.tsv", type=ap.FileType('r'),
	        help="input tabular file with representation mark values"
	        )
	parser.add_argument(
	        "ouhst", metavar="OU.hst", type=ap.FileType('w'),
	        help="output histogram file"
	        )
	parser.add_argument(
	        "--bins", dest="bins_number", type=int, default=41,
	        help="number of bins, default is 41"
	        )
	parser.add_argument(
	        "--cutoff", dest="cutoff", type=float, default=15,
	        help="expected count cutoff, default is 15"
	        )
	parser.add_argument(
	        "--expected", metavar="N", dest="exp", type=int, default=-3,
	        help="index of column with expected count, default is -3"
	        )
	parser.add_argument(
	        "--observed", metavar="N", dest="obs", type=int,
	        help="index of column with observed count, " +
	        "default is expected index - 1"
	        )
	args = parser.parse_args()
	bins = args.bins_number
	bins_total = bins + 1 # + > 2.0
	exp_index = args.exp
	obs_index = args.obs or args.exp - 1
	counts = dict()
	with args.intab as intab:
		intab.readline()
		for line in intab:
			vals = line.strip().split('\t')
			acv = vals[0]
			site = ds(vals[1])
			pair = (acv, site)
			expected = float(vals[exp_index])
			observed = float(vals[obs_index])
			if math.isnan(expected) or expected <= args.cutoff:
				expected = observed = 0
			expected_, observed_ = counts.get(pair, (0, 0))
			expected_ += expected
			observed_ += observed
			counts[pair] = (expected_, observed_)
	hist = [0] * bins_total
	span = 2.0 - 0.0
	labs = ["%.2f" % ((i+0.5) * span / bins) for i in range(bins_total)]
	for expected, observed in counts.values():
		if expected <= args.cutoff:
			continue
		ratio = observed / expected
		bin_index = min(int(ratio * bins / span), bins)
		hist[bin_index] += 1
	total = sum(hist)
	with args.ouhst as ouhst:
		for label, value in zip(labs, hist):
			ouhst.write("%s\t%.2f\n" % (label, value * 100.0 / total))

