#! /usr/bin/env python

"""Draw 2D-histogram of compositional bias obtained with make_hist2d."""

import argparse
from matplotlib import pyplot
from matplotlib.colors import LogNorm
from os.path import basename, splitext
import sys


def load_hst2d(inhst):
    """Load histogram from .h2d file"""
    xvals = []
    yvals = []
    matrix = []
    for line in inhst:
        if line.startswith("##"):
            continue
        vals = line.strip().split("\t")
        if line.startswith("#"):
            xvals = [float(i) for i in vals[1:]]
        else:
            yvals.append(float(vals[0]))
            matrix.append([float(i) for i in vals[1:]])
    return xvals, yvals, matrix


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Draw 2D-histrogram obtained with make_hist2d."
    )
    parser.add_argument(
        "inhst", metavar="HIST", type=argparse.FileType("r"),
        help="a histogram to draw"
    )
    parser.add_argument(
        "-o", "--out", dest="oupic", metavar="FILE", default="hist.png",
        help="""output figure file, the type is parsed from the extension;
        default is 'hist.png'"""
    )
    parser.add_argument(
        "--dpi", metavar="N", type=int, default=100,
        help="DPI of the output picture; default is 100"
    )
    args = parser.parse_args(argv)
    with args.inhst as inhst:
        xvals, yvals, matrix = load_hst2d(inhst)
    fig = pyplot.figure(1, (5, 5), 300)
    fig.subplots_adjust(left=0.11, bottom=0.08, right=0.98, top=0.98)
    pyplot.rcParams["font.size"] = 8.0
    pyplot.xlabel("Compositional bias value", fontsize=10)
    pyplot.ylabel("Compositional bias value", fontsize=10)
    ax = pyplot.subplot(1, 1, 1)
    pyplot.imshow(matrix, cmap="Blues", interpolation="none",
                  norm=LogNorm())
    xstep = (len(xvals) + 5) // 10
    xticks = range(len(xvals))[::xstep]
    xlabs = ["%.2f" % val for val in xvals[::xstep]]
    pyplot.xticks(xticks, xlabs)
    ystep = (len(yvals) + 5) // 10
    yticks = range(len(yvals))[::ystep]
    ylabs = ["%.2f" % val for val in yvals[::ystep]]
    pyplot.yticks(yticks, ylabs)
    ax.invert_yaxis()
    pyplot.savefig(args.oupic, dpi=args.dpi)


if __name__ == "__main__":
    sys.exit(main())
