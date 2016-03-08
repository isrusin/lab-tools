import ctypes as ct

class Counts():
	@staticmethod
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
		return length, counts, totals
	
	def __init__(self, incnt):
		self.length, self.counts, self.totals = Counts.load_counts(incnt)
	
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
