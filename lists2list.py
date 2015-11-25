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
	group = parser.add_mutually_exclusive_group(required=False)
	group.add_argument("-u", dest="action", action="store_const", const='u',
	                   help="union (in either list)")
	group.add_argument("-i", dest="action", action="store_const", const='i',
	                   help="intersection (in every list)")
	group.add_argument("-d", dest="action", action="store_const", const='d',
	                   help="difference (only in the first list)")
	group.add_argument("-s", dest="action", action="store_const", const='s',
	                   help="symmetric difference (only in one list)")
	parser.add_argument("-o", "--output", dest="oulist", metavar="FILE",
	                    type=ap.FileType('w'), default=sys.stdout,
	                    help="output file, default is stdout")
	args = parser.parse_args()
	action = {'u': set.update,
	          'i': set.intersection_update,
	          'd': set.difference_update,
	          's': symmetric_difference_update
	         }.get(args.action, set.update)
	current_set = read_acvs(args.sets.pop(0))
	for next_set in args.sets:
		action(current_set, read_acvs(next_set))
	with args.oulist as oulist:
		for line in sorted(current_set):
			try:
				oulist.write(line + '\n')
			except IOError:
				break

