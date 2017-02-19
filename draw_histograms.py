#! /usr/bin/env python

"""Draw histograms obtained by make_histogram.py on the same plot."""

import argparse
import matplotlib.pyplot as plt
import sys
from os.path import basename, splitext

def load_hst(inhst):
    xvals = []
    yvals = []
    for line in inhst:
        xval, yval = line.strip().split("\t")
        xvals.append(float(xval))
        yvals.append(float(yval))
    return xvals, yvals

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Draw histrograms obtained by make_histrogram.py."
    )
    parser.add_argument(
        "inhst", metavar="HIST", type=argparse.FileType("r"), nargs="+",
        help="a histogram to draw"
    )
    parser.add_argument(
        "-o", "--out", dest="oupic", metavar="FILE", default="hists.png",
        help="output figure file, the type is parsed from the extension"
    )
    args = parser.parse_args(argv)
    colors = ["#ff0000", "#00bb33", "#0033bb",
              "#ffbb33", "#ff33bb", "0.5", "0.1"]
    hists = []
    names = []
    for inhst in args.inhst:
        names.append(splitext(basename(inhst.name))[0])
        with inhst:
            hists.append(load_hst(inhst))
    fig = plt.figure(1, (5, 3.5), 300)
    fig.subplots_adjust(left=0.085, bottom=0.11, right=0.98, top=0.975)
    color_iter = iter(colors)
    plt.rcParams["font.size"] = 8.0
    plt.xlabel("Compositional bias value", fontsize=10)
    plt.ylabel("Site-chromosome pairs, %", fontsize=10)
    ax = plt.subplot(1, 1, 1)
    for name, (xvals, yvals) in zip(names, hists):
        params = {"lw": 1.0, "label": name, "dash_capstyle": "round"}
        try:
            params["color"] = color_iter.next()
        except StopIteration:
            pass
        plt.plot(xvals, yvals, **params)
    ticks = [0.2 * i  for i in range(11)]
    labs = ["%.1f" % tick for tick in ticks]
    plt.xticks(ticks, labs)
    ax.grid()
    ax.legend()
    plt.xlim(0, 2)
    plt.savefig(args.oupic, dpi=150)

if __name__ == "__main__":
    sys.exit(main())
