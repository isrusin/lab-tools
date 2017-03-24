#! /usr/bin/env python

"""Draw histograms obtained by make_histogram on a single plot."""

import argparse
from matplotlib import pyplot
from os.path import basename, splitext
import sys


def load_hst(inhst):
    """Load histogram from .hst file"""
    xvals = []
    yvals = []
    for line in inhst:
        xval, yval = line.strip().split("\t")
        xvals.append(float(xval))
        yvals.append(float(yval))
    return xvals, yvals


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Draw histrograms obtained by make_histrogram."
    )
    parser.add_argument(
        "inhst", metavar="HIST", type=argparse.FileType("r"), nargs="+",
        help="a histogram to draw"
    )
    parser.add_argument(
        "-o", "--out", dest="oupic", metavar="FILE", default="hists.png",
        help="""output figure file, the type is parsed from the extension;
        default is 'hists.png'"""
    )
    parser.add_argument(
        "-Y", "--ylim-max", metavar="N", type=float,
        help="y-axis upper limit; default is calculated from the inputs"
    )
    parser.add_argument(
        "--dpi", metavar="N", type=int, default=100,
        help="DPI of the output picture; default is 100"
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
    max_val = args.ylim_max
    if max_val is None:
        max_val = max(max(yvals) for _xvals, yvals in hists)
        max_val += 5 - max_val % 5
    fig = pyplot.figure(1, (5, 3.5), 300)
    fig.subplots_adjust(left=0.085, bottom=0.11, right=0.98, top=0.975)
    color_iter = iter(colors)
    pyplot.rcParams["font.size"] = 8.0
    pyplot.xlabel("Compositional bias value", fontsize=10)
    pyplot.ylabel("Site-chromosome pairs, %", fontsize=10)
    ax = pyplot.subplot(1, 1, 1)
    for name, (xvals, yvals) in zip(names, hists):
        params = {"lw": 1.0, "label": name, "dash_capstyle": "round"}
        try:
            params["color"] = color_iter.next()
        except StopIteration:
            pass
        pyplot.plot(xvals, yvals, **params)
    ticks = [0.2 * i  for i in range(11)]
    labs = ["%.1f" % tick for tick in ticks]
    pyplot.xticks(ticks, labs)
    ax.grid()
    ax.legend()
    pyplot.xlim(0, 2)
    pyplot.ylim(0, min(max_val, 99)) # '100%' dislocates the y-axis label
    pyplot.savefig(args.oupic, dpi=args.dpi)


if __name__ == "__main__":
    sys.exit(main())
