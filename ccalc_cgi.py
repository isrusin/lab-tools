#! /usr/bin/python

import cgi
import tempfile as tmp
import ContrastCalculation.counts as cnt
import ContrastCalculation.sites as st

MAX_SIZE = 1 #in MiB
TEMP_DIR = "../ccalc/tmp"

def return_message(message):
	print "Content-Type: text/html"
	print "<h1>Error!</h1>"
	print message
	exit()

def load_in_temp(form, name, tag, suffix):
	if name not in form:
		return_message("%s file is required." % tag)
	infile = form[name].file
	with infile:
		data = infile.read(MAX_SIZE * (1024 ** 2))
		if infile.readline() != "":
			return_message(
			        "%s file is too big, max size is %d MiB." %
			        (tag, MAX_SIZE)
			)
	tmpfile = tmp.NamedTemporaryFile(
	        suffix=suffix, dir=TEMP_DIR, delete=False
	)
	with tmpfile:
		tmpfile.write(data)
	return tmpfile.name

form = cgi.FieldStorage()

m_flag = form.getvalue("mmax", "no") == "yes"
p_flag = form.getvalue("pevzner", "no") == "yes"
k_flag = form.getvalue("karlin", "no") == "yes"

if not (m_flag or p_flag or k_flag):
	return_message("At least one method should be selected.")

ouline = "{Site}\t{Fo}"
title = "Site\tObserved number"
if m_flag:
	ouline += "\t{Me}\t{Mr}"
	title += "\tMmax expected\tMmax ratio"
if p_flag:
	ouline += "\t{Pe}\t{Pr}"
	title += "\tPevzner's expected\tPevzner's ratio"
if k_flag:
	ouline += "\t{Ke}\t{Kr}"
	title += "\tKarlin's expected\tKarlin's ratio"
ouline += "\t{L}\n"
title += "\tSequence length\n"

stl_path = load_in_temp(form, "sites", "Site list", ".stl")
sites = []
skipped = []
length = 0
with open(stl_path) as instl:
	for line in instl:
		site = line.strip()
		if not site:
			continue
		if len(site) > 10:
			skipped.append(site)
		else:
			sites.append(site)
			length = max(length, len(site))

if not length:
	return_message("There is no fitting sites in the list.")

fasta_path = load_in_temp(form, "fasta", "Fasta", ".fasta")
counts = cnt.calculate_counts(fasta_path, length)
outmp = tmp.NamedTemporaryFile(suffix=".tsv", dir=TEMP_DIR, delete=False)
with outmp:
	outmp.write(title)
	for site in sites:
		vals = {"Site": site}
		wrapped = st.Site(site)
		vals["Fo"] = counts.get_count(wrapped.dsite)
		vals["L"] = counts.get_total(wrapped.L)
		if m_flag:
			me = st.MarkovSite(site).calc_expected(counts)
			vals["Me"] = me
			vals["Mr"] = vals["Fo"] / me
		if p_flag:
			pe = st.PevznerSite(site).calc_expected(counts)
			vals["Pe"] = pe
			vals["Pr"] = vals["Fo"] / pe
		if k_flag:
			ke = st.KarlinSite(site).calc_expected(counts)
			vals["Ke"] = ke
			vals["Kr"] = vals["Fo"] / ke
		outmp.write(ouline.format(**vals))

oupath = outmp.name
ouname = oupath.rsplit("/", 1)[-1]
with open("../ccalc/ccalc_result_form.html") as inform:
	ouhtml = inform.read()
ouhtml = ouhtml.replace("@filepath", oupath).replace("@filename", ouname)

skipped_html = ""
if skipped:
	skipped_html = "<h4>Following sites are too long, skipped:</h4>\n"
	skipped_html += "<p>\n" + "<br>\n".join(skipped) + "</p>\n"

ouhtml = ouhtml.replace("@skipped", skipped_html)
print "Content-Type: text/html"
print ouhtml
