#!/usr/bin/env python3
"""
Frost Bank Tower — parametric architectural CAD study
Site plan · typical floor · north elevation · 3D massing GLB
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

from frost_tower_dimensions import (
    BASE_LENGTH_FT,
    BASE_WIDTH_FT,
    CROWN_HEIGHT_FT,
    CROWN_SETBACKS_FT,
    CROWN_TOP_SIDE_FT,
    FLOOR_COUNT,
    PARKING_LEVELS,
    PODIUM_FLOORS,
    PODIUM_HEIGHT_FT,
    ROOF_HEIGHT_FT,
    SITE_ADDRESS,
    SITE_SQFT,
    TOTAL_HEIGHT_FT,
    TYPICAL_FLOOR_SIDE_FT,
)

ROOT = Path(__file__).resolve().parent
BG = "#FAF9F6"
INK = "#2A2A2A"
MUTED = "#6E6A65"
GRID = "#D8D2C8"
GLASS = "#9EB4C8"
LIMESTONE = "#C9C0B0"
CROWN_LITE = "#B8D4E8"


def ft_to_draw(ft: float, scale_px_per_ft: float = 0.012) -> float:
    return ft * scale_px_per_ft


def draw_title_block(ax, x, y, w, h, sheet: str) -> None:
    cols = [x + w * i / 6 for i in range(7)]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", fill=False, ec=INK, lw=1.4))
    for i in range(1, 6):
        ax.plot([cols[i], cols[i]], [y, y + h], color=INK, lw=0.5)
    bands = [h * 0.78, h * 0.55, h * 0.32]
    for by in [y + h - b for b in bands]:
        ax.plot([x, x + w], [by, by], color=INK, lw=0.45)
    ax.text(cols[0] + 0.08, y + h - 0.18, "TITLE", fontsize=5.5, color=MUTED)
    ax.text(cols[0] + 0.08, y + h - 0.42, "Frost Bank Tower Study", fontsize=8, color=INK)
    ax.text(cols[3] + 0.08, y + h - 0.18, "SHEET", fontsize=5.5, color=MUTED)
    ax.text(cols[3] + 0.08, y + h - 0.42, sheet, fontsize=7, color=INK)
    rows = [
        ("LOCATION", "401 Congress Ave, Austin TX", "SCALE", "1/64\"=1'-0\"", "REV", "A"),
        ("ARCHITECT", "Duda/Paine + HKS", "HEIGHT", f"{TOTAL_HEIGHT_FT}'-0\"", "FLOORS", str(FLOOR_COUNT)),
        ("SOURCE", "Public reference dims", "CROWN", f"{CROWN_HEIGHT_FT}'-0\"", "STATUS", "STUDY"),
        ("AUTHOR", "Kristen Fenwick", "UNITS", "feet", "CLASS", "AEC"),
    ]
    y0 = y + h - bands[0]
    rh = bands[0] / 4
    for i, (a, b, c, d, e, f) in enumerate(rows):
        ry = y0 - (i + 0.55) * rh
        ax.text(cols[0] + 0.06, ry, a, fontsize=5, color=MUTED, va="center")
        ax.text(cols[1] + 0.06, ry, b, fontsize=5.8, color=INK, va="center")
        ax.text(cols[2] + 0.06, ry, c, fontsize=5, color=MUTED, va="center")
        ax.text(cols[3] + 0.06, ry, d, fontsize=5.8, color=INK, va="center")
        ax.text(cols[4] + 0.06, ry, e, fontsize=5, color=MUTED, va="center")
        ax.text(cols[5] - 0.06, ry, f, fontsize=5.8, color=INK, va="center", ha="right")
    name_x = (cols[4] + cols[5]) / 2
    ax.text(name_x, y + h * 0.12, "KRISTEN", fontsize=6, color=INK, ha="center", rotation=90, fontweight="light")
    ax.text(name_x, y + h * 0.04, "FENWICK", fontsize=6, color=INK, ha="center", rotation=90, fontweight="light")


def render_site_plan() -> None:
    fig, ax = plt.subplots(figsize=(12, 9), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_aspect("equal")

    ax.text(0.4, 8.5, "Frost Bank Tower — Site Plan Study", fontsize=16, color=INK, fontweight="light")
    ax.text(0.4, 8.1, f"{SITE_ADDRESS}  ·  Block 42  ·  {SITE_SQFT:,.0f} sf site",
            fontsize=8.5, color=MUTED)

    ox, oy = 2.0, 2.2
    s = 0.018
    site_w, site_d = 360 * s, 280 * s  # illustrative block envelope

    ax.add_patch(Rectangle((ox, oy), site_w, site_d, fill=False, ec=GRID, lw=1.2, ls="--"))
    ax.text(ox + site_w / 2, oy - 0.25, "SITE BOUNDARY (EST.)", ha="center", fontsize=7, color=MUTED)

    bw, bl = BASE_WIDTH_FT * s, BASE_LENGTH_FT * s
    bx = ox + (site_w - bl) / 2
    by = oy + (site_d - bw) / 2
    ax.add_patch(Rectangle((bx, by), bl, bw, fill=True, facecolor=LIMESTONE, edgecolor=INK, lw=2))
    ax.add_patch(Rectangle((bx + bl * 0.08, by + bw * 0.1), bl * 0.84, bw * 0.8,
                            fill=False, ec=GLASS, lw=1.4, ls="-"))

    # Congress Ave
    ax.plot([ox - 0.4, ox + site_w + 0.4], [oy - 0.55, oy - 0.55], color=INK, lw=2)
    ax.text(ox + site_w / 2, oy - 0.75, "CONGRESS AVENUE", ha="center", fontsize=8, color=INK)

    # Parking garage footprint (under podium)
    ax.add_patch(Rectangle((bx + bl * 0.05, by + bw * 0.05), bl * 0.35, bw * 0.9,
                            fill=False, ec=MUTED, lw=0.8, ls=(0, (4, 3))))
    ax.text(bx + bl * 0.22, by + bw * 0.5, f"PARKING\n{PARKING_LEVELS} LVLS",
            ha="center", va="center", fontsize=6, color=MUTED)

    ax.text(bx + bl / 2, by + bw + 0.35, "TOWER FOOTPRINT", ha="center", fontsize=8, color=INK)
    ax.annotate("", xy=(bx, by - 0.15), xytext=(bx + bl, by - 0.15),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.8))
    ax.text(bx + bl / 2, by - 0.35, f"{BASE_LENGTH_FT}'-0\"", ha="center", fontsize=8, color=INK)
    ax.annotate("", xy=(bx - 0.15, by), xytext=(bx - 0.15, by + bw),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.8))
    ax.text(bx - 0.38, by + bw / 2, f"{BASE_WIDTH_FT}'-0\"", ha="center", va="center",
            rotation=90, fontsize=8, color=INK)

    draw_title_block(ax, 7.8, 0.5, 3.8, 2.4, "A1.0")
    plt.savefig(ROOT / "frost_site_plan.png", dpi=220, bbox_inches="tight", facecolor=BG, pad_inches=0.25)
    plt.close()


def render_typical_floor() -> None:
    fig, ax = plt.subplots(figsize=(12, 9), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_aspect("equal")

    ax.text(0.4, 8.5, "Frost Bank Tower — Typical Office Floor Plan", fontsize=16, color=INK, fontweight="light")
    ax.text(0.4, 8.1, f"Floor 10–30 (typ.)  ·  ~{TYPICAL_FLOOR_SIDE_FT:.0f} ft plate  ·  curtain-wall perimeter",
            fontsize=8.5, color=MUTED)

    ox, oy = 2.4, 2.0
    s = 0.02
    w, h = BASE_WIDTH_FT * s * 0.92, BASE_LENGTH_FT * s * 0.88
    ax.add_patch(Rectangle((ox, oy), h, w, fill=False, ec=INK, lw=2.2))
    core_w, core_h = h * 0.22, w * 0.28
    cx, cy = ox + (h - core_h) / 2, oy + (w - core_w) / 2
    ax.add_patch(Rectangle((cx, cy), core_h, core_w, fill=True, facecolor=GRID, edgecolor=INK, lw=1.2))
    ax.text(cx + core_h / 2, cy + core_w / 2, "CORE\nELEV.\nSTAIRS\nMEP",
            ha="center", va="center", fontsize=6.5, color=MUTED)

    # Perimeter mullion grid (intricate curtain wall rhythm)
    mullion_x = np.linspace(ox + 0.08, ox + h - 0.08, 14)
    mullion_y = np.linspace(oy + 0.08, oy + w - 0.08, 9)
    for mx in mullion_x:
        ax.plot([mx, mx], [oy + 0.05, oy + w - 0.05], color=GLASS, lw=0.35)
    for my in mullion_y:
        ax.plot([ox + 0.05, ox + h - 0.05], [my, my], color=GLASS, lw=0.35)

    # Office bays
    for i in range(3):
        for j in range(2):
            rx = ox + 0.35 + i * (h * 0.28)
            ry = oy + 0.35 + j * (w * 0.38)
            if rx + h * 0.22 < cx or rx > cx + core_h:
                ax.add_patch(Rectangle((rx, ry), h * 0.2, w * 0.3, fill=False, ec=MUTED, lw=0.5))

    ax.text(ox + h / 2, oy + w + 0.35, "TOP VIEW — TYPICAL FLOOR", ha="center", fontsize=9, color=INK)
    draw_title_block(ax, 7.8, 0.5, 3.8, 2.4, "A2.0")
    plt.savefig(ROOT / "frost_floor_plan.png", dpi=220, bbox_inches="tight", facecolor=BG, pad_inches=0.25)
    plt.close()


def render_north_elevation() -> None:
    fig, ax = plt.subplots(figsize=(12, 14), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 16)
    ax.axis("off")
    ax.set_aspect("equal")

    ax.text(0.4, 15.2, "Frost Bank Tower — North Elevation", fontsize=16, color=INK, fontweight="light")
    ax.text(0.4, 14.75, f"Total {TOTAL_HEIGHT_FT}'-0\"  ·  Roof {ROOF_HEIGHT_FT}'-0\"  ·  Crown {CROWN_HEIGHT_FT}'-0\"",
            fontsize=8.5, color=MUTED)

    ox, oy = 3.0, 1.0
    s = 0.018

    # Podium limestone
    pod_h = PODIUM_HEIGHT_FT * s
    pod_w = BASE_LENGTH_FT * s
    ax.add_patch(Rectangle((ox, oy), pod_w, pod_h, fill=True, facecolor=LIMESTONE, edgecolor=INK, lw=2))

    # Glass tower with floor lines
    tower_h = (ROOF_HEIGHT_FT - PODIUM_HEIGHT_FT) * s
    ax.add_patch(Rectangle((ox + pod_w * 0.04, oy + pod_h), pod_w * 0.92, tower_h,
                            fill=True, facecolor=GLASS, edgecolor=INK, lw=2, alpha=0.55))
    for i in range(1, FLOOR_COUNT - PODIUM_FLOORS):
        fy = oy + pod_h + tower_h * i / (FLOOR_COUNT - PODIUM_FLOORS)
        ax.plot([ox + pod_w * 0.04, ox + pod_w * 0.96], [fy, fy], color="#7A8FA0", lw=0.25)

    # Crown setbacks — intricate folded geometry
    crown_pts = []
    for elev, length, _width in CROWN_SETBACKS_FT:
        y = oy + elev * s
        half = length * s / 2
        cx = ox + pod_w / 2
        crown_pts.append([cx - half, y])
    crown_pts.append([ox + pod_w / 2 + CROWN_TOP_SIDE_FT * s / 2, oy + TOTAL_HEIGHT_FT * s])
    crown_pts.append([ox + pod_w / 2 - CROWN_TOP_SIDE_FT * s / 2, oy + TOTAL_HEIGHT_FT * s])
    for elev, length, _ in reversed(CROWN_SETBACKS_FT):
        y = oy + elev * s
        half = length * s / 2
        cx = ox + pod_w / 2
        crown_pts.append([cx + half, y])

    ax.add_patch(Polygon(crown_pts, closed=True, fill=True, facecolor=CROWN_LITE,
                         edgecolor=INK, lw=1.8, alpha=0.75))

    # Crown facet lines
    for elev, length, _ in CROWN_SETBACKS_FT[1:-1]:
        y = oy + elev * s
        half = length * s / 2
        cx = ox + pod_w / 2
        ax.plot([cx - half, cx + half], [y, y], color=INK, lw=0.6)

    # Dimensions
    ax.annotate("", xy=(ox - 0.35, oy), xytext=(ox - 0.35, oy + TOTAL_HEIGHT_FT * s),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    ax.text(ox - 0.55, oy + TOTAL_HEIGHT_FT * s / 2, f"{TOTAL_HEIGHT_FT}'-0\"",
            rotation=90, va="center", ha="center", fontsize=8, color=INK)
    ax.annotate("", xy=(ox, oy - 0.25), xytext=(ox + pod_w, oy - 0.25),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    ax.text(ox + pod_w / 2, oy - 0.45, f"{BASE_LENGTH_FT}'-0\"", ha="center", fontsize=8, color=INK)

    ax.text(ox + pod_w + 0.3, oy + ROOF_HEIGHT_FT * s, "ROOF", fontsize=7, color=MUTED)
    ax.text(ox + pod_w + 0.3, oy + TOTAL_HEIGHT_FT * s - 0.1, "CROWN", fontsize=7, color=MUTED)

    ax.text(0.4, 0.55, "NOTE: Crown setback dimensions EST. from published imagery. "
            "Verify against Duda/Paine drawings for construction accuracy.",
            fontsize=7, color=MUTED, wrap=True)

    draw_title_block(ax, 7.6, 0.4, 3.9, 2.5, "A3.0")
    plt.savefig(ROOT / "frost_north_elevation.png", dpi=220, bbox_inches="tight", facecolor=BG, pad_inches=0.25)
    plt.close()


def build_massing_3d() -> trimesh.Trimesh:
    """3D massing model from setback schedule."""
    parts = []
    s = 0.3048  # feet to meters for GLB

    def box_at(length, width, height, z0, cx=0, cy=0):
        mesh = trimesh.creation.box(extents=[length * s, width * s, height * s])
        mesh.apply_translation([cx * s, cy * s, (z0 + height / 2) * s])
        return mesh

    # Podium
    parts.append(box_at(BASE_LENGTH_FT, BASE_WIDTH_FT, PODIUM_HEIGHT_FT, 0))

    z = PODIUM_HEIGHT_FT
    schedule = [(ROOF_HEIGHT_FT, BASE_LENGTH_FT, BASE_WIDTH_FT)] + list(CROWN_SETBACKS_FT[1:])
    prev_l, prev_w = BASE_LENGTH_FT, BASE_WIDTH_FT
    prev_z = PODIUM_HEIGHT_FT

    for elev, length, width in schedule:
        h = elev - prev_z
        if h > 0:
            parts.append(box_at(prev_l, prev_w, h, prev_z))
        prev_l, prev_w, prev_z = length, width, elev

    # Final crown cap
    h = TOTAL_HEIGHT_FT - prev_z
    if h > 0:
        parts.append(box_at(prev_l, prev_w, h, prev_z))

    return trimesh.util.concatenate(parts)


def main():
    render_site_plan()
    render_typical_floor()
    render_north_elevation()
    mesh = build_massing_3d()
    mesh.export(ROOT / "frost_tower_massing.glb")
    mesh.export(ROOT / "frost_tower_massing.stl")
    print("Frost Bank Tower study generated.")
    print("  frost_site_plan.png")
    print("  frost_floor_plan.png")
    print("  frost_north_elevation.png")
    print("  frost_tower_massing.glb")


if __name__ == "__main__":
    main()