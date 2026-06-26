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
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from frost_tower_dimensions import (
    BASE_LENGTH_FT,
    BASE_WIDTH_FT,
    CROWN_HEIGHT_FT,
    CROWN_INFILL_THICKNESS_FT,
    CROWN_SETBACKS_FT,
    CROWN_TOP_SIDE_FT,
    CURTAIN_WALL_THICKNESS_FT,
    FLOOR_COUNT,
    GLASS_SHAFT_INSET_FT,
    PALETTE_BLUE_GREY,
    PALETTE_CHERRY_BLOSSOM,
    PALETTE_MORNING_BUTTER,
    PALETTE_SOFT_LINEN,
    PARKING_LEVELS,
    PARKING_STRATA_COUNT,
    PARKING_STRATA_DEPTH_FT,
    PODIUM_FLOORS,
    PODIUM_HEIGHT_FT,
    ROOF_HEIGHT_FT,
    SITE_ADDRESS,
    SITE_SQFT,
    TOTAL_HEIGHT_FT,
    TOWER_SHAFT_TAPER,
    TYPICAL_FLOOR_SIDE_FT,
)

ROOT = Path(__file__).resolve().parent
BG = "#FAF9F6"
INK = "#2A2A2A"
MUTED = "#6E6A65"
GRID = "#D8D2C8"
GLASS = PALETTE_BLUE_GREY
LIMESTONE = PALETTE_SOFT_LINEN
CROWN_LITE = PALETTE_MORNING_BUTTER
CORE_FILL = PALETTE_CHERRY_BLOSSOM

FT_TO_M = 0.3048
IN_PER_FT = 1 / 64  # 1/64" = 1'-0" — single scale for every orthographic view
SHEET_W, SHEET_H = 24.0, 18.0
HATCH = "#C5C0B8"


def _hex_rgba(hex_color: str, alpha: int = 255) -> list[int]:
    h = hex_color.lstrip("#")
    return [int(h[i : i + 2], 16) for i in (0, 2, 4)] + [alpha]


# 346eur layer mapping — see methodology.html for program assignments
LAYER_GLASS = _hex_rgba(PALETTE_BLUE_GREY)
LAYER_SITE = _hex_rgba(PALETTE_SOFT_LINEN)
LAYER_CORE = _hex_rgba(PALETTE_CHERRY_BLOSSOM)
LAYER_CROWN = _hex_rgba(PALETTE_MORNING_BUTTER)


def ft_to_draw(ft: float, scale_px_per_ft: float = 0.012) -> float:
    return ft * scale_px_per_ft


def _s(ft: float) -> float:
    """Feet → inches on sheet at 1/64 scale."""
    return ft * IN_PER_FT


def _view_frame(ax, x: float, y: float, w: float, h: float, label: str) -> None:
    ax.add_patch(Rectangle((x, y), w, h, fill=False, ec=INK, lw=0.9))
    ax.plot([x, x + w], [y, y], color=INK, lw=1.2)
    ax.text(x + w / 2, y - 0.22, label, ha="center", va="top", fontsize=7.5,
            color=INK, fontweight="light")


def _centerline(ax, x0: float, y0: float, x1: float, y1: float) -> None:
    ax.plot([x0, x1], [y0, y1], color=MUTED, lw=0.45, ls=(0, (6, 3, 1, 3)))


def _dim_v(ax, x: float, y0: float, y1: float, text: str, offset: float = 0.35) -> None:
    ax.plot([x, x - offset], [y0, y0], color=INK, lw=0.35)
    ax.plot([x, x - offset], [y1, y1], color=INK, lw=0.35)
    ax.annotate("", xy=(x - offset, y0), xytext=(x - offset, y1),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.7, mutation_scale=8))
    ax.text(x - offset - 0.12, (y0 + y1) / 2, text, rotation=90, va="center", ha="center",
            fontsize=6.5, color=INK)


def _dim_h(ax, x0: float, x1: float, y: float, text: str, offset: float = 0.28) -> None:
    ax.plot([x0, x0], [y, y - offset], color=INK, lw=0.35)
    ax.plot([x1, x1], [y, y - offset], color=INK, lw=0.35)
    ax.annotate("", xy=(x0, y - offset), xytext=(x1, y - offset),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.7, mutation_scale=8))
    ax.text((x0 + x1) / 2, y - offset - 0.15, text, ha="center", va="top", fontsize=6.5, color=INK)


