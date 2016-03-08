import cPickle

nucls = {'A': 0, 'C': 1, 'G': 2, 'T': 3}

dnucls = {
        'N': [0, 1, 2, 3],
        'B': [1, 2, 3],
        'D': [0, 2, 3],
        'H': [0, 1, 2],
        'V': [0, 1, 2],
        'M': [0, 1], 'K': [2, 3],
        'R': [0, 2], 'Y': [1, 3],
        'W': [0, 3], 'S': [1, 2],
        }

def digitize(site):
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

def dump_sl(site_list, ounsl):
	with ounsl:
		cPickle.dump(site_list, ounsl, -1)

def load_sl(innsl):
	with innsl:
		return cPickle.load(innsl)

class Site():
	def __init__(self, site):
		self.str_site = site.strip('N')
		self.L = len(self.str_site)
		self.eL = len(site.replace('N', ''))
		self.dsite = digitize(self.str_site)
	
	def calc_expected(self, counts):
		pass

class MarkovSite(Site):
	def __init__(self, site):
		Site.__init__(self, site)
		self.rpart = digitize(self.str_site[1:])
		self.lpart = digitize(self.str_site[:-1])
		self.cpart = digitize(self.str_site[1:-1])
	
	def calc_expected(self, counts):
		if self.eL == 1:
			return counts.get_total(1) * len(self.dsite) / 4.0
		div = counts.get_count(self.cpart)
		if div == 0:
			return float('NaN')
		num = counts.get_count(self.lpart) * counts.get_count(self.rpart)
		return float(num) / div

class PevznerSite(Site):
	def __init__(self, site):
		Site.__init__(self, site)
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

def digitize_withl(site):
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

class KarlinSite(Site):
	def __init__(self, site):
		Site.__init__(self, site)
		arr_site = list(self.str_site)
		self.oddN = []
		self.evenN = []
		_addN(0, arr_site, self.str_site, self.eL, self.oddN, self.evenN)
	
	def calc_expected(self, counts):
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

