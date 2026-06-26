#!/usr/bin/env python3
"""Generate intricate Aurora trunnion mounting plate — 3D mesh, GLB, renders."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent


def plate_outline_2d() -> np.ndarray:
    """Curved bracket outline — superellipse-inspired with mounting ears."""
    pts = []
    for deg in np.linspace(180, 540, 120):
        t = math.radians(deg)
        # Superellipse-like body
        x = 88 * np.sign(math.cos(t)) * abs(math.cos(t)) ** 0.62
        y = 62 * np.sign(math.sin(t)) * abs(math.sin(t)) ** 0.72
        # Mounting ears at four corners
        if 30 < deg % 360 < 60:
            x += 14 * math.cos(math.radians(deg - 40))
            y += 10
        elif 120 < deg % 360 < 150:
            x -= 14 * math.cos(math.radians(deg - 130))
            y += 10
        elif 210 < deg % 360 < 240:
            x -= 14 * math.cos(math.radians(deg - 220))
            y -= 10
        elif 300 < deg % 360 < 330:
            x += 14 * math.cos(math.radians(deg - 310))
            y -= 10
        pts.append([x, y])
    return np.array(pts)


def extrude_profile(profile: np.ndarray, height: float) -> trimesh.Trimesh:
    """Extrude closed 2D profile along Z."""
    n = len(profile)
    bottom = np.column_stack([profile, np.zeros(n)])
    top = np.column_stack([profile, np.full(n, height)])
    verts = np.vstack([bottom, top])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.extend([
            [i, j, n + j], [i, n + j, n + i],  # sides
        ])
    # caps (fan triangulation)
    for i in range(1, n - 1):
        faces.append([0, i, i + 1])
        faces.append([n, n + i + 1, n + i])
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.fix_normals()
    return m


def lightening_pocket(cx: float, cy: float, rx: float, ry: float, depth: float) -> trimesh.Trimesh:
    pocket = trimesh.creation.cylinder(radius=1, height=depth, sections=48)
    scale = np.eye(4)
    scale[0, 0], scale[1, 1] = rx, ry
    pocket.apply_transform(scale)
    pocket.apply_translation([cx, cy, depth * 0.4])
    return pocket


def build_plate_3d() -> trimesh.Trimesh:
    profile = plate_outline_2d()
    plate = extrude_profile(profile, height=14)

    # Central interface recess (Vesper pod mount)
    recess = trimesh.creation.cylinder(radius=38, height=6, sections=64)
    recess.apply_translation([0, 0, 14])

    # Lightening pockets
    pockets = []
    for ox, oy in [(0, 0), (-42, 22), (42, -22), (-38, -28), (38, 28)]:
        p = lightening_pocket(ox, oy, 16 if ox == 0 else 12, 10 if ox == 0 else 8, 8)
        pockets.append(p)

    # Counterbored corner holes
    holes = []
    for hx, hy in [(-72, 48), (72, 48), (-72, -48), (72, -48)]:
        bore = trimesh.creation.cylinder(radius=8, height=20, sections=48)
        bore.apply_translation([hx, hy, -2])
        thru = trimesh.creation.cylinder(radius=4.4, height=20, sections=32)
        thru.apply_translation([hx, hy, -2])
        holes.extend([bore, thru])

    # Keyhole adjustment slots
    slots = []
    for sx, sy, rot in [(-50, 0, 0), (50, 0, 0)]:
        slot = trimesh.creation.box(extents=[36, 8, 20])
        circle = trimesh.creation.cylinder(radius=6, height=20, sections=32)
        circle.apply_translation([-12, 0, 0])
        try:
            s = slot.union(circle, engine="manifold")
        except ValueError:
            s = slot
        s.apply_transform(trimesh.transformations.rotation_matrix(math.radians(rot), [0, 0, 1]))
        s.apply_translation([sx, sy, -2])
        slots.append(s)

    # Underside stiffening ribs
    ribs = []
    for angle in [-25, 0, 25]:
        rib = trimesh.creation.box(extents=[120, 4, 8])
        rib.apply_transform(trimesh.transformations.rotation_matrix(math.radians(angle), [0, 0, 1]))
        rib.apply_translation([0, 0, 0])
        ribs.append(rib)

    result = plate
    for p in pockets + holes + slots:
        try:
            result = result.difference(p, engine="manifold")
        except ValueError:
            pass

    # Raised counterbore rings + pocket rims (visual detail)
    accents = []
    for hx, hy in [(-72, 48), (72, 48), (-72, -48), (72, -48)]:
        ring = trimesh.creation.cylinder(radius=8, height=1.2, sections=48)
        ring.apply_translation([hx, hy, 12.8])
        accents.append(ring)
    for ox, oy, rx, ry in [(0, 0, 16, 10), (-42, 22, 12, 8), (42, -22, 12, 8)]:
        rim_pts = []
        for a in np.linspace(0, 2 * np.pi, 48, endpoint=False):
            rim_pts.append([ox + rx * math.cos(a), oy + ry * math.sin(a), 14])
        rim = trimesh.creation.cylinder(radius=1.2, height=0.8, sections=24)
        for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            r = rim.copy()
            r.apply_translation([ox + rx * math.cos(a), oy + ry * math.sin(a), 13.6])
            accents.append(r)

    result = trimesh.util.concatenate([result] + ribs + accents)
    result.merge_vertices()
    return result


def render_3d(mesh: trimesh.Trimesh) -> None:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    v, f = mesh.vertices, mesh.faces
    polys = v[f]
    step = max(1, len(polys) // 4000)

    for fname, elev, azim, title in [
        ("mounting_plate_3d.png", 28, -48, "Aurora Trunnion Plate — isometric"),
        ("mounting_plate_underside.png", -35, -42, "Underside ribs · lightening pockets"),
    ]:
        fig = plt.figure(figsize=(11, 8), facecolor="#F4F1EC")
        ax = fig.add_subplot(111, projection="3d", facecolor="#F4F1EC")
        col = Poly3DCollection(polys[::step], alpha=0.95, linewidths=0.03, edgecolors="#5a5550")
        col.set_facecolor("#b5aea2")
        ax.add_collection3d(col)
        span = v.max(0) - v.min(0)
        mid = (v.max(0) + v.min(0)) / 2
        ax.set_xlim(mid[0] - span[0] * 0.55, mid[0] + span[0] * 0.55)
        ax.set_ylim(mid[1] - span[1] * 0.55, mid[1] + span[1] * 0.55)
        ax.set_zlim(mid[2] - span[2] * 0.55, mid[2] + span[2] * 0.55)
        ax.view_init(elev=elev, azim=azim)
        ax.axis("off")
        ax.text2D(0.03, 0.96, title, transform=ax.transAxes, fontsize=10.5,
                  color="#2A2A2A", fontweight="light")
        plt.tight_layout(pad=0)
        plt.savefig(ROOT / fname, dpi=200, bbox_inches="tight", facecolor="#F4F1EC")
        plt.close()


def _section_paths(mesh: trimesh.Trimesh, z: float) -> list[np.ndarray]:
    """Slice mesh at Z height and return 2D path polylines in model coords."""
    section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if section is None:
        return []
    planar, _ = section.to_planar()
    paths = []
    for entity in planar.entities:
        pts = planar.vertices[entity.points]
        if len(pts) > 1:
            paths.append(pts)
    return paths


def _draw_section_paths(ax, paths: list[np.ndarray], ox: float, oy: float, scale: float,
                        lw: float, color: str, ls: str = "-") -> None:
    for pts in paths:
        xs = pts[:, 0] * scale + ox
        ys = pts[:, 1] * scale + oy
        closed = np.linalg.norm(pts[0] - pts[-1]) < 0.5
        if closed and len(pts) > 2:
            xs = np.append(xs, xs[0])
            ys = np.append(ys, ys[0])
        ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="round")


def render_2d_drawing(mesh: trimesh.Trimesh) -> None:
    """2D technical drawing derived from actual 3D mesh sections — matches top view."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    bounds = mesh.bounds
    width_mm = bounds[1][0] - bounds[0][0]
    height_mm = bounds[1][1] - bounds[0][1]

    fig, ax = plt.subplots(figsize=(14, 10), facecolor="#FAF9F6")
    ax.set_facecolor("#FAF9F6")
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_aspect("equal")

    ax.text(0.5, 9.55, "Aurora Trunnion Mounting Plate", fontsize=18, fontweight="light",
            color="#2A2A2A")
    ax.text(0.5, 9.15, "Kristen Fenwick  ·  Scale 1:1  ·  Units: mm  ·  6061-T6 Aluminum",
            fontsize=9, color="#6E6A65")

    # Fit top view into drawing area from mesh bounds
    margin = 1.8
    avail_w = 5.8
    avail_h = 5.2
    scale = min(avail_w / width_mm, avail_h / height_mm)
    cx_mm = (bounds[0][0] + bounds[1][0]) / 2
    cy_mm = (bounds[0][1] + bounds[1][1]) / 2
    ox = 3.6 - cx_mm * scale
    oy = 5.8 - cy_mm * scale

    # Center lines through mesh centroid
    ax.plot([ox + cx_mm * scale, ox + cx_mm * scale],
            [oy + (bounds[0][1] - 8) * scale, oy + (bounds[1][1] + 8) * scale],
            color="#B8B2A8", lw=0.7, ls=(0, (6, 4)))
    ax.plot([ox + (bounds[0][0] - 8) * scale, ox + (bounds[1][0] + 8) * scale],
            [oy + cy_mm * scale, oy + cy_mm * scale],
            color="#B8B2A8", lw=0.7, ls=(0, (6, 4)))

    # Top surface outline (z ≈ 14) — outer profile + counterbore rings
    top_paths = _section_paths(mesh, z=13.95)
    top_paths += _section_paths(mesh, z=13.2)
    _draw_section_paths(ax, top_paths, ox, oy, scale, lw=2.4, color="#2A2A2A")

    # Pocket floors + through-holes (z ≈ 6)
    inner_paths = _section_paths(mesh, z=6.0)
    inner_paths += _section_paths(mesh, z=1.0)
    _draw_section_paths(ax, inner_paths, ox, oy, scale, lw=1.2, color="#2A2A2A")

    # Rib edges visible from top (z ≈ 8)
    rib_paths = _section_paths(mesh, z=7.8)
    _draw_section_paths(ax, rib_paths, ox, oy, scale, lw=1.0, color="#6E6A65", ls="-")

    ax.text(ox + cx_mm * scale, oy + (bounds[1][1] + 14) * scale,
            "TOP VIEW", ha="center", fontsize=11, color="#2A2A2A", fontweight="light")

    # Dimensions from mesh bounds
    left = ox + bounds[0][0] * scale
    right = ox + bounds[1][0] * scale
    bottom = oy + bounds[0][1] * scale
    top = oy + bounds[1][1] * scale

    dim_y = bottom - 0.35
    ax.annotate("", xy=(left, dim_y), xytext=(right, dim_y),
                arrowprops=dict(arrowstyle="<->", color="#2A2A2A", lw=0.9))
    ax.text((left + right) / 2, dim_y - 0.22, f"{width_mm:.0f}",
            ha="center", fontsize=9, color="#2A2A2A")

    dim_x = left - 0.35
    ax.annotate("", xy=(dim_x, bottom), xytext=(dim_x, top),
                arrowprops=dict(arrowstyle="<->", color="#2A2A2A", lw=0.9))
    ax.text(dim_x - 0.18, (bottom + top) / 2, f"{height_mm:.0f}",
            ha="center", va="center", rotation=90, fontsize=9, color="#2A2A2A")

    # Section A–A
    sx0, sy0 = 8.2, 5.0
    th = 14 * scale * (14 / max(width_mm, 1)) * (width_mm / 176)
    th = 0.22
    ax.plot([sx0, sx0 + 2.6], [sy0, sy0], color="#2A2A2A", lw=2.2)
    ax.plot([sx0, sx0 + 2.6], [sy0 + th, sy0 + th], color="#2A2A2A", lw=2.2)
    ax.plot([sx0 + 0.9, sx0 + 1.5], [sy0, sy0 + th * 0.55], color="#2A2A2A", lw=1.0)
    ax.plot([sx0 + 0.9, sx0 + 1.5], [sy0 + th, sy0 + th * 0.45], color="#2A2A2A", lw=1.0)
    ax.annotate("", xy=(sx0 + 2.85, sy0), xytext=(sx0 + 2.85, sy0 + th),
                arrowprops=dict(arrowstyle="<->", color="#2A2A2A", lw=0.9))
    ax.text(sx0 + 3.05, sy0 + th / 2, "14", fontsize=9, va="center")
    ax.text(sx0 + 1.3, sy0 + 0.65, "SECTION A–A", ha="center", fontsize=10,
            color="#2A2A2A", fontweight="light")

    notes_x = 8.2
    ax.text(notes_x, 8.6, "NOTES", fontsize=10, color="#2A2A2A", fontweight="light")
    for i, note in enumerate([
        "1. DEBURR AND BREAK ALL SHARP EDGES 0.5 mm MAX.",
        "2. HOLE POSITION TOLERANCE ±0.15 mm.",
        "3. LIGHTENING POCKETS: RA 1.6 µm SURFACE FINISH.",
        "4. COUNTERBORE DEPTH 5.0 mm UNLESS NOTED.",
        "5. COMPATIBLE WITH VESPER DEPLOYMENT POD INTERFACE.",
        "6. TOP VIEW PROJECTED FROM 3D MODEL — 1:1.",
    ]):
        ax.text(notes_x, 8.25 - i * 0.3, note, fontsize=8.5, color="#6E6A65")

    tb_x, tb_y = 10.0, 0.6
    ax.add_patch(FancyBboxPatch((tb_x, tb_y), 3.6, 2.2, boxstyle="square,pad=0",
                                fill=False, ec="#2A2A2A", lw=1.5))
    for yy in [tb_y + 0.55, tb_y + 1.1, tb_y + 1.65]:
        ax.plot([tb_x, tb_x + 3.6], [yy, yy], color="#2A2A2A", lw=0.6)
    ax.plot([tb_x + 1.45, tb_x + 1.45], [tb_y, tb_y + 2.2], color="#2A2A2A", lw=0.6)
    for i, (k, v) in enumerate([
        ("TITLE", "Aurora Trunnion Plate"),
        ("MATERIAL", "6061-T6 Aluminum"),
        ("DRAWN BY", "K. Fenwick"),
        ("DATE", "Jun 2026"),
        ("SHEET", "1 of 1"),
    ]):
        ax.text(tb_x + 0.12, tb_y + 1.9 - i * 0.44, k, fontsize=7.5, color="#9A958F")
        ax.text(tb_x + 1.6, tb_y + 1.9 - i * 0.44, v, fontsize=8.5, color="#2A2A2A")

    for ext in ("png", "pdf"):
        plt.savefig(ROOT / f"mounting_plate_drawing.{ext}", dpi=220, bbox_inches="tight",
                    facecolor="#FAF9F6", pad_inches=0.25)

    # Standalone large top view (matches 3D viewer overhead)
    fig2, ax2 = plt.subplots(figsize=(8, 8), facecolor="#FAF9F6")
    ax2.set_facecolor("#FAF9F6")
    ax2.set_aspect("equal")
    ax2.axis("off")
    s2 = min(6.8 / width_mm, 6.8 / height_mm)
    o2x = 4 - cx_mm * s2
    o2y = 4 - cy_mm * s2
    _draw_section_paths(ax2, top_paths, o2x, o2y, s2, lw=2.6, color="#2A2A2A")
    _draw_section_paths(ax2, inner_paths, o2x, o2y, s2, lw=1.3, color="#2A2A2A")
    _draw_section_paths(ax2, rib_paths, o2x, o2y, s2, lw=1.1, color="#6E6A65")
    ax2.plot([o2x + cx_mm * s2, o2x + cx_mm * s2],
             [o2y + bounds[0][1] * s2, o2y + bounds[1][1] * s2],
             color="#B8B2A8", lw=0.6, ls=(0, (5, 4)))
    ax2.plot([o2x + bounds[0][0] * s2, o2x + bounds[1][0] * s2],
             [o2y + cy_mm * s2, o2y + cy_mm * s2],
             color="#B8B2A8", lw=0.6, ls=(0, (5, 4)))
    ax2.text(0.5, 7.6, "TOP VIEW", fontsize=12, color="#2A2A2A", fontweight="light")
    plt.savefig(ROOT / "mounting_plate_top_view.png", dpi=220, bbox_inches="tight",
                facecolor="#FAF9F6", pad_inches=0.2)
    plt.close("all")


def main():
    mesh = build_plate_3d()
    mesh.export(ROOT / "mounting_plate.glb")
    mesh.export(ROOT / "mounting_plate.stl")
    render_3d(mesh)
    render_2d_drawing(mesh)
    print(f"Mounting plate: {len(mesh.vertices):,} verts")
    print("Exported GLB, STL, 3D renders, and 2D drawing.")


if __name__ == "__main__":
    main()