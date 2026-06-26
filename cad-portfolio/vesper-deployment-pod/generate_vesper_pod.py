#!/usr/bin/env python3
"""
Vesper Deployment Pod — sculptural emergency-deployment housing.
Organic aerospace form · helical raceway · toroidal drum · sensor bay.
Exports GLB (in-browser 3D), STL, and portfolio renders.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent


def revolve_profile(profile: np.ndarray, segments: int = 96) -> trimesh.Trimesh:
    verts, faces = [], []
    for i in range(segments):
        t0 = 2 * math.pi * i / segments
        t1 = 2 * math.pi * (i + 1) / segments
        ring0, ring1 = [], []
        for x, z in profile:
            ring0.append([x * math.cos(t0), x * math.sin(t0), z])
            ring1.append([x * math.cos(t1), x * math.sin(t1), z])
        base = len(verts)
        verts.extend(ring0)
        verts.extend(ring1)
        n = len(profile)
        for j in range(n - 1):
            a, b = base + j, base + j + 1
            c, d = base + n + j + 1, base + n + j
            faces.extend([[a, b, c], [a, c, d]])
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.fix_normals()
    return m


def vesper_shell_profile() -> np.ndarray:
    """Seed-pod silhouette with integrated release throat taper."""
    pts = []
    for z in np.linspace(-88, 98, 56):
        if z < -55:
            r = 10 + (z + 88) * 0.55
        elif z < -20:
            r = 28 + 6 * math.sin((z + 55) / 35 * math.pi)
        elif z < 35:
            r = 48 + 5 * math.sin(z / 28) + 3 * math.cos(z / 12)
        elif z < 70:
            t = (z - 35) / 35
            r = 53 - 18 * t + 5 * math.sin(t * math.pi * 3)
        else:
            t = (z - 70) / 28
            r = 35 * (1 - t) + 8 * t
        pts.append([max(r, 4), z])
    return np.array(pts)


def helix_raceway(major_r: float, z0: float, pitch: float, turns: float,
                  tube_r: float, sections: int = 160) -> trimesh.Trimesh:
    pieces = []
    for t in np.linspace(0, turns * 2 * math.pi, sections):
        x = major_r * math.cos(t)
        y = major_r * math.sin(t)
        z = z0 + pitch * t / (2 * math.pi)
        s = trimesh.creation.icosphere(subdivisions=2, radius=tube_r)
        s.apply_translation([x, y, z])
        pieces.append(s)
    return trimesh.util.concatenate(pieces)


def torus_ring(major_r: float, tube_r: float, inner_r: float) -> trimesh.Trimesh:
    outer = trimesh.creation.torus(major_radius=major_r, minor_radius=tube_r,
                                   major_sections=72, minor_sections=28)
    inner = trimesh.creation.torus(major_radius=major_r, minor_radius=inner_r,
                                   major_sections=72, minor_sections=28)
    try:
        return outer.difference(inner, engine="manifold")
    except ValueError:
        return outer


def sculptural_grip() -> trimesh.Trimesh:
    pieces = []
    for t in np.linspace(0, math.pi, 36):
        s = trimesh.creation.icosphere(subdivisions=2, radius=5.5)
        s.apply_translation([48 * math.cos(t) + 8, 0, 12 + 28 * math.sin(t)])
        pieces.append(s)
    return trimesh.util.concatenate(pieces)


def window_frame() -> trimesh.Trimesh:
    """Cutaway frame — visual inset, no boolean needed."""
    outer = trimesh.creation.cylinder(radius=16, height=8, sections=48)
    inner = trimesh.creation.cylinder(radius=12, height=10, sections=48)
    try:
        frame = outer.difference(inner, engine="manifold")
    except ValueError:
        frame = outer
    frame.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    frame.apply_translation([44, 0, 30])
    # Inner drum visible through window
    drum_view = trimesh.creation.icosphere(subdivisions=3, radius=11)
    drum_view.apply_translation([40, 0, 30])
    return trimesh.util.concatenate([frame, drum_view])


def sensor_bay() -> trimesh.Trimesh:
    ring = torus_ring(major_r=12, tube_r=3, inner_r=1.8)
    ring.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    ring.apply_translation([50, 0, 48])
    dome = trimesh.creation.icosphere(subdivisions=4, radius=9)
    dome.apply_translation([54, 0, 48])
    return trimesh.util.concatenate([ring, dome])


def locking_collar() -> trimesh.Trimesh:
    collar = torus_ring(major_r=47, tube_r=7, inner_r=4.2)
    collar.apply_translation([0, 0, 20])
    pin = trimesh.creation.cylinder(radius=3, height=22, sections=32)
    pin.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    pin.apply_translation([50, 0, 20])
    return trimesh.util.concatenate([collar, pin])


def wall_mount_arcs() -> trimesh.Trimesh:
    pieces = []
    for z in [-18, 38]:
        arc = trimesh.creation.torus(major_radius=60, minor_radius=5,
                                     major_sections=56, minor_sections=18)
        arc.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        arc.apply_translation([0, -54, z])
        pieces.append(arc)
    spine = revolve_profile(np.array([[50, -25], [58, -25], [58, 55], [50, 55], [46, 15], [50, -25]]), 40)
    spine.apply_translation([0, -50, 0])
    pieces.append(spine)
    return trimesh.util.concatenate(pieces)


def release_nozzle_ring() -> trimesh.Trimesh:
    prof = np.array([[20, -72], [15, -80], [11, -86], [9, -90], [13, -90], [19, -84], [24, -72]])
    return revolve_profile(prof, 72)


def build_assembly() -> trimesh.Trimesh:
    shell = revolve_profile(vesper_shell_profile(), 128)
    shell.apply_translation([0, 0, 12])

    drum = torus_ring(major_r=30, tube_r=10, inner_r=6.5)
    drum.apply_translation([0, 0, 26])

    helix = helix_raceway(major_r=56, z0=0, pitch=52, turns=2.6, tube_r=4.5)
    collar = locking_collar()
    grip = sculptural_grip()
    window = window_frame()
    sensor = sensor_bay()
    nozzle = release_nozzle_ring()
    mounts = wall_mount_arcs()

    # Fin details — aerospace surface texture
    fins = []
    for a in np.linspace(0, 2 * math.pi, 8, endpoint=False):
        fin = trimesh.creation.box(extents=[3, 18, 28])
        fin.apply_transform(trimesh.transformations.rotation_matrix(a, [0, 0, 1]))
        fin.apply_translation([42 * math.cos(a), 42 * math.sin(a), 50])
        fins.append(fin)

    parts = [shell, drum, helix, collar, grip, window, sensor, nozzle, mounts] + fins
    assembly = trimesh.util.concatenate(parts)
    assembly.merge_vertices()
    return assembly


def render_views(mesh: trimesh.Trimesh) -> None:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    v, f = mesh.vertices, mesh.faces
    polys = v[f]
    step = max(1, len(polys) // 5000)

    configs = [
        ("vesper_hero.png", 24, 52, "Vesper Deployment Pod — sculptural aerospace housing"),
        ("vesper_detail.png", 10, 28, "Helical raceway · toroidal drum · locking collar"),
        ("vesper_side.png", 6, 85, "Sensor bay · release nozzle · wall-mount arcs"),
    ]

    for fname, elev, azim, title in configs:
        fig = plt.figure(figsize=(12, 8.5), facecolor="#F4F1EC")
        ax = fig.add_subplot(111, projection="3d", facecolor="#F4F1EC")
        col = Poly3DCollection(polys[::step], alpha=0.94, linewidths=0.02, edgecolors="#5a5550")
        col.set_facecolor("#b8b0a4")
        ax.add_collection3d(col)

        span = v.max(axis=0) - v.min(axis=0)
        mid = (v.max(axis=0) + v.min(axis=0)) / 2
        ax.set_xlim(mid[0] - span[0] * 0.6, mid[0] + span[0] * 0.6)
        ax.set_ylim(mid[1] - span[1] * 0.6, mid[1] + span[1] * 0.6)
        ax.set_zlim(mid[2] - span[2] * 0.6, mid[2] + span[2] * 0.6)
        ax.view_init(elev=elev, azim=azim)
        ax.axis("off")
        ax.text2D(0.03, 0.96, title, transform=ax.transAxes, fontsize=10.5,
                  color="#2A2A2A", fontweight="light")
        plt.tight_layout(pad=0)
        plt.savefig(ROOT / fname, dpi=200, bbox_inches="tight", facecolor="#F4F1EC")
        plt.close()


def main():
    mesh = build_assembly()
    mesh.export(ROOT / "vesper-pod.glb")
    mesh.export(ROOT / "vesper-pod.stl")
    render_views(mesh)
    print(f"Vesper Pod: {len(mesh.vertices):,} verts · {len(mesh.faces):,} faces")
    print("Exported GLB, STL, PNG renders.")


if __name__ == "__main__":
    main()