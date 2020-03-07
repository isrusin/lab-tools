#! /usr/bin/env python3

import sys

if len(sys.argv) != 2:
    print("Usage: <script> [@]usa_list")
    sys.exit(1)


COMPLS = {
    "A": "T", "T": "A", "C": "G", "G": "C",
    "a": "t", "t": "a", "c": "g", "g": "c"
}
OUTPUT_WIDTH = 80

def get_compl(seq):
    compl = []
    for nucl in seq[::-1]:
        compl.append(COMPLS.get(nucl, "?"))
    return "".join(compl)

def parse_usa(filename):
    entries = dict()
    with open(filename) as inusa:
        for line in inusa:
            filename, entry_coords = line.strip().split(":", 1)
            seqid = entry_coords
            coords = None
            if "[" in entry_coords:
                seqid, coord_str = entry_coords.split("[", 1)
                parts = coord_str.strip("]").split(":")
                start = int(parts[0])
                stop = int(parts[1])
                reverse = len(parts) == 3 and parts[2] == "r"
                coords = (start, stop, reverse)
            coord_dict = entries.setdefault(filename, dict())
            coord_dict.setdefault(seqid, []).append(coords)
    return entries #{filename: {ID: [(start, stop, reversed), .., None]}}

def extract_frags(seq, coord_list):
    frags = []
    for coords in coord_list:
        if coords:
            start, stop, reverse = coords
            frag = seq[start-1: stop] #coords from 1 and both inclusive
            if reverse:
                frag = get_compl(frag)
            frags.append(frag)
        else:
            frags.append(seq)
    return frags

def print_frags(seqid, seq, coord_dict):
    coord_list = coord_dict[seqid]
    frags = extract_frags(seq, coord_list)
    for frag, coords in zip(frags, coord_list):
        coord_tag = ""
        if coords:
            start, stop, reverse = coords
            coord_tag = "_%d_%d%s" % (start, stop, "_r" if reverse else "")
        print(">", seqid, coord_tag, sep="")
        for i in range(0, len(frag), OUTPUT_WIDTH):
            print(frag[i: i+OUTPUT_WIDTH])


if __name__ == "__main__":
    entries = parse_usa(sys.argv[1].lstrip("@"))
    for filename, coord_dict in entries.items():
        seqids = set(coord_dict)
        seqid = None
        seq = ""
        with open(filename) as infasta:
            for line in infasta:
                if line.startswith(">"):
                    if seqid in seqids:
                        print_frags(seqid, seq, coord_dict)
                    seqid_tag = line[1:].split()[0]
                    seqid = seqid_tag.split("|")[-1]
                    seq = ""
                else:
                    seq += line.strip()
        if seqid in seqids:
            print_frags(seqid, seq, coord_dict)

