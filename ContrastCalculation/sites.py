"""Site wrappers implementing contrast calculation methods.

Contains site wrappers, function for site digitizing, and dumper-loader
functions for wrapped site collections.
"""

import cPickle

__all__ = ["digitize", "digitize_withl", "dump_sl", "load_sl", "Site",
           "MarkovSite", "PevznerSite", "KarlinSite"]

nucls = {'A': 0, 'C': 1, 'G': 2, 'T': 3}

dnucls = {
        'N': [0, 1, 2, 3],
        'A': [0], 'B': [1, 2, 3],
        'C': [1], 'D': [0, 2, 3],
        'G': [2], 'H': [0, 1, 2],
        'T': [3], 'V': [0, 1, 2],
        'M': [0, 1], 'K': [2, 3],
        'R': [0, 2], 'Y': [1, 3],
        'W': [0, 3], 'S': [1, 2],
        }

def digitize(site):
	"""Return integer representation of a site.
	
	Returns a list of integers, each one represents one non-degenerate
	variant of the given site.
	"""
	sites = [1]
	for begin in range(len(site)):
		if site[begin] != 'N':
			break
	else:
		return sites
	end = len(site)
	while site[end - 1] == 'N':
		end -= 1
	for nucl in site[begin:end]:
		if nucl in nucls:
			digit = nucls[nucl]
			sites = [digit + (dsite << 2) for dsite in sites]
		else:
			sites = [digit + (dsite << 2) for dsite in sites
			         for digit in dnucls[nucl]]
	return sites

def digitize_withl(site):
	"""Return integer representation of a site and its length.
	
	Returns a list of integers, each one represents one non-degenerate
	variant of the given site.
	"""
	sites = [1]
	begin = 0
	while site[begin] == 'N':
		begin += 1
	end = len(site)
	while site[end - 1] == 'N':
		end -= 1
	for nucl in site[begin:end]:
		if nucl in nucls:
			digit = nucls[nucl]
			sites = [digit + (dsite << 2) for dsite in sites]
		else:
			sites = [digit + (dsite << 2) for dsite in sites
			         for digit in dnucls[nucl]]
	return sites, end-begin

def _addN(start, arr_site, init_site, eL, this_step, next_step):
	if eL == 1:
		return
	for i in range(start, len(arr_site)):
		if arr_site[i] == 'N':
			continue
		arr_site[i] = 'N'
		this_step.append(digitize_withl(arr_site))
		_addN(i+1, arr_site, init_site, eL-1, next_step, this_step)
		arr_site[i] = init_site[i]

class Site():
	
	"""A parent wrapper class for a site."""
	
	def __init__(self, site):
		"""Site(site)
		
		    site -- string, could contain ATGCBDHVSWMKRYN symbols.
		"""
		self.str_site = site.upper().strip('N')
		self.L = len(self.str_site)
		self.eL = len(site.upper().replace('N', ''))
		self.dsite = digitize(self.str_site)
		self._prepare()
	
	def _prepare(self):
		"""Site preparation for expected number calculation."""
		pass
	
	def get_length(self, effective=True):
		"""Get length of the site.
		
		    effective -- True (default) if effective length should be
		returned, else False. Effective length is a number of meaning
		(not N) postitions.
		"""
		return self.eL if effective else self.L
	
	def calc_observed(self, counts):
		"""Calculate observed number of occurences of the site by counts.
		
		    counts -- Counts object.
		"""
		return counts.get_count(self.dsite)
	
	def calc_expected(self, counts):
		"""Estimate expected number of occurences of the site.
		
		Simplest estimation is used based on the assumption that all
		positions of the site are independent.
		    counts -- Counts object.
		"""
		expected = counts.get_total(self.L)
		for nucl in self.str_site:
			expected *= counts.get_freq(dnucls[nucl], 1)
		return expected
	
	def calc_contrast(self, counts):
		"""Calculate contrast ratio.
		
		    counts -- Counts object.
		"""
		expected = self.calc_expected(counts) or float("NaN")
		return self.calc_observed(counts) / expected
	
	def __len__(self):
		return self.L
	
	def __str__(self):
		return self.str_site

class MarkovSite(Site):
	
	"""Site wrapper implementing Mmax based expected number calculation."""
	
	def _prepare(self):
		self.rpart = digitize(self.str_site[1:])
		self.lpart = digitize(self.str_site[:-1])
		self.cpart = digitize(self.str_site[1:-1])
	
	def calc_expected(self, counts):
		"""Estimate expected number of the site with Mmax based method."""
		if self.eL == 1:
			return counts.get_total(1) * len(self.dsite) / 4.0
		div = counts.get_count(self.cpart)
		if div == 0:
			return float('NaN')
		num = counts.get_count(self.lpart) * counts.get_count(self.rpart)
		return float(num) / div

class PevznerSite(Site):
	
	"""Site wrapper implementing Pevzner's expected number calculation."""
	
	def _prepare(self):
		arr_site = list(self.str_site)
		self.singleN = []
		self.doubleN = []
		for i in range(self.L):
			if arr_site[i] == 'N':
				continue
			arr_site[i] = 'N'
			self.singleN.append(digitize(arr_site))
			for j in range(i+1, self.L):
				if arr_site[j] == 'N':
					continue
				arr_site[j] = 'N'
				self.doubleN.append(digitize(arr_site))
				arr_site[j] = self.str_site[j]
			arr_site[i] = self.str_site[i]
	
	def calc_expected(self, counts):
		"""Estimate expected number of the site with Pevzner's method."""
		if self.eL == 1:
			return counts.get_total(1) * len(self.dsite) / 4.0
		div = 1.0
		for dsite in self.doubleN:
			div *= counts.get_count(dsite)
		if div == 0.0:
			return float('NaN')
		div = pow(div, 2.0/(self.eL*self.eL - self.eL))
		num = 1.0
		for dsite in self.singleN:
			num *= counts.get_count(dsite)
		return pow(num, 2.0/self.eL) / div

class KarlinSite(Site):
	
	"""Site wrapper implementing Karlin's expected number calculation."""
	
	def _prepare(self):
		arr_site = list(self.str_site)
		self.oddN = []
		self.evenN = []
		_addN(0, arr_site, self.str_site, self.eL, self.oddN, self.evenN)
	
	def calc_expected(self, counts):
		"""Estimate expected number of the site with Karlin's method."""
		if self.eL == 1:
			return counts.get_total(1) * len(self.dsite) / 4.0
		div = 1.0
		for dsite, dlen in self.evenN:
			div *= counts.get_freq(dsite, dlen)
		if div == 0.0:
			return float('NaN')
		num = counts.get_total(self.L)
		for dsite, dlen in self.oddN:
			num *= counts.get_freq(dsite, dlen)
		return num / div

def dump_sl(site_list, ounsl):
	"""Dump collection of wrapped sites."""
	with ounsl:
		cPickle.dump(site_list, ounsl, -1)

def load_sl(innsl):
	"""Load collection of wrapped sites from the dump file."""
	with innsl:
		return cPickle.load(innsl)

