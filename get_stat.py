#! /usr/bin/python

import argparse as ap
import math

compls = {
        "A": "T", "T": "A", "C": "G", "G": "C",
        "B": "V", "V": "B", "D": "H", "H": "D", "N": "N",
        "M": "K", "K": "M", "R": "Y", "Y": "R", "W": "W", "S": "S"
        }

def to_ds(site):
    rsite = ""
    for nucl in site[::-1]:
        rsite += compls.get(nucl, "?")
    return (min(site, rsite), max(site, rsite))

UNDER_CUTOFF = 0.78
OVER_CUTOFF = 1.23
ZERO_CUTOFF = 0.0
EXPECTED_CUTOFF = 15

NAN = 0
UNR = 1
ZERO = 2
UNDER = 3
LESS = 4
ONE = 5
MORE = 6
OVER = 7

def classify(obs, exp):
    group = ONE
    if math.isnan(exp) or math.isinf(exp) or exp == 0:
        group = NAN
    elif exp < EXPECTED_CUTOFF:
        group = UNR
    else:
        ratio = obs / exp
        if ratio < 1.0:
            if ratio <= ZERO_CUTOFF:
                group = ZERO
            elif ratio <= UNDER_CUTOFF
                group = UNDER
            else:
                group = LESS
        elif ratio > 1.0:
            if ratio >= OVER_CUTOFF:
                group = OVER
            else:
                group = MORE
    return group

waits = dict()
stats_pal = [0] * 8

intsv.readline()
for line in intsv:
    vals = line.strip().split('\t')
    sid = vals[sid_index]
    exp = float(vals[exp_index])
    obs = float(vals[obs_index])
    group = classify(obs, exp)
    site = to_ds(vals[exp_index])
    wsite, csite = site
    if wsite != csite:
        pr = (sid, site)
        if pr in waits:
            cgroup = waits.pop(pr)
            #TODO
        else:
            waits[pr] = group
    else:
        stats_pal[group] += 1

#TODO