def _crown_step_bands() -> list[tuple[float, float, float, float]]:
    """Discrete horizontal crown tiers — (z0, z1, north_length, east_width)."""
    bands: list[tuple[float, float, float, float]] = []
    prev_z = CROWN_SETBACKS_FT[0][0]
    for elev, length, width in CROWN_SETBACKS_FT[1:]:
        if elev > prev_z:
            bands.append((prev_z, elev, length, width))
        prev_z = elev
    return bands


def _tower_glass_width_ft() -> float:
    return BASE_LENGTH_FT - 2 * GLASS_SHAFT_INSET_FT


def _core_size_ft() -> tuple[float, float]:
    return BASE_LENGTH_FT * 0.22, BASE_WIDTH_FT * 0.28


def draw_north_elevation_geom(ax, ox: float, oy: float) -> tuple[float, float, float, float]:
    """Return (x0, y0, width, height) bounds in sheet inches."""
    pod_w = _s(BASE_LENGTH_FT)
    pod_h = _s(PODIUM_HEIGHT_FT)
    ax.add_patch(Rectangle((ox, oy), pod_w, pod_h, facecolor=LIMESTONE, edgecolor=INK, lw=1.1))

    glass_w = _s(_tower_glass_width_ft())
    glass_x = ox + (pod_w - glass_w) / 2
    tower_h = _s(ROOF_HEIGHT_FT - PODIUM_HEIGHT_FT)
    ax.add_patch(Rectangle((glass_x, oy + pod_h), glass_w, tower_h,
                            facecolor=GLASS, edgecolor=INK, lw=1.1, alpha=0.85))
    floors = FLOOR_COUNT - PODIUM_FLOORS
    for i in range(1, floors):
        fy = oy + pod_h + tower_h * i / floors
        ax.plot([glass_x, glass_x + glass_w], [fy, fy], color="#5A7A9A", lw=0.22)

    cx = ox + pod_w / 2
    for z0, z1, length, _width in _crown_step_bands():
        band_h = _s(z1 - z0)
        band_y = oy + _s(z0)
        band_w = _s(length)
        x0 = cx - band_w / 2
        ax.add_patch(Rectangle((x0, band_y), band_w, band_h,
                                facecolor=CROWN_LITE, edgecolor=INK, lw=0.75))
        ax.plot([x0, x0 + band_w], [band_y + band_h, band_y + band_h], color=INK, lw=0.5)

    total_h = _s(TOTAL_HEIGHT_FT)
    _centerline(ax, cx, oy - 0.15, cx, oy + total_h + 0.15)
    _dim_v(ax, ox, oy, oy + total_h, f"{TOTAL_HEIGHT_FT}'-0\"")
    _dim_h(ax, ox, ox + pod_w, oy, f"{BASE_LENGTH_FT}'-0\"")
    _dim_v(ax, ox + pod_w + 0.55, oy + _s(ROOF_HEIGHT_FT), oy + total_h,
           f"{CROWN_HEIGHT_FT}'-0\"", offset=0.2)
    ax.text(ox + pod_w + 0.7, oy + _s(ROOF_HEIGHT_FT) + 0.08, "ROOF", fontsize=5.5, color=MUTED)
    ax.text(ox + pod_w + 0.7, oy + total_h - 0.1, "CROWN", fontsize=5.5, color=MUTED)
    return ox, oy, pod_w, total_h


def draw_section_a_geom(ax, ox: float, oy: float) -> None:
    """Section A–A through crown centerline — hatched cut surfaces."""
    total_h = _s(TOTAL_HEIGHT_FT)
    half_w = _s(BASE_WIDTH_FT) / 2
    cx = ox + half_w

    ax.add_patch(Rectangle((ox, oy), _s(BASE_WIDTH_FT), _s(PODIUM_HEIGHT_FT),
                            facecolor=LIMESTONE, edgecolor=INK, lw=1.0, hatch="///", alpha=0.9))
    core_w, _ = _core_size_ft()
    core_hw = _s(core_w) / 2
    ax.add_patch(Rectangle((cx - core_hw, oy), _s(core_w), _s(ROOF_HEIGHT_FT),
                            facecolor=CORE_FILL, edgecolor=INK, lw=0.9, hatch="xx", alpha=0.75))

    glass_hw = _s(BASE_WIDTH_FT - 2 * GLASS_SHAFT_INSET_FT) / 2
    ax.add_patch(Rectangle((cx - glass_hw, oy + _s(PODIUM_HEIGHT_FT)),
                            _s(BASE_WIDTH_FT - 2 * GLASS_SHAFT_INSET_FT),
                            _s(ROOF_HEIGHT_FT - PODIUM_HEIGHT_FT),
                            facecolor=GLASS, edgecolor=INK, lw=0.9, alpha=0.55))

    for z0, z1, _length, width in _crown_step_bands():
        tier_w = _s(width)
        x0 = cx - tier_w / 2
        ax.add_patch(Rectangle((x0, oy + _s(z0)), tier_w, _s(z1 - z0),
                                facecolor=CROWN_LITE, edgecolor=INK, lw=0.6, hatch=".."))

    _centerline(ax, cx, oy - 0.1, cx, oy + total_h + 0.1)
    ax.plot([ox - 0.35, ox + _s(BASE_WIDTH_FT) + 0.35],
            [oy + _s(ROOF_HEIGHT_FT), oy + _s(ROOF_HEIGHT_FT)], color=MUTED, lw=0.5, ls="--")
    ax.text(ox - 0.3, oy + _s(ROOF_HEIGHT_FT) + 0.08, "A", fontsize=7, color=INK, fontweight="bold")
    ax.text(ox + _s(BASE_WIDTH_FT) + 0.15, oy + _s(ROOF_HEIGHT_FT) + 0.08, "A", fontsize=7, color=INK)
    _dim_v(ax, ox + _s(BASE_WIDTH_FT), oy, oy + total_h, f"{TOTAL_HEIGHT_FT}'-0\"", offset=0.25)


def draw_site_plan_geom(ax, ox: float, oy: float) -> None:
    site_l = _s(280)
    site_w = _s(220)
    ax.add_patch(Rectangle((ox, oy), site_l, site_w, fill=False, ec=GRID, lw=0.9, ls=(0, (5, 4))))
    ax.text(ox + site_l / 2, oy - 0.2, "SITE BOUNDARY (EST.)", ha="center", fontsize=5.5, color=MUTED)

    bl, bw = _s(BASE_LENGTH_FT), _s(BASE_WIDTH_FT)
    bx = ox + (site_l - bl) / 2
    by = oy + (site_w - bw) / 2
    ax.add_patch(Rectangle((bx, by), bl, bw, facecolor=LIMESTONE, edgecolor=INK, lw=1.1))
    ax.add_patch(Rectangle((bx + _s(GLASS_SHAFT_INSET_FT), by + _s(GLASS_SHAFT_INSET_FT)),
                            _s(_tower_glass_width_ft()), _s(BASE_WIDTH_FT - 2 * GLASS_SHAFT_INSET_FT),
                            fill=False, ec=GLASS, lw=0.9))
    park_w = bl * 0.38
    ax.add_patch(Rectangle((bx + _s(4), by + _s(4)), park_w, bw - _s(8),
                            fill=False, ec=MUTED, lw=0.6, ls=(0, (4, 3))))
    ax.text(bx + park_w / 2 + _s(4), by + bw / 2, f"PARKING\n{PARKING_LEVELS} LVLS",
            ha="center", va="center", fontsize=5, color=MUTED)
    ax.plot([ox - 0.2, ox + site_l + 0.2], [oy - 0.45, oy - 0.45], color=INK, lw=1.0)
    ax.text(ox + site_l / 2, oy - 0.62, "CONGRESS AVENUE", ha="center", fontsize=6, color=INK)
    _dim_h(ax, bx, bx + bl, by + bw, f"{BASE_LENGTH_FT}'-0\"")
    _dim_v(ax, bx, by, by + bw, f"{BASE_WIDTH_FT}'-0\"", offset=0.22)


def draw_floor_plan_geom(ax, ox: float, oy: float) -> None:
    plate_l, plate_w = _s(BASE_LENGTH_FT), _s(BASE_WIDTH_FT)
    ax.add_patch(Rectangle((ox, oy), plate_l, plate_w, fill=False, edgecolor=INK, lw=1.2))
    core_l, core_w = _s(_core_size_ft()[0]), _s(_core_size_ft()[1])
    cx = ox + (plate_l - core_l) / 2
    cy = oy + (plate_w - core_w) / 2
    ax.add_patch(Rectangle((cx, cy), core_l, core_w, facecolor=CORE_FILL, edgecolor=INK, lw=0.9))
    ax.text(cx + core_l / 2, cy + core_w / 2, "CORE\nELEV.\nSTAIRS\nMEP",
            ha="center", va="center", fontsize=5.5, color=MUTED)

    mullion_x = np.linspace(ox + _s(3), ox + plate_l - _s(3), 14)
    mullion_y = np.linspace(oy + _s(3), oy + plate_w - _s(3), 9)
    for mx in mullion_x:
        ax.plot([mx, mx], [oy + _s(2), oy + plate_w - _s(2)], color=GLASS, lw=0.28)
    for my in mullion_y:
        ax.plot([ox + _s(2), ox + plate_l - _s(2)], [my, my], color=GLASS, lw=0.28)

    _centerline(ax, ox + plate_l / 2, oy - 0.1, ox + plate_l / 2, oy + plate_w + 0.1)
    _centerline(ax, ox - 0.1, oy + plate_w / 2, ox + plate_l + 0.1, oy + plate_w / 2)
    _dim_h(ax, ox, ox + plate_l, oy + plate_w, f"{BASE_LENGTH_FT}'-0\"")
    _dim_v(ax, ox + plate_l, oy, oy + plate_w, f"{BASE_WIDTH_FT}'-0\"", offset=0.22)


def draw_isometric_geom(ax) -> None:
    """Third-angle isometric massing derived from the same dimensions as orthographic views."""
    ax.set_facecolor(BG)
    ax.axis("off")

    def _box_faces(x, y, z, w, h, d, color, alpha=0.92):
        verts = np.array([
            [x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z],
            [x, y, z + d], [x + w, y, z + d], [x + w, y + h, z + d], [x, y + h, z + d],
        ], dtype=float)
        faces = [
            [verts[j] for j in (0, 1, 2, 3)], [verts[j] for j in (4, 5, 6, 7)],
            [verts[j] for j in (0, 1, 5, 4)], [verts[j] for j in (2, 3, 7, 6)],
            [verts[j] for j in (1, 2, 6, 5)], [verts[j] for j in (0, 3, 7, 4)],
        ]
        col = Poly3DCollection(faces, alpha=alpha, linewidths=0.25, edgecolors=INK)
        col.set_facecolor(color)
        ax.add_collection3d(col)

    s = 0.011
    ox, oy, oz = -1.0, -0.4, 0.0
    _box_faces(ox, oy, oz, BASE_LENGTH_FT * s, BASE_WIDTH_FT * s, PODIUM_HEIGHT_FT * s, LIMESTONE)
    gi = GLASS_SHAFT_INSET_FT
    _box_faces(ox + gi * s, oy + gi * s, oz + PODIUM_HEIGHT_FT * s,
               _tower_glass_width_ft() * s, (BASE_WIDTH_FT - 2 * gi) * s,
               (ROOF_HEIGHT_FT - PODIUM_HEIGHT_FT) * s, GLASS, alpha=0.8)
    cl, cw = _core_size_ft()
    _box_faces(ox + (BASE_LENGTH_FT - cl) / 2 * s, oy + (BASE_WIDTH_FT - cw) / 2 * s, oz,
               cl * s, cw * s, ROOF_HEIGHT_FT * s, CORE_FILL, alpha=0.7)
    for z0, z1, length, width in _crown_step_bands():
        band_h = (z1 - z0) * s
        band_x = ox + (BASE_LENGTH_FT - length) / 2 * s
        band_y = oy + (BASE_WIDTH_FT - width) / 2 * s
        _box_faces(band_x, band_y, oz + z0 * s, length * s, width * s, band_h, CROWN_LITE)

    ax.view_init(elev=22, azim=-52)
    ax.set_xlim(-2, 4)
    ax.set_ylim(-1, 3)
    ax.set_zlim(0, 5.5)
    ax.set_box_aspect((2.2, 1.2, 2.8))


