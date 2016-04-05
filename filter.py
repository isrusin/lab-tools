#!/usr/bin/python
import argparse as ap
import sys

_FILTER_NONE = 0
_FILTER_DIRECT = 1
_FILTER_REVERSE = 2

def load_prs(prs_file):
	prs = set()
	with prs_file:
		for line in prs_file:
			prs.add(tuple(line.strip().split('\t')))
	return prs

def load_set(set_file):
	with set_file:
		return set(set_file.read().strip().split('\n'))

def load_sets(set_file, antiset_file, isprs=False):
	load_func = load_prs if isprs else load_set
	if set_file:
		loaded = load_func(set_file)
		if antiset_file:
			loaded.update_difference(load_func(antiset_file))
		return _FILTER_DIRECT, loaded
	elif antiset_file:
		return _FILTER_REVERSE, load_func(antiset_file)
	else:
		return _FILTER_NONE, None

def filter(value, value_set, filter_mode):
	if filter_mode == _FILTER_DIRECT:
		return value not in value_set
	elif filter_mode == _FILTER_REVERSE:
		return value in value_set
	else:
		return False


if __name__ == "__main__":
	parser = ap.ArgumentParser(
	        prog="filter", description="Filter .prs (default) or " +
	        ".tsv (-t option) file by set(s) of SIDs, sites or pairs."
	        )
	parser.add_argument("infile", metavar="FILE", type=ap.FileType('r'),
	                    help="input .prs (default) or .tsv file")
	parser.add_argument("-t", "--title", dest="title", action="store_true",
	                    help="treat input file as .tsv (with title line)")
	parser.add_argument(
	        "-a", dest="sids", type=ap.FileType('r'), metavar="SET",
	        help="filter by the SET of sids."
	        )
	parser.add_argument(
	        "-A", dest="nosids", type=ap.FileType('r'), metavar="SET",
	        help="filter by the reversed SET of sids."
	        )
	parser.add_argument(
	        "-s", dest="sites", type=ap.FileType('r'), metavar="SET",
	        help="filter by the SET of sites."
	        )
	parser.add_argument(
	        "-S", dest="nosites", type=ap.FileType('r'), metavar="SET",
	        help="filter by the reversed SET of sites."
	        )
	parser.add_argument(
	        "-p", dest="pairs", type=ap.FileType('r'), metavar="SET",
	        help="filter by the SET of pairs."
	        )
	parser.add_argument(
	        "-P", dest="nopairs", type=ap.FileType('r'), metavar="SET",
	        help="filter by the reversed SET of pairs."
	        )
	parser.add_argument("-o", "--out", dest="oufile", metavar="FILE",
	                    type=ap.FileType('w'), default=sys.stdout,
	                    help="output file, default is stdout")
	args = parser.parse_args()
	sids_mode, sids = load_sets(args.sids, args.nosids)
	sites_mode, sites = load_sets(args.sites, args.nosites)
	pairs_mode, pairs = load_sets(args.pairs, args.nopairs, isprs=True)
	with args.oufile as oufile, args.infile as infile:
		if args.title:
			oufile.write(infile.readline())
		for line in infile:
			sid, site = pair = tuple(line.strip().split('\t', 2)[:2])
			if filter(sid, sids, sids_mode):
				continue
			if filter(site, sites, sites_mode):
				continue
			if filter(pair, pairs, pairs_mode):
				continue
			oufile.write(line)

