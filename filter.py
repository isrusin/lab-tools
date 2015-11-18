#!/usr/bin/python
import argparse as ap
import sys

def load_prs(prs_file):
	prs = set()
	with prs_file:
		for line in prs_file:
			prs.add(tuple(line.strip().split('\t')))
	return prs

def load_set(set_file, isprs=False):
	if isprs:
		return load_prs(set_file)
	with set_file:
		return set(set_file.read().strip().split('\n'))

def load_sets(file_list, isprs=False):
	tags = set()
	filter_tags = False
	if file_list:
		tags = load_set(file_list.pop(0), isprs)
		for set_file in file_list:
			tags.intersection_update(load_set(set_file, isprs))
		filter_tags = True
	return tags, filter_tags

if __name__ == "__main__":
	parser = ap.ArgumentParser(prog="filter", usage="%(prog)s [-h] FILE " +
	                           "[-t] [-a SET] [-s SET] [-p SET] [-o FILE]",
	                           description="Filter .prs (default) or .tsv " +
	                           "(-t option) file by set(s) of SIDs, sites " +
	                           "or pairs.")
	parser.add_argument("infile", metavar="FILE", type=ap.FileType('r'),
	                    help="input .prs (default) or .tsv file")
	parser.add_argument("-t", "--title", dest="title", action="store_true",
	                    help="treat input file as .tsv (with title)")
	parser.add_argument("-a", dest="sids", type=ap.FileType('r'), nargs="*",
	                    metavar="SET", help="filter by the SET of sids.")
	parser.add_argument("-s", dest="sites", type=ap.FileType('r'), nargs="*",
	                    metavar="SET", help="filter by the SET of sites.")
	parser.add_argument("-p", dest="pairs", type=ap.FileType('r'), nargs="*",
	                    metavar="SET", help="filter by the SET of pairs.")
	parser.add_argument("-o", "--output", dest="oufile", metavar="FILE",
	                    type=ap.FileType('w'), default=sys.stdout,
	                    help="output file, default is stdout")
	args = parser.parse_args()
	sids, filter_sids = load_sets(args.sids)
	sites, filter_sites = load_sets(args.sites)
	pairs, filter_pairs = load_sets(args.pairs, True)
	with args.oufile as oufile:
		with args.infile as infile:
			if args.title:
				oufile.write(infile.readline())
			for line in infile:
				sid, site = pair = tuple(line.strip().split('\t', 2)[:2])
				if filter_sids and sid not in sids:
					continue
				if filter_sites and site not in sites:
					continue
				if filter_pairs and pair not in pairs:
					continue
				oufile.write(line)

