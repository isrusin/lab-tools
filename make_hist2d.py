#! /usr/bin/env python

"""Make 2D-histrogram of compositional bias values."""

import argparse
import math
import sys


COMPLS = {
    "A": "T", "B": "V", "T": "A", "V": "B", "W": "W",
    "C": "G", "D": "H", "G": "C", "H": "D", "S": "S",
    "K": "M", "M": "K", "R": "Y", "Y": "R", "N": "N"
}


def get_ds_site(site):
    rsite = "".join(COMPLS[nucl] for nucl in site[::-1])
    dsite = (min(site, rsite), max(site, rsite))
    return dsite


class LineParser(object):
    def __init__(self, indices):
        id_index, site_index, obs_index, exp_index = indices
        self.id_index = id_index
        self.site_index = site_index
        self.obs_index = obs_index
        self.exp_index = exp_index

    def __call__(self, line):
        vals = line.strip().split("\t")
        sid = vals[self.id_index]
        site = get_ds_site(vals[self.site_index])
        observed = float(vals[self.obs_index])
        expected = float(vals[self.exp_index])
        return (sid, site), observed, expected


def load_ds_counts(intsv, line_parser, pairs, cutoff):
    counts = dict()
    with intsv:
        intsv.readline()
        for line in intsv:
            pair, observed, expected = line_parser(line)
            if pair not in pairs:
                continue
            if math.isnan(expected) or expected <= cutoff:
                observed, expected = (0, 0)
            observed_, expected_ = counts.get(pair, (0, 0))
            observed += observed_
            expected += expected_
            counts[pair] = (observed, expected)
    return counts


class BinsManager(object):
    def __init__(self, bins_number, start=0, end=2.0):
        self.number = bins_number
        self.start = start
        self.end = end
        self.width = end - start

    def get_bin(self, value):
        bin_index = int((value - self.start) * self.number / self.width)
        return min(bin_index, self.number)

    def get_labels(self):
        correction = self.start + 0.5 # shift to bin center
        labels = []
        for bin_index in range(self.number + 1):
            label = (bin_index + correction) * self.width / self.number
            labels.append(label)
        return labels


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Make 2D-histrogram of compositional bias values."
    )
    io_group = parser.add_argument_group(title="Input/output agruments")
    io_group.add_argument(
        "intab1", metavar="TSV1", type=argparse.FileType("r"),
        help="""first TSV file with compositional bias values, use '-'
        for STDIN"""
    )
    io_group.add_argument(
        "intab2", metavar="TSV2", type=argparse.FileType("r"),
        help="""second TSV file with compositional bias values, use '-'
        for STDIN"""
    )
    io_group.add_argument(
        "-i", dest="intrp", metavar="TRIOS", type=argparse.FileType("r"),
        default=sys.stdin, help="input list of triples, default STDIN"
    )
    io_group.add_argument(
        "-o", dest="ouhst", metavar="FILE", type=argparse.FileType("w"),
        default=sys.stdout, help="output file, default STDOUT"
    )
    parameter_group = parser.add_argument_group(
        title="Parameters", description="""Each option could be extended
        by '1' or '2' to change the parameter for the file separately."""
    )
    parameter_group.add_argument(
        "--bins", metavar="N", dest="bins_number", type=int, default=41,
        help="number of bins, default 41"
    )
    parameter_group.add_argument(
        "--bins1", dest="bins_number1", type=int,
        help=argparse.SUPPRESS
    )
    parameter_group.add_argument(
        "--bins2", dest="bins_number2", type=int,
        help=argparse.SUPPRESS
    )
    parameter_group.add_argument(
        "--cutoff", metavar="F", dest="cutoff", type=float, default=15,
        help="expected number cutoff, default 15"
    )
    parameter_group.add_argument(
        "--cutoff1", dest="cutoff1", type=float,
        help=argparse.SUPPRESS
    )
    parameter_group.add_argument(
        "--cutoff2", dest="cutoff2", type=float,
        help=argparse.SUPPRESS
    )
    parameter_group.add_argument(
        "--exp", "--expected", metavar="N", dest="exp_index", type=int,
        default=-3, help="index of expected number column, default -3"
    )
    parameter_group.add_argument(
        "--exp1", "--expected1", dest="exp_index1", type=int,
        help=argparse.SUPPRESS
    )
    parameter_group.add_argument(
        "--exp2", "--expected2", dest="exp_index2", type=int,
        help=argparse.SUPPRESS
    )
    parameter_group.add_argument(
        "--obs", "--observed", metavar="N", dest="obs_index", type=int,
        default=2, help="index of observed number column, default 2"
    )
    parameter_group.add_argument(
        "--obs1", "--observed1", dest="obs_index1", type=int,
        help=argparse.SUPPRESS
    )
    parameter_group.add_argument(
        "--obs2", "--observed2", dest="obs_index2", type=int,
        help=argparse.SUPPRESS
    )
    return parser.parse_args(argv)


