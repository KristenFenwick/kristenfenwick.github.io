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


def render_2d_drawing() -> None:
    """Publication-quality 2D technical drawing PNG."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Wedge
    from matplotlib.lines import Line2D

    fig, ax = plt.subplots(figsize=(13, 9), facecolor="#FAF9F6")
    ax.set_facecolor("#FAF9F6")
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_aspect("equal")

    # Title
    ax.text(0.4, 8.55, "Aurora Trunnion Mounting Plate", fontsize=18, fontweight="light",
            color="#2A2A2A", fontfamily="sans-serif")
    ax.text(0.4, 8.2, "Kristen Fenwick  ·  Scale 1:1  ·  Units: mm  ·  6061-T6 Aluminum",
            fontsize=9, color="#6E6A65")

    # TOP VIEW — intricate outline
    ox, oy = 1.2, 4.2
    scale = 0.018
    prof = plate_outline_2d() * scale
    poly = Polygon(prof + [ox + 1.6, oy + 1.1], closed=True,
                   fill=False, edgecolor="#2A2A2A", linewidth=2.2)
    ax.add_patch(poly)

    # Center lines
    ax.plot([ox + 1.6, ox + 1.6], [oy + 0.2, oy + 2.0], color="#B8B2A8", lw=0.8, ls="--")
    ax.plot([ox + 0.3, ox + 2.9], [oy + 1.1, oy + 1.1], color="#B8B2A8", lw=0.8, ls="--")

    # Holes
    for hx, hy in [(-72, 48), (72, 48), (-72, -48), (72, -48)]:
        cx, cy = ox + 1.6 + hx * scale, oy + 1.1 + hy * scale
        ax.add_patch(Circle((cx, cy), 8 * scale, fill=False, ec="#2A2A2A", lw=1.6))
        ax.add_patch(Circle((cx, cy), 4.4 * scale, fill=False, ec="#2A2A2A", lw=1.0))
        ax.plot(cx, cy, "k+", ms=4, mew=0.8)

    # Central recess
    ax.add_patch(Circle((ox + 1.6, oy + 1.1), 38 * scale, fill=False, ec="#2A2A2A", lw=1.2, ls="--"))

    # Lightening pockets
    theta = np.linspace(0, 2 * np.pi, 40)
    for px, py, rx, ry in [(0, 0, 16, 10), (-42, 22, 12, 8), (42, -22, 12, 8)]:
        ellipse_pts = np.column_stack([
            (px + rx * np.cos(theta)) * scale + ox + 1.6,
            (py + ry * np.sin(theta)) * scale + oy + 1.1,
        ])
        ax.add_patch(Polygon(ellipse_pts, closed=True, fill=False, ec="#2A2A2A", lw=1.0))

    # Keyhole slots
    for sx in [-50, 50]:
        cx = ox + 1.6 + sx * scale
        ax.add_patch(FancyBboxPatch((cx - 18 * scale, oy + 1.1 - 4 * scale),
                                    36 * scale, 8 * scale, boxstyle="round,pad=0",
                                    fill=False, ec="#2A2A2A", lw=1.0))
        ax.add_patch(Circle((cx - 12 * scale, oy + 1.1), 6 * scale, fill=False, ec="#2A2A2A", lw=1.0))

    ax.text(ox + 1.6, oy + 2.25, "TOP VIEW", ha="center", fontsize=10, color="#2A2A2A",
            fontweight="light", fontfamily="sans-serif")

    # Dimension — overall width
    ax.annotate("", xy=(ox + 0.3, oy - 0.05), xytext=(ox + 2.9, oy - 0.05),
                arrowprops=dict(arrowstyle="<->", color="#2A2A2A", lw=0.9))
    ax.text(ox + 1.6, oy - 0.22, "176", ha="center", fontsize=9, color="#2A2A2A")

    ax.annotate("", xy=(ox - 0.15, oy + 0.2), xytext=(ox - 0.15, oy + 2.0),
                arrowprops=dict(arrowstyle="<->", color="#2A2A2A", lw=0.9))
    ax.text(ox - 0.35, oy + 1.1, "124", ha="center", va="center", rotation=90, fontsize=9)

    # SECTION A-A
    sx0, sy0 = 5.0, 4.5
    ax.plot([sx0, sx0 + 2.8], [sy0, sy0], color="#2A2A2A", lw=2.2)
    ax.plot([sx0, sx0 + 2.8], [sy0 + 0.14 * scale * 1000 / 18, sy0 + 0.14 * scale * 1000 / 18],
            color="#2A2A2A", lw=2.2)
    # pocket cut in section
    ax.plot([sx0 + 1.0, sx0 + 1.6], [sy0, sy0 + 0.08], color="#2A2A2A", lw=1.0)
    ax.plot([sx0 + 1.0, sx0 + 1.6], [sy0 + 0.14 * scale * 1000 / 18, sy0 + 0.06], color="#2A2A2A", lw=1.0)
    ax.annotate("", xy=(sx0 + 3.0, sy0), xytext=(sx0 + 3.0, sy0 + 0.14 * scale * 1000 / 18),
                arrowprops=dict(arrowstyle="<->", color="#2A2A2A", lw=0.9))
    ax.text(sx0 + 3.2, sy0 + 0.07, "14", fontsize=9, va="center")
    ax.text(sx0 + 1.4, sy0 + 0.55, "SECTION A–A", ha="center", fontsize=10, color="#2A2A2A",
            fontweight="light")

    # NOTES
    notes_x = 5.0
    ax.text(notes_x, 7.8, "NOTES", fontsize=10, color="#2A2A2A", fontweight="light")
    for i, note in enumerate([
        "1. DEBURR AND BREAK ALL SHARP EDGES 0.5 mm MAX.",
        "2. HOLE POSITION TOLERANCE ±0.15 mm.",
        "3. LIGHTENING POCKETS: RA 1.6 µm SURFACE FINISH.",
        "4. COUNTERBORE DEPTH 5.0 mm UNLESS NOTED.",
        "5. COMPATIBLE WITH VESPER DEPLOYMENT POD INTERFACE.",
        "6. UNLESS NOTED, DIMENSIONS IN mm.",
    ]):
        ax.text(notes_x, 7.45 - i * 0.28, note, fontsize=8.5, color="#6E6A65")

    # Title block
    tb_x, tb_y = 9.2, 0.5
    ax.add_patch(FancyBboxPatch((tb_x, tb_y), 3.5, 2.2, boxstyle="square,pad=0",
                                fill=False, ec="#2A2A2A", lw=1.5))
    for yy in [tb_y + 0.55, tb_y + 1.1, tb_y + 1.65]:
        ax.plot([tb_x, tb_x + 3.5], [yy, yy], color="#2A2A2A", lw=0.6)
    ax.plot([tb_x + 1.4, tb_x + 1.4], [tb_y, tb_y + 2.2], color="#2A2A2A", lw=0.6)
    fields = [
        ("TITLE", "Aurora Trunnion Plate"),
        ("MATERIAL", "6061-T6 Aluminum"),
        ("DRAWN BY", "K. Fenwick"),
        ("DATE", "Jun 2026"),
        ("SHEET", "1 of 1"),
    ]
    for i, (k, v) in enumerate(fields):
        ax.text(tb_x + 0.12, tb_y + 1.9 - i * 0.44, k, fontsize=7.5, color="#9A958F")
        ax.text(tb_x + 1.55, tb_y + 1.9 - i * 0.44, v, fontsize=8.5, color="#2A2A2A")

    for ext in ("png", "pdf"):
        plt.savefig(ROOT / f"mounting_plate_drawing.{ext}", dpi=200, bbox_inches="tight",
                    facecolor="#FAF9F6", pad_inches=0.3)
    plt.close()


def main():
    mesh = build_plate_3d()
    mesh.export(ROOT / "mounting_plate.glb")
    mesh.export(ROOT / "mounting_plate.stl")
    render_3d(mesh)
    render_2d_drawing()
    print(f"Mounting plate: {len(mesh.vertices):,} verts")
    print("Exported GLB, STL, 3D renders, and 2D drawing.")


if __name__ == "__main__":
    main()