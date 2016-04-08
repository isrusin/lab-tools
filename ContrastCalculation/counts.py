"""A wrapper and handlers for word counts.

Contains a wrapper for word counts calculated with count_words, which is
either stand-alone util C dynamic library function accessed through ctypes.
"""

import os
import ctypes

__all__ = ["Counts", "load_counts", "calculate_counts"]

class Counts():
	
	"""Wrapper for word counts."""
	
	def __init__(self, length, counts, totals):
		"""Counts(length, counts, totals)
		
		Counts wrapper constructor. Do not use it directly!
		Note: Use calculate_counts to calculate counts and load_count to
		load them from count_words output file.
		"""
		self.length = length
		self.counts = counts
		self.totals = totals
	
	def get_count(self, sites):
		"""Get count for given list of sites.
		
		Return sum of counts for given sites. Sites should be degitized
		(see sites module for details).
		"""
		count = 0
		for site in sites:
			count += self.counts[site]
		return count
	
	def get_freq(self, sites, length):
		"""Get frequency for given list of sites.
		
		Normalize count for the sites by total number of sites of specified
		length.
		Sites should be degitized (see sites module for details).
		"""
		freq = self.get_count(sites) / self.totals[length]
		return freq
	
	def get_total(self, length):
		"""Get total number of sites of specified length."""
		return self.totals[length]

def load_counts(incnt):
	"""load_counts(file)
	
	Load counts from file obtained with count_words.
	  file -- file-like object, should support with statment.
	Returns Counts object.
	"""
	with incnt:
		length = int(incnt.readline())
		num = 1 << (length * 2 + 1)
		CountsArr = ctypes.c_int32 * num
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
	"""calculate_counts(filename, length)
	
	Calculate counts for all words of the length and all shorter ones.
	  filename -- path to fasta file, may be gzipped.
	  length -- maximum length of the words to calculate counts for.
	Returns Counts object.
	
	Note: requires count_words/count_words.so library.
	"""
	module_path = os.path.dirname(__file__) or "."
	cw_lib = ctypes.CDLL(module_path + "/count_words/count_words.so")
	count_words = cw_lib.count_words
	num = 1 << (length * 2 + 1)
	count_words.restype = ctypes.POINTER(ctypes.c_int32 * num)
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