def get_arg(name, args):
    default = args.__getattribute__(name)
    value1 = args.__getattribute__(name + "1")
    value1 = default if value1 is None else value1
    value2 = args.__getattribute__(name + "2")
    value2 = default if value2 is None else value2
    return value1, value2


def load_triples(intrp):
    pairs1 = set()
    pairs2 = set()
    triples = set()
    with intrp:
        for line in intrp:
            sid1, sid2, site = line.strip().split("\t")
            site = get_ds_site(site)
            triples.add(((sid1, site), (sid2, site)))
            pairs1.add((sid1, site))
            pairs2.add((sid2, site))
    return pairs1, pairs2, triples


def main(argv=None):
    args = parse_args(argv)
    obs_index1, obs_index2 = get_arg("obs_index", args)
    exp_index1, exp_index2 = get_arg("exp_index", args)
    cutoff1, cutoff2 = get_arg("cutoff", args)
    bins_number1, bins_number2 = get_arg("bins_number", args)
    ou_meta = ["## Compositional bias histogram 2D\n"]
    pairs1, pairs2, triples = load_triples(args.intrp)
    ou_meta.append("## Triples list: %s\n" % args.intrp.name)

    line_parser1 = LineParser((0, 1, obs_index1, exp_index1))
    counts1 = load_ds_counts(args.intab1, line_parser1, pairs1, cutoff1)
    bins_manager1 = BinsManager(bins_number1)
    labs1 = bins_manager1.get_labels()
    ou_meta.extend([
        "## Source1: %s\n" % args.intab1.name,
        "##   Bins number: (%d+1)\n" % bins_number1,
        "##   Expected cutoff: %.1f\n" % cutoff1,
    ])

    line_parser2 = LineParser((0, 1, obs_index2, exp_index2))
    counts2 = load_ds_counts(args.intab2, line_parser2, pairs2, cutoff2)
    bins_manager2 = BinsManager(bins_number2)
    labs2 = bins_manager2.get_labels()
    ou_meta.extend([
        "## Source2: %s\n" % args.intab2.name,
        "##   Bins number: (%d+1)\n" % bins_number2,
        "##   Expected cutoff: %.1f\n" % cutoff2,
    ])
    hist = []
    total = 0
    for lab in labs1:
        hist.append([0] * len(labs2))
    for pair1, pair2 in triples:
        observed1, expected1 = counts1[pair1]
        observed2, expected2 = counts2[pair2]
        if expected1 == 0 or expected2 ==0:
            continue
        bin1 = bins_manager1.get_bin(observed1 / expected1)
        bin2 = bins_manager2.get_bin(observed2 / expected2)
        hist[bin1][bin2] += 1
        total += 1
    sys.stderr.write("The histogram was build by %d values.\n" % total)
    ou_meta.append("## Total: %d\n" % total)
    with args.ouhst as ouhst:
        ouhst.writelines(ou_meta)
        ouhst.write("#Bin")
        for lab in labs2:
            ouhst.write("\t%.2f" % lab)
        ouhst.write("\n")
        if not total:
            total = 1
        for lab, row in zip(labs1, hist):
            ouhst.write("%.2f" % lab)
            for value in row:
                ouhst.write("\t%.2f" % (value * 100.0 / total, ))
            ouhst.write("\n")


if __name__ == "__main__":
    sys.exit(main())

