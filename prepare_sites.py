#! /usr/bin/python

import argparse as ap

import ContrastCalculation.sites as st

if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        description="Prepare site list for contrast calculation"
	        )
	parser.add_argument(
	        "-i", dest="instl", metavar="FILE.stl", type=ap.FileType('r'),
	        required=True, help="input site list (.stl)"
	        )
	parser.add_argument(
	        "-m", dest="method", metavar="{K,M,P}", required=True,
	        choices=['K', 'M', 'P'], help="method of contrasts calculation"
	        )
	parser.add_argument(
	        "-o", dest="ounsl", metavar="FILE.*sl", type=ap.FileType('wb'),
	        required=True, help="output list of prepared sites"
	        )
	args = parser.parse_args()
	SiteClass = st.KarlinSite
	if args.method == 'M':
		SiteClass = st.MarkovSite
	elif args.method == 'P':
		SiteClass = st.PevznerSite
	with args.instl as instl:
		sites = instl.read().strip().split('\n')
	prepared = [SiteClass(site) for site in sites]
	st.dump_sl(prepared, args.ounsl)

