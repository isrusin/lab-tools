#! /usr/bin/python

import argparse as ap
import sys

if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        description="Sum counts from several inputs"
	        )
	parser.add_argument(
	        "incnt", metavar="IN.cnt", nargs="+", type=ap.FileType('r'),
	        help="input file with counts"
	        )
	parser.add_argument(
	        "-o", dest="oucnt", metavar="OU.cnt", type=ap.FileType('w'),
	        default=sys.stdout, help="output file with sum of counts"
	        )
	args = parser.parse_args()
	sites = []
	counts = []
	with args.incnt[0] as incnt:
		length = int(incnt.readline())
		for line in incnt:
			site, count = line.split('\t')
			sites.append(site)
			counts.append(int(count))
	for incnt in args.incnt[1:]:
		with incnt:
			if int(incnt.readline()) != length:
				print "%s for wrong site length, skipped" % incnt.name
				continue
			for index, line in enumerate(incnt):
				counts[index] += int(line.split('\t')[-1])
	with args.oucnt as oucnt:
		oucnt.write("%d\n" % length)
		for site, count in zip(sites, counts):
			oucnt.write("%s\t%d\n" % (site, count))

