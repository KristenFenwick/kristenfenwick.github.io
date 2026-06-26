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

FX, FY, FZ = 320, 240, 88
FLOOR = 6
WALL_T = 8
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
    angles = np.linspace(0, 2 * math.pi, segments, endpoint=False)
    for a in angles:
        a2 = a + 2 * math.pi / segments
        if axis == "y":
            x1, z1 = cx + r * math.cos(a), cz + r * math.sin(a)
            x2, z2 = cx + r * math.cos(a2), cz + r * math.sin(a2)
            faces.append(np.array([
                [x1, cy, z1], [x2, cy, z2], [x2, cy + h, z2], [x1, cy + h, z1]
            ]))
        elif axis == "x":
            y1, z1 = cy + r * math.cos(a), cz + r * math.sin(a)
            y2, z2 = cy + r * math.cos(a2), cz + r * math.sin(a2)
            faces.append(np.array([
                [cx, y1, z1], [cx, y2, z2], [cx + h, y2, z2], [cx + h, y1, z1]
            ]))
    return [(f, color) for f in faces]


def build_scene(exploded=False):
    gap = 24 if exploded else 0
    parts = []
    z_h = FLOOR + gap

    # 7. Wall mounting bracket
    parts += box_faces(0, -WALL_T - gap, 0, FX, WALL_T, FZ + FLOOR, "#c5bfb4")
    for y_center in [FLOOR + FZ * 0.25, FLOOR + FZ * 0.75]:
        parts += box_faces(FX / 2 - 60, -WALL_T - 18 - gap, y_center - 11, 120, 18, 22, "#b0aaa0")

    # 1. Wall-mounted storage housing
    parts += box_faces(8, WALL_T, z_h, FX - 16, FY - WALL_T - 8, FZ - 4, "#ece8e2")

    # 2. Spool/drum mechanism
    parts += cylinder_faces(DRUM_X, DRUM_Y, z_h + 20, DRUM_R_OUT, 62, axis="y", color="#b8b2a8")
    parts += cylinder_faces(DRUM_X, DRUM_Y, z_h + 22, DRUM_R_IN, 58, axis="y", color="#faf9f6")

    # 5. Guided release channel
    parts += box_faces(FX - 64, FY - 72, z_h + FZ - 20, 56, 62, 18, "#bfb9ae")

    # 6. Modular cable path nodes
    nodes = [
        (DRUM_X, DRUM_Y - DRUM_R_OUT - 4, z_h + 10),
        (FX * 0.50, DRUM_Y - 14, z_h + 16),
        (FX * 0.66, FY - 56, z_h + 22),
        (FX - 36, FY - 44, z_h + 24),
    ]
    for nx, ny, nz in nodes:
        parts += cylinder_faces(nx, ny, nz, 4.5, 8, axis="y", color="#6e6a65")

    # 4. Handle/grip
    parts += box_faces(FX / 2 - 36, 0, z_h + 18, 72, 14, 18, "#a8a29a")

    # 8. Safety label plate
    parts += box_faces(20, FY - 46, z_h + FZ - 6, 86, 28, 2, "#d4cec4")

    # 9. Sensor slot (IoT future iteration)
    parts += box_faces(FX - 54, 20, z_h + 12, 34, 22, 12, "#9a9590")

    # Cover
    parts += box_faces(8, WALL_T, z_h + FZ - 4 + gap, FX - 16, FY - WALL_T - 8, 4, "#c9c3b8")

    # 3. Locking pin
    parts += cylinder_faces(FX * 0.72, FY - 36, z_h + FZ - 14, 2.5, 28, axis="x", color="#5a5652")

    return parts


def render_view(parts, elev, azim, outfile, title=None):
    fig = plt.figure(figsize=(10, 7), facecolor="#FAF9F6")
    ax = fig.add_subplot(111, projection="3d", facecolor="#FAF9F6")

    for face, color in parts:
        poly = Poly3DCollection([face], alpha=0.96, linewidths=0.15, edgecolors="#5a5652")
        poly.set_facecolor(color)
        ax.add_collection3d(poly)

    ax.set_xlim(-40, FX + 20)
    ax.set_ylim(-50, FY + 20)
    ax.set_zlim(-30, FZ + 50)
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((FX, FY + 50, FZ))
    ax.axis("off")
    if title:
        ax.text2D(0.02, 0.96, title, transform=ax.transAxes, fontsize=10,
                  color="#2A2A2A", fontfamily="sans-serif", fontweight="light")

    plt.tight_layout(pad=0)
    plt.savefig(outfile, dpi=180, bbox_inches="tight", facecolor="#FAF9F6")
    plt.close()


def write_stl(outfile: Path):
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

    add_box(0, -WALL_T, 0, FX, WALL_T, FZ + FLOOR)
    add_box(8, WALL_T, FLOOR, FX - 16, FY - WALL_T - 8, FZ - 4)
    add_box(8, WALL_T, FLOOR + FZ - 4, FX - 16, FY - WALL_T - 8, 4)
    add_box(FX - 64, FY - 72, FLOOR + FZ - 20, 56, 62, 18)
    add_box(FX / 2 - 36, 0, FLOOR + 18, 72, 14, 18)
    add_box(20, FY - 46, FLOOR + FZ - 6, 86, 28, 2)
    add_box(FX - 54, 20, FLOOR + 12, 34, 22, 12)

    data = np.zeros(len(faces), dtype=mesh.Mesh.dtype)
    for i, f in enumerate(faces):
        for j in range(3):
            data["vectors"][i][j] = vertices[f[j]]
    m = mesh.Mesh(data)
    m.save(str(outfile))


def main():
    scene = build_scene(exploded=False)
    exploded = build_scene(exploded=True)

    render_view(scene, elev=20, azim=-62,
                outfile=ROOT / "mcsm_assembly_preview.png",
                title="MCSM — wall-mounted storage housing + 9-component assembly")
    render_view(exploded, elev=16, azim=-55,
                outfile=ROOT / "mcsm_exploded_preview.png",
                title="Exploded view — bracket, drum, housing, cover, locking pin")
    render_view(scene, elev=4, azim=-88,
                outfile=ROOT / "mcsm_section_preview.png",
                title="Section — guided release channel, cable path, sensor slot")

    write_stl(ROOT / "mcsm_assembly.stl")
    print("Generated previews and STL.")


if __name__ == "__main__":
    main()