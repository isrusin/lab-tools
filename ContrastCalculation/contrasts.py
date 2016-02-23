#from counts import Counts

dig_nucls = {
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
	mask = 1 << 2*len(site)
	dig_sites = [mask]
	mask >>= 2
	for nucl in site:
		new_sites = []
		for digit in dig_nucls[nucl]:
			i = digit * mask
			new_sites.extend(dig_site + i for dig_site in dig_sites)
		mask >>= 2
		dig_sites = new_sites
	return dig_sites

def analogize(dig_site):
	nucls = "ACGT"
	site = ""
	while dig_site > 1:
		site = nucls[dig_site & 3] + site
		dig_site >>= 2
	return site

def calc_expected_P(site, counts):
	arr_site = list(site)
	singleN = float(counts.get_count(digitize(arr_site[1:])))
	singleN *= float(counts.get_count(digitize(arr_site[:-1])))
	doubleN = float(counts.get_count(digitize(arr_site[1:-1])))
	for i in range(1, len(site)-1):
		if arr_site[i] == 'N':
			continue
		arr_site[i] = 'N'
		singleN *= counts.get_count(digitize(arr_site))
		doubleN *= counts.get_count(digitize(arr_site[1:]))
		for j in range(i+1, len(site)-1):
			if arr_site[j] == 'N':
				continue
			arr_site[j] = 'N'
			doubleN *= counts.get_count(digitize(arr_site))
			arr_site[j] = site[j]
		doubleN *= counts.get_count(digitize(arr_site[:-1]))
		arr_site[i] = site[i]
	eL = len(site.replace('N', ''))
	return pow(singleN, 2.0/eL) / pow(doubleN, 2.0/(eL*eL-eL))

def calc_expected_M(site, counts):
	rpart = counts.get_count(digitize(site[1:]))
	lpart = counts.get_count(digitize(site[:-1]))
	cpart = counts.get_count(digitize(site[1:-1]))
	return rpart * lpart / float(cpart)

def get_values(site, counts, calc_expected, is_freq):
	length = len(site)
	No = counts.get_count(digitize(site))
	total = counts.get_total(length)
	Ne = calc_expected(site, counts)
	if is_freq:
		Ne *= total
	return No, Ne, No / Ne, total

#counts = Counts(open("AE000513.1.cnt"))
#print get_values("GTCTTG", counts, calc_expected_M, False)
#print get_values("GTCTTG", counts, calc_expected_P, False)
#print counts.totals
