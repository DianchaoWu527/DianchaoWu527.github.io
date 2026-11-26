#!/usr/bin/env python3
"""Build the site's schematic figures in the editorial palette.

Run: python3 scripts/build_figures.py

Outputs (all text is converted to paths, so the SVGs do not depend on the
viewer's installed fonts):

  figures/langevin-potential.svg        periodic-potential schematic (poster hero)
  figures/langevin-potential-thumb.svg  label-free variant for the homepage
  figures/mbs-expansion.svg             price expansion, typeset for the homepage
  figures/langevin-figure1.png          manuscript Figure 1, recoloured (see below)
  figures/mbs-error-orders.svg          Figure 1 of arXiv:2611.33367, recoloured

The manuscript's Figure 1 (kolmogorov_distance_rate.png) is only available as a
raster export, so `recolour_figure1` maps its default matplotlib colours onto
the site palette pixel by pixel. Geometry and data are untouched. If the raw
simulation output is at hand, redraw the figure with SITE_RC instead and drop
this step.

The MBS figure is the vector file from the preprint (figures/src/rp_numerics.pdf).
`recolour_mbs_figure` converts it with pdftocairo and swaps its five colours for
the site palette; curves, markers and labels are otherwise untouched.

SITE_RC is the shared style: reuse it when regenerating data figures so every
plot on the site matches (cream background, navy ink, muted grey text).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"

BG, INK, MUTED, LINE = "#f7f5ef", "#24292f", "#606975", "#deded8"
NAVY, BLUE, TEAL, PALE, OCHRE = "#294b67", "#426f91", "#428c89", "#789eae", "#b18b46"

SITE_RC = {
    "svg.fonttype": "path",          # glyphs as outlines: no font fallback in browsers
    "svg.hashsalt": "dianchaowu.com",  # stable ids, reproducible output
    "font.family": "DejaVu Sans",
    "mathtext.fontset": "dejavusans",
    "figure.facecolor": "none",
    "axes.facecolor": "none",
    "savefig.facecolor": "none",
    "axes.edgecolor": LINE,
    "axes.labelcolor": MUTED,
    "axes.prop_cycle": matplotlib.cycler(color=[NAVY, BLUE, TEAL, PALE, OCHRE]),
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "grid.color": LINE,
    "grid.linewidth": 0.6,
    "lines.linewidth": 1.6,
}


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / name, format="svg", metadata={"Date": None, "Creator": None})
    plt.close(fig)


def potential(labels=True):
    """One cell repeats; the unwrapped displacement accumulates across cells."""
    width, height = (5.355, 2.6655) if labels else (5.355, 2.05)
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0.03, 0.0, 0.94, 1.0])
    q = np.linspace(-0.06, 2.06, 900)
    v = np.cos(2 * np.pi * q)
    floor = -1.22
    if labels:   # the thumbnail stays pure line art, like the typeset one beside it
        ax.fill_between(q, floor, v, color=NAVY, alpha=0.055, linewidth=0)
    for cell in (0, 1, 2):
        ax.plot([cell, cell], [floor - (0.75 if labels else 0.1), 1.85], color=LINE,
                linewidth=0.8, dashes=(2.4, 4), zorder=0)
    k = 1.0 if labels else 1.7   # the thumbnail is shown at ~40% size: thicken its marks
    ax.plot(q, v, color=NAVY, linewidth=2.2 * k, solid_capstyle="round")

    q0, qt = 0.4, 1.6
    y0 = np.cos(2 * np.pi * q0)
    ax.scatter([q0], [y0], s=62 * k * k, color=OCHRE, edgecolor=BG, linewidth=1.0 * k, zorder=5)
    ax.scatter([qt], [y0], s=96 * k * k, color=NAVY, edgecolor=BG, linewidth=1.0 * k, zorder=5)
    ax.annotate("", xy=(qt, 1.42), xytext=(q0, 1.42),
                arrowprops=dict(arrowstyle="->", color=NAVY, linewidth=1.5 * k,
                                shrinkA=0, shrinkB=0, mutation_scale=11 * k))
    if labels:
        ax.text(1.0, 1.56, r"Unwrapped displacement  $Q_T - Q_0$", color=NAVY,
                fontsize=10, ha="center", va="bottom")
        # In the open valley, clear of the curve on both sides.
        ax.text(0.5, 0.52, r"$V(q)=\cos(2\pi q)$", color=MUTED, fontsize=11.5,
                ha="center", va="center")
        ax.text(q0, floor - 0.14, r"$Q_0$", color=INK, fontsize=13, ha="center", va="top")
        ax.text(qt, floor - 0.14, r"$Q_T$", color=INK, fontsize=13, ha="center", va="top")
        ax.text(1.0, floor - 0.72, "One cell repeats; the travelled distance accumulates.",
                color=MUTED, fontsize=9, ha="center", va="center")
        ax.set_ylim(floor - 0.98, 2.02)
    else:
        ax.set_ylim(floor - 0.12, 1.9)
    ax.set_xlim(-0.06, 2.06)
    ax.axis("off")
    return fig


def expansion():
    """Theorem 4.1 / Corollary 4.2 of arXiv:2611.33367, typeset as a figure."""
    with matplotlib.rc_context({"mathtext.fontset": "cm"}):
        fig = plt.figure(figsize=(5.355, 2.05))
        fig.text(0.5, 0.64, r"$P^{\varepsilon}=P^{0}+\varepsilon Y\,+R^{\varepsilon}$",
                 color=NAVY, fontsize=38, ha="center", va="center")
        fig.text(0.5, 0.23,
                 r"$\Vert R^{\varepsilon}\Vert_{\infty}\leq C\,\varepsilon^{2}\,\Vert\zeta\Vert_{\infty}^{2}$",
                 color=MUTED, fontsize=26, ha="center", va="center")
        return fig


def _rgb(hex_colour):
    return np.array([int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)], dtype=float) / 255


def recolour_figure1(source=ROOT / "kolmogorov_distance_rate.png", width=1856):
    """Map tab:blue/orange/green/red and the grey ink onto the site palette.

    Each pixel is read as `white * (1 - a) + source_colour * a`; the output keeps
    the coverage `a` and swaps the colour, on a transparent background.
    """
    from PIL import Image

    rgb = np.asarray(Image.open(source).convert("RGB"), dtype=float) / 255
    hi, lo = rgb.max(axis=2), rgb.min(axis=2)
    sat = hi - lo
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360

    out = np.zeros(rgb.shape[:2] + (4,))
    # Grey ink: text, spines and grid. The exponent keeps text dark and grid faint.
    grey_a = np.clip((1 - rgb.mean(axis=2)) / 0.85, 0, 1) ** 1.45
    out[..., :3] = _rgb("#454e59")
    out[..., 3] = grey_a

    classes = [  # (hue range, source colour, site colour)
        ((180, 260), "#1f77b4", NAVY),    # Kolmogorov distance, histogram
        ((15, 55), "#ff7f0e", TEAL),      # fitted slope
        ((75, 165), "#2ca02c", MUTED),    # reference slope -1/2
        ((275, 375), "#ff0000", OCHRE),   # matching Gaussian
    ]
    coloured = sat > 0.06
    for (h0, h1), src, dst in classes:
        mask = coloured & (((hue >= h0) & (hue <= h1)) | ((hue + 360 >= h0) & (hue + 360 <= h1)))
        ink = 1 - _rgb(src)
        a = np.clip(((1 - rgb) @ ink) / (ink @ ink), 0, 1)
        out[mask, :3] = _rgb(dst)
        out[mask, 3] = a[mask]

    image = Image.fromarray((out * 255).round().astype("uint8"), "RGBA")
    height = round(image.height * width / image.width)
    image = image.resize((width, height), Image.LANCZOS)
    OUT.mkdir(exist_ok=True)
    image.save(OUT / "langevin-figure1.png", optimize=True)


def recolour_mbs_figure(source=OUT / "src" / "rp_numerics.pdf"):
    """Figure 1 of arXiv:2611.33367 in the site palette (needs poppler's pdftocairo)."""
    import subprocess

    target = OUT / "mbs-error-orders.svg"
    subprocess.run(["pdftocairo", "-svg", str(source), str(target)], check=True)
    swaps = {
        "rgb(0%, 0%, 0%)": "#454e59",                               # text, axes
        "rgb(4.31366%, 4.31366%, 4.31366%)": MUTED,                 # reference slopes
        "rgb(47.842407%, 47.450256%, 45.881653%)": PALE,            # price change
        "rgb(16.470337%, 47.058105%, 83.920288%)": NAVY,            # remainder, symmetric law
        "rgb(92.155457%, 40.783691%, 20.391846%)": OCHRE,           # skewed law
        "rgb(100%, 100%, 100%)": BG,                                # background, open markers
    }
    svg = target.read_text(encoding="utf-8")
    for old, new in swaps.items():
        assert old in svg, f"colour {old} not found: the source figure changed"
        svg = svg.replace(old, new)
    assert "rgb(" not in svg, "unmapped colour left in the figure"
    target.write_text(svg, encoding="utf-8")


def main():
    recolour_figure1()
    recolour_mbs_figure()
    with matplotlib.rc_context(SITE_RC):
        save(potential(labels=True), "langevin-potential.svg")
        save(potential(labels=False), "langevin-potential-thumb.svg")
        save(expansion(), "mbs-expansion.svg")


if __name__ == "__main__":
    main()