def draw_sheet_title_block(ax, x: float, y: float, w: float, h: float, sheet: str = "A0.0") -> None:
    cols = [x + w * i / 6 for i in range(7)]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", fill=False, ec=INK, lw=1.2))
    for i in range(1, 6):
        ax.plot([cols[i], cols[i]], [y, y + h], color=INK, lw=0.45)
    title_h = h * 0.28
    ax.plot([x, x + w], [y + h - title_h, y + h - title_h], color=INK, lw=0.55)
    ax.text(cols[0] + 0.1, y + h - 0.18, "TITLE", fontsize=5.5, color=MUTED)
    ax.text(cols[0] + 0.1, y + h - 0.48, "Frost Bank Tower — Architectural CAD Study",
            fontsize=8.5, color=INK, fontweight="light")
    ax.text(cols[3] + 0.1, y + h - 0.18, "DWG NO.", fontsize=5.5, color=MUTED)
    ax.text(cols[3] + 0.1, y + h - 0.48, sheet, fontsize=8, color=INK)
    rows = [
        ("LOCATION", SITE_ADDRESS, "SCALE", '1/64"=1\'-0"', "REV", "B"),
        ("ARCHITECT", "Duda/Paine + HKS", "HEIGHT", f"{TOTAL_HEIGHT_FT}'-0\"", "FLOORS", str(FLOOR_COUNT)),
        ("PROJECTION", "Third Angle", "ROOF", f"{ROOF_HEIGHT_FT}'-0\"", "STATUS", "STUDY"),
        ("AUTHOR", "Kristen Fenwick", "CROWN", f"{CROWN_HEIGHT_FT}'-0\"", "CLASS", "AEC"),
        ("PALETTE", "346eur / CFD", "UNITS", "feet", "SHEET", "1 of 1"),
    ]
    row_h = (h - title_h) / len(rows)
    for i, (a, b, c, d, e, f) in enumerate(rows):
        ry = y + h - title_h - (i + 0.55) * row_h
        ax.plot([x, x + w], [y + h - title_h - i * row_h, y + h - title_h - i * row_h],
                color=INK, lw=0.3)
        ax.text(cols[0] + 0.08, ry, a, fontsize=5, color=MUTED, va="center")
        ax.text(cols[1] + 0.08, ry, b, fontsize=5.8, color=INK, va="center")
        ax.text(cols[2] + 0.08, ry, c, fontsize=5, color=MUTED, va="center")
        ax.text(cols[3] + 0.08, ry, d, fontsize=5.8, color=INK, va="center")
        ax.text(cols[4] + 0.08, ry, e, fontsize=5, color=MUTED, va="center")
        ax.text(cols[5] - 0.08, ry, f, fontsize=5.8, color=INK, va="center", ha="right")
    ax.text(x + 0.12, y + 0.12,
            "PROJECTION · THIRD ANGLE · ORTHOGRAPHIC + ISOMETRIC · PARAMETRIC MASSING",
            fontsize=5.2, color=MUTED)


def render_drawing_sheet() -> None:
    """Unified multi-view sheet — aligned orthographic projections at one scale."""
    fig = plt.figure(figsize=(SHEET_W, SHEET_H), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, SHEET_W)
    ax.set_ylim(0, SHEET_H)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(Rectangle((0.35, 0.35), SHEET_W - 0.7, SHEET_H - 0.7, fill=False, ec=INK, lw=1.6))
    ax.text(SHEET_W / 2, SHEET_H - 0.55, "FROST BANK TOWER — ARCHITECTURAL CAD STUDY",
            ha="center", fontsize=11, color=INK, fontweight="light")

    elev_x, elev_y = 1.0, 3.2
    elev_w, elev_h = 4.2, 9.2
    _view_frame(ax, elev_x - 0.35, elev_y - 0.45, elev_w, elev_h, "NORTH ELEVATION · SCALE 1/64\"=1'-0\"")
    draw_north_elevation_geom(ax, elev_x, elev_y)

    sec_x, sec_y = 6.0, 3.2
    sec_w, sec_h = 3.4, 9.2
    _view_frame(ax, sec_x - 0.3, sec_y - 0.45, sec_w, sec_h, "SECTION A–A · LOOKING EAST")
    draw_section_a_geom(ax, sec_x, sec_y)

    site_x, site_y = 10.2, 9.0
    site_w, site_h = 4.8, 3.2
    _view_frame(ax, site_x - 0.25, site_y - 0.35, site_w, site_h, "SITE PLAN STUDY")
    draw_site_plan_geom(ax, site_x, site_y)

    plan_x, plan_y = 10.2, 3.2
    plan_w, plan_h = 4.8, 5.2
    _view_frame(ax, plan_x - 0.25, plan_y - 0.35, plan_w, plan_h,
                f"TYPICAL OFFICE FLOOR · FLOORS 10–30 · ~{TYPICAL_FLOOR_SIDE_FT:.0f} FT PLATE")
    draw_floor_plan_geom(ax, plan_x, plan_y)

    iso_ax = fig.add_axes([0.62, 0.14, 0.34, 0.38], projection="3d")
    _view_frame(ax, 15.4, 3.0, 7.8, 9.0, "ISOMETRIC MASSING · 3D REFERENCE")
    draw_isometric_geom(iso_ax)

    notes = [
        "NOTES:",
        "1. ALL ORTHOGRAPHIC VIEWS AT UNIFORM SCALE 1/64\"=1'-0\".",
        "2. CROWN SETBACKS & FOOTPRINT DIMENSIONS EST. — VERIFY WITH AOR DRAWINGS.",
        "3. COLORS: BLUE GREY #7298C7 ENVELOPE · SOFT LINEN #F5F1E6 PODIUM ·",
        "   MORNING BUTTER #F3D98F CROWN · CHERRY BLOSSOM #F5A8A8 CORE (346EUR / CFD).",
        "4. SECTION HATCHING INDICATES CUT MASS ONLY — NOT MATERIAL SPECIFICATION.",
    ]
    for i, line in enumerate(notes):
        ax.text(0.9, 2.55 - i * 0.28, line, fontsize=5.5, color=MUTED if i else INK,
                fontweight="light" if i == 0 else "normal")

    draw_sheet_title_block(ax, 9.5, 0.55, 14.0, 2.35, "KF-FT-001")
    fig.savefig(ROOT / "frost_drawing_sheet.png", dpi=200, facecolor=BG, pad_inches=0.15)
    plt.close(fig)


def _render_single_view(filename: str, title: str, subtitle: str, sheet: str,
                        draw_fn, frame_w: float, frame_h: float, margin: float = 1.2) -> None:
    """Export individual views using the same geometry helpers as the master sheet."""
    fig_w = frame_w + margin * 2 + 4.5
    fig_h = frame_h + margin * 2 + 2.8
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(margin, fig_h - 0.55, title, fontsize=14, color=INK, fontweight="light")
    ax.text(margin, fig_h - 0.95, subtitle, fontsize=8, color=MUTED)
    ox, oy = margin, margin
    draw_fn(ax, ox, oy)
    draw_sheet_title_block(ax, fig_w - 4.3, 0.45, 4.0, 2.1, sheet)
    plt.savefig(ROOT / filename, dpi=220, facecolor=BG, pad_inches=0.2)
    plt.close()


def render_site_plan() -> None:
    _render_single_view(
        "frost_site_plan.png",
        "Frost Bank Tower — Site Plan Study",
        f"{SITE_ADDRESS}  ·  Block 42  ·  {SITE_SQFT:,.0f} sf site  ·  Scale 1/64\"=1'-0\"",
        "A1.0",
        draw_site_plan_geom,
        _s(280) + 0.8,
        _s(220) + 1.0,
    )


def render_typical_floor() -> None:
    _render_single_view(
        "frost_floor_plan.png",
        "Frost Bank Tower — Typical Office Floor Plan",
        f"Floor 10–30 (typ.)  ·  {BASE_LENGTH_FT}′×{BASE_WIDTH_FT}′ plate  ·  curtain-wall perimeter",
        "A2.0",
        draw_floor_plan_geom,
        _s(BASE_LENGTH_FT) + 0.8,
        _s(BASE_WIDTH_FT) + 0.8,
    )


def render_north_elevation() -> None:
    _render_single_view(
        "frost_north_elevation.png",
        "Frost Bank Tower — North Elevation",
        f"Total {TOTAL_HEIGHT_FT}'-0\"  ·  Roof {ROOF_HEIGHT_FT}'-0\"  ·  Crown {CROWN_HEIGHT_FT}'-0\"",
        "A3.0",
        draw_north_elevation_geom,
        _s(BASE_LENGTH_FT) + 1.2,
        _s(TOTAL_HEIGHT_FT) + 0.8,
    )


