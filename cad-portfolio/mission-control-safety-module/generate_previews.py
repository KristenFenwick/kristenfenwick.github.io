#!/usr/bin/env python3
"""Generate STL and portfolio preview images for MCSM assembly."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh

ROOT = Path(__file__).resolve().parent

# Parametric constants (mirror mcsm_config.scad)
FX, FY, FZ = 320, 240, 88
FLOOR = 6
DRUM_R_OUT, DRUM_R_IN = 46, 34
DRUM_Y = FY * 0.52
DRUM_X = FX * 0.36


def box_faces(x, y, z, w, h, d, color):
    verts = np.array([
        [x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z],
        [x, y, z + d], [x + w, y, z + d], [x + w, y + h, z + d], [x, y + h, z + d],
    ])
    faces = [
        [verts[0], verts[1], verts[2], verts[3]],
        [verts[4], verts[5], verts[6], verts[7]],
        [verts[0], verts[1], verts[5], verts[4]],
        [verts[2], verts[3], verts[7], verts[6]],
        [verts[1], verts[2], verts[6], verts[5]],
        [verts[0], verts[3], verts[7], verts[4]],
    ]
    return [(f, color) for f in faces]


def cylinder_faces(cx, cy, cz, r, h, axis="z", segments=48, color="#8a8580"):
    faces = []
    if axis == "y":
        angles = np.linspace(0, 2 * math.pi, segments, endpoint=False)
        for a in angles:
            a2 = a + 2 * math.pi / segments
            x1, z1 = cx + r * math.cos(a), cz + r * math.sin(a)
            x2, z2 = cx + r * math.cos(a2), cz + r * math.sin(a2)
            faces.append(np.array([
                [x1, cy, z1], [x2, cy, z2], [x2, cy + h, z2], [x1, cy + h, z1]
            ]))
    return [(f, color) for f in faces]


def build_scene(exploded=False):
    gap = 22 if exploded else 0
    parts = []

    # Base plate
    parts += box_faces(0, 0, -gap, FX, FY, FLOOR, "#d8d2c8")

    # Housing shell
    z_h = FLOOR + gap
    parts += box_faces(8, 8, z_h, FX - 16, FY - 16, FZ - 4, "#ece8e2")

    # Hollow drum (torus-like ring approximated as outer minus visual ring)
    parts += cylinder_faces(DRUM_X, DRUM_Y - gap, z_h + 20, DRUM_R_OUT, 62, axis="y", color="#b8b2a8")
    parts += cylinder_faces(DRUM_X, DRUM_Y - gap, z_h + 22, DRUM_R_IN, 58, axis="y", color="#faf9f6")

    # Cover
    parts += box_faces(8, 8, z_h + FZ - 4 + gap, FX - 16, FY - 16, 4, "#c9c3b8")

    # Deployment gate block
    parts += box_faces(FX - 58, FY - 70, z_h + FZ - 18, 52, 58, 16, "#bfb9ae")

    # Cable guide rollers
    for rx, ry, rz in [(FX * 0.52, DRUM_Y - 8, z_h + 12), (FX * 0.68, FY - 52, z_h + 18)]:
        parts += cylinder_faces(rx, ry - gap, rz, 5, 10, axis="y", color="#6e6a65")

    return parts


def render_view(parts, elev, azim, outfile, title=None):
    fig = plt.figure(figsize=(10, 7), facecolor="#FAF9F6")
    ax = fig.add_subplot(111, projection="3d", facecolor="#FAF9F6")

    for face, color in parts:
        poly = Poly3DCollection([face], alpha=0.96, linewidths=0.15, edgecolors="#5a5652")
        poly.set_facecolor(color)
        ax.add_collection3d(poly)

    ax.set_xlim(-20, FX + 20)
    ax.set_ylim(-20, FY + 20)
    ax.set_zlim(-30, FZ + 40)
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((FX, FY, FZ))
    ax.axis("off")
    if title:
        ax.text2D(0.02, 0.96, title, transform=ax.transAxes, fontsize=11,
                  color="#2A2A2A", fontfamily="sans-serif", fontweight="light")

    plt.tight_layout(pad=0)
    plt.savefig(outfile, dpi=180, bbox_inches="tight", facecolor="#FAF9F6")
    plt.close()


def write_stl(outfile: Path):
    """Export simplified combined mesh for portfolio download."""
    vertices = []
    faces = []

    def add_box(x, y, z, w, h, d):
        base = len(vertices)
        box_verts = [
            [x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z],
            [x, y, z + d], [x + w, y, z + d], [x + w, y + h, z + d], [x, y + h, z + d],
        ]
        vertices.extend(box_verts)
        faces.extend([
            [base, base + 1, base + 2], [base, base + 2, base + 3],
            [base + 4, base + 5, base + 6], [base + 4, base + 6, base + 7],
            [base, base + 1, base + 5], [base, base + 5, base + 4],
            [base + 2, base + 3, base + 7], [base + 2, base + 7, base + 6],
            [base + 1, base + 2, base + 6], [base + 1, base + 6, base + 5],
            [base, base + 3, base + 7], [base, base + 7, base + 4],
        ])

    add_box(0, 0, 0, FX, FY, FLOOR)
    add_box(8, 8, FLOOR, FX - 16, FY - 16, FZ - 4)
    add_box(8, 8, FLOOR + FZ - 4, FX - 16, FY - 16, 4)
    add_box(FX - 58, FY - 70, FLOOR + FZ - 18, 52, 58, 16)

    data = np.zeros(len(faces), dtype=mesh.Mesh.dtype)
    for i, f in enumerate(faces):
        for j in range(3):
            data["vectors"][i][j] = vertices[f[j]]
    m = mesh.Mesh(data)
    m.save(str(outfile))


def main():
    scene = build_scene(exploded=False)
    exploded = build_scene(exploded=True)

    render_view(scene, elev=22, azim=-58,
                outfile=ROOT / "mcsm_assembly_preview.png",
                title="MCSM Assembly — 2023 Dodge Charger trunk mount")
    render_view(exploded, elev=18, azim=-52,
                outfile=ROOT / "mcsm_exploded_preview.png",
                title="Exploded view — base, drum, housing, cover")
    render_view(scene, elev=0, azim=-90,
                outfile=ROOT / "mcsm_section_preview.png",
                title="Section view — cable channel + deployment gate")

    write_stl(ROOT / "mcsm_assembly.stl")
    print("Generated previews and STL.")


if __name__ == "__main__":
    main()