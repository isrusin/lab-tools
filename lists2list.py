#!/usr/bin/python
import argparse as ap
import sys

toremove = set()
def symmetric_difference_update(fset, sset):
	toremove.update(fset.intersection(sset))
	fset.symmetric_difference_update(sset)
	fset.difference_update(toremove)

def read_acvs(inlist):
	with inlist:
		return set(inlist.read().strip().split('\n'))

if __name__ == "__main__":
	parser = ap.ArgumentParser(description="Get ID-sets and return their " +
	                           "union (default), intersection or difference.")
	parser.add_argument("sets", metavar="FILE", type=ap.FileType('r'),
	                    nargs="+", help="input ID-set file, one ID per line")
	parser.add_argument("-a", "--action", dest="action", default='u',
	                    choices=['u', 'i', 'd', 's'], help="operation type: " +
	                    "Union (in either list); " +
	                    "Intersection (in every list); " +
	                    "Difference (only in the first list); " +
	                    "Symmetric difference (only in one of the lists).")
	parser.add_argument("-o", "--output", dest="oulist", metavar="FILE",
	                    type=ap.FileType('w'), default=sys.stdout,
	                    help="output file, default is stdout")
	args = parser.parse_args()
	action = {'u': set.update,
	          'i': set.intersection_update,
	          'd': set.difference_update,
	          's': symmetric_difference_update
	         }[args.action]
	current_set = read_acvs(args.sets.pop(0))
	for next_set in args.sets:
		action(current_set, read_acvs(next_set))
	with args.oulist as oulist:
		for line in sorted(current_set):
			oulist.write(line + '\n')