def _paint(mesh: trimesh.Trimesh, rgba: list[int]) -> trimesh.Trimesh:
    mesh.visual.face_colors = np.tile(rgba, (len(mesh.faces), 1))
    return mesh


def _box_ft(length: float, width: float, height: float, z0: float,
            cx: float = 0.0, cy: float = 0.0) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=[length * FT_TO_M, width * FT_TO_M, height * FT_TO_M])
    mesh.apply_translation([cx * FT_TO_M, cy * FT_TO_M, (z0 + height / 2) * FT_TO_M])
    return mesh


def _quad_ft(v0, v1, v2, v3, rgba: list[int]) -> trimesh.Trimesh:
    verts = np.array([v0, v1, v2, v3], dtype=float) * FT_TO_M
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    return _paint(trimesh.Trimesh(vertices=verts, faces=faces), rgba)


def _folded_step(lo: float, wo: float, li: float, wi: float,
                 z0: float, z1: float, rgba: list[int]) -> list[trimesh.Trimesh]:
    """Four inclined facade folds plus corner chamfers between two setback tiers."""
    folds = []
    # North (+Y)
    folds.append(_quad_ft(
        (-lo / 2, wo / 2, z0), (lo / 2, wo / 2, z0),
        (li / 2, wi / 2, z1), (-li / 2, wi / 2, z1), rgba))
    # South (-Y)
    folds.append(_quad_ft(
        (lo / 2, -wo / 2, z0), (-lo / 2, -wo / 2, z0),
        (-li / 2, -wi / 2, z1), (li / 2, -wi / 2, z1), rgba))
    # East (+X)
    folds.append(_quad_ft(
        (lo / 2, -wo / 2, z0), (lo / 2, wo / 2, z0),
        (li / 2, wi / 2, z1), (li / 2, -wi / 2, z1), rgba))
    # West (-X)
    folds.append(_quad_ft(
        (-lo / 2, wo / 2, z0), (-lo / 2, -wo / 2, z0),
        (-li / 2, -wi / 2, z1), (-li / 2, wi / 2, z1), rgba))
    # Corner chamfers (folded-plane rhythm from reference sketch)
    folds.append(_quad_ft(
        (lo / 2, wo / 2, z0), (lo / 2, wi / 2, z1),
        (li / 2, wi / 2, z1), (li / 2, wo / 2, z1), rgba))
    folds.append(_quad_ft(
        (-lo / 2, wo / 2, z0), (-li / 2, wo / 2, z1),
        (-li / 2, wi / 2, z1), (-lo / 2, wi / 2, z1), rgba))
    folds.append(_quad_ft(
        (lo / 2, -wo / 2, z0), (li / 2, -wo / 2, z1),
        (li / 2, -wi / 2, z1), (lo / 2, -wi / 2, z1), rgba))
    folds.append(_quad_ft(
        (-lo / 2, -wo / 2, z0), (-lo / 2, -wi / 2, z1),
        (-li / 2, -wi / 2, z1), (-li / 2, -wo / 2, z1), rgba))
    return folds


def _crown_infill_slab(length: float, width: float, z: float) -> trimesh.Trimesh:
    t = CROWN_INFILL_THICKNESS_FT
    return _paint(_box_ft(length, width, t, z - t), LAYER_CORE)


def _hollow_curtain_wall(length: float, width: float, height: float, z0: float) -> trimesh.Trimesh:
    """Thin-walled envelope — represents curtain wall depth, not solid infill."""
    wall = CURTAIN_WALL_THICKNESS_FT
    outer = _box_ft(length, width, height, z0)
    inner_l = length - 2 * wall
    inner_w = width - 2 * wall
    inner_h = max(height - wall, wall)
    if inner_l <= wall or inner_w <= wall:
        return _paint(outer, LAYER_GLASS)
    inner = _box_ft(inner_l, inner_w, inner_h, z0 + wall * 0.5)
    try:
        shell = outer.difference(inner)
        if shell is not None and len(shell.faces) > 0:
            return _paint(shell, LAYER_GLASS)
    except Exception:
        pass
    return _paint(outer, LAYER_GLASS)


def _parking_strata() -> list[tuple[str, trimesh.Trimesh]]:
    """Horizontal subsurface layers within footprint — no protruding volumes."""
    layers: list[tuple[str, trimesh.Trimesh]] = []
    layer_h = PARKING_STRATA_DEPTH_FT / PARKING_STRATA_COUNT
    for i in range(PARKING_STRATA_COUNT):
        inset = i * 2.0
        length = BASE_LENGTH_FT * 0.94 - inset
        width = BASE_WIDTH_FT * 0.94 - inset
        z0 = -PARKING_STRATA_DEPTH_FT + i * layer_h
        slab_h = layer_h * 0.82
        mesh = _paint(_box_ft(length, width, slab_h, z0), LAYER_CORE)
        layers.append((f"parking_stratum_{i + 1}", mesh))
    return layers


def build_massing_3d() -> trimesh.Scene:
    """Layered massing with folded crown facets and color-coded program volumes."""
    scene = trimesh.Scene()
    meshes: list[tuple[str, trimesh.Trimesh]] = []

    def add(name: str, mesh: trimesh.Trimesh) -> None:
        meshes.append((name, mesh))

    tower_l = BASE_LENGTH_FT - GLASS_SHAFT_INSET_FT
    tower_w = BASE_WIDTH_FT - GLASS_SHAFT_INSET_FT
    core_l = BASE_LENGTH_FT * 0.22
    core_w = BASE_WIDTH_FT * 0.28

    # Site pad (Soft Linen) — symmetric, no offset protrusions
    add("site_pad", _paint(
        _box_ft(BASE_LENGTH_FT + 14, BASE_WIDTH_FT + 10, 6, -6), LAYER_SITE))

    # Parking strata: horizontal layers inside footprint (Cherry Blossom)
    for name, mesh in _parking_strata():
        add(name, mesh)

    # Limestone podium (Soft Linen)
    add("podium", _paint(_box_ft(BASE_LENGTH_FT, BASE_WIDTH_FT, PODIUM_HEIGHT_FT, 0), LAYER_SITE))

    # Vertical core — podium through roof only, centered (Cherry Blossom)
    add("core", _paint(_box_ft(core_l, core_w, ROOF_HEIGHT_FT, 0), LAYER_CORE))

    # Hollow curtain-wall shaft with controlled taper (Blue Grey)
    shaft_segments = 6
    shaft_h = ROOF_HEIGHT_FT - PODIUM_HEIGHT_FT
    for i in range(shaft_segments):
        t0 = i / shaft_segments
        seg_l = tower_l * (1 - (1 - TOWER_SHAFT_TAPER) * t0)
        seg_w = tower_w * (1 - (1 - TOWER_SHAFT_TAPER) * t0)
        seg_h = shaft_h / shaft_segments
        z0 = PODIUM_HEIGHT_FT + shaft_h * t0
        add(f"tower_curtain_wall_{i + 1}", _hollow_curtain_wall(seg_l, seg_w, seg_h, z0))

    # Crown: layered infill slabs + folded transition planes (orange facets)
    schedule = list(CROWN_SETBACKS_FT)
    for idx in range(1, len(schedule)):
        z1, li, wi = schedule[idx]
        z0, lo, wo = schedule[idx - 1][:3]
        if z1 <= z0:
            continue
        add(f"crown_infill_{idx}", _crown_infill_slab(lo, wo, z0))
        for j, fold in enumerate(_folded_step(lo, wo, li, wi, z0, z1, LAYER_CROWN)):
            add(f"crown_fold_{idx}_{j}", fold)

    # Square crown cap — glass infill volume at top
    top_z, top_l, top_w = schedule[-1]
    cap_h = TOTAL_HEIGHT_FT - top_z
    if cap_h > 0:
        add("crown_cap", _hollow_curtain_wall(top_l, top_w, cap_h, top_z))

    for name, mesh in meshes:
        scene.add_geometry(mesh, node_name=name)
    return scene


def main():
    render_drawing_sheet()
    render_site_plan()
    render_typical_floor()
    render_north_elevation()
    scene = build_massing_3d()
    scene.export(ROOT / "frost_tower_massing.glb")
    combined = trimesh.util.concatenate(list(scene.geometry.values()))
    combined.export(ROOT / "frost_tower_massing.stl")
    print("Frost Bank Tower study generated.")
    print("  frost_drawing_sheet.png")
    print("  frost_site_plan.png")
    print("  frost_floor_plan.png")
    print("  frost_north_elevation.png")
    print("  frost_tower_massing.glb")


if __name__ == "__main__":
    main()