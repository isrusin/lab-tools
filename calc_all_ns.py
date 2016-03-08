#! /usr/bin/python

import argparse as ap

from ContrastCalculation.counts import Counts
import ContrastCalculation.sites as st

if __name__ == "__main__":
	parser = ap.ArgumentParser(description="Calculate all contrasts")
	parser.add_argument(
	        "-i", dest="inacv", metavar="FILE.acv", type=ap.FileType('r'),
	        required=True, help="input file with ACv list (.acv)"
	        )
	parser.add_argument(
	        "-c", dest="cntpath", metavar="PATH", required=True,
	        help=".cnt files path with %%s placeholder that will be " +
	        "replaced with ACv from the input ACv list, only parent " +
	        "folder could be specified, '/%%s.cnt' tag will be added " +
	        "in the case"
	        )
	parser.add_argument(
	        "-s", dest="instl", metavar="FILE.stl", type=ap.FileType('r'),
	        required=True, help="input file with sites (.stl)"
	        )
	parser.add_argument(
	        "-o", dest="oupath", metavar="PATH", required=True,
	        help="output .ns files path with %%s placeholder or " +
	        "output folder ('/%%s.ns' tag will be added)"
	        )
	args = parser.parse_args()
	with args.inacv as inacv:
		acvs = inacv.read().strip().split('\n')
	cntpath = args.cntpath
	if "%s" not in cntpath:
		cntpath += "/%s.cnt"
	oupath = args.oupath
	if "%s" not in oupath:
		oupath += "/%s.ns"
	sites = []
	with args.instl as instl:
		for line in instl:
			site = line.strip()
			sites.append((st.MarkovSite(site), st.PevznerSite(site),
			              st.KarlinSite(site)))
	for acv in acvs:
		counts = Counts(open(cntpath % acv))
		with open(oupath % acv, 'w') as ouns:
			ouns.write("Site\tMo\tMe\tMr\tPo\tPe\tPr\tKo\tKe\tKr\tL\n")
			for msite, psite, ksite in sites:
				Fo = counts.get_count(msite.dsite)
				L = counts.get_total(msite.L)
				Me = msite.calc_expected(counts)
				Mr = Fo / Me if Me else float('NaN')
				M_str = "%d\t%.2f\t%.3f" % (Fo, Me, Mr)
				Pe = psite.calc_expected(counts)
				Pr = Fo / Pe if Pe else float('NaN')
				P_str = "%d\t%.2f\t%.3f" % (Fo, Pe, Pr)
				Ke = ksite.calc_expected(counts)
				Kr = Fo / Ke if Ke else float('NaN')
				K_str = "%d\t%.2f\t%.3f" % (Fo, Ke, Kr)
				vals = (msite.str_site, M_str, P_str, K_str, L)
				ouns.write("%s\t%s\t%s\t%s\t%d\n" % vals)

