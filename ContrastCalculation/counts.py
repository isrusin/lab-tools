import os
import ctypes as ct

class Counts():
	def __init__(self, length, counts, totals):
		self.length = length
		self.counts = counts
		self.totals = totals
	
	def get_count(self, sites):
		count = 0
		for site in sites:
			count += self.counts[site]
		return count
	
	def get_freq(self, sites, length):
		freq = self.get_count(sites) / self.totals[length]
		return freq
	
	def get_total(self, length):
		return self.totals[length]

def load_counts(incnt):
	with incnt:
		length = int(incnt.readline())
		num = 1 << (length * 2 + 1)
		CountsArr = ct.c_int32 * num
		counts = CountsArr()
		totals = [0]
		site = 4
		while site < num:
			maxsite = site << 1
			total = 0
			while site < maxsite:
				line = incnt.readline()
				count = int(line.rsplit('\t', 1)[-1])
				counts[site] = count
				total += count
				site += 1
			totals.append(float(total))
			site <<= 1
	counts[1] = int(totals[1])
	return Counts(length, counts, totals)

def calculate_counts(fasta_path, length):
	module_path = os.path.dirname(__file__) or "."
	cw_lib = ct.CDLL(module_path + "/count_words/count_words.so")
	count_words = cw_lib.count_words
	num = 1 << (length * 2 + 1)
	count_words.restype = ct.POINTER(ct.c_int32 * num)
	counts = count_words(fasta_path, length).contents
	totals = [0]
	site = 4
	while site < num:
		maxsite = site << 1
		total = 0
		while site < maxsite:
			total += counts[site]
			site += 1
		totals.append(float(total))
		site <<= 1
	counts[1] = int(totals[1])
	return Counts(length, counts, totals)

