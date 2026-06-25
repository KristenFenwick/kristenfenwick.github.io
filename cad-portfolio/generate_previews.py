#!/usr/bin/env python3
"""Generate PNG/PDF previews and STL for CAD portfolio samples."""

from __future__ import annotations

import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent


def write_stl(path: Path) -> None:
    width, height, thickness = 60.0, 35.0, 6.0
    hole_r, inset = 4.0, 15.0
    fillet = 2.0

    def box_triangles(x0, y0, z0, x1, y1, z1):
        verts = [
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ]
        faces = [
            (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
            (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
            (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
        ]
        for a, b, c in faces:
            yield verts[a], verts[b], verts[c]

    x0, y0, z0 = fillet, 0.0, fillet
    x1, y1, z1 = width - fillet, thickness, height - fillet
    triangles = list(box_triangles(x0, y0, z0, x1, y1, z1))

    with path.open("wb") as f:
        f.write(b"\x00" * 80)
        f.write(struct.pack("<I", len(triangles)))
        for v1, v2, v3 in triangles:
            nx, ny, nz = 0.0, 0.0, 1.0
            f.write(struct.pack("<3f", nx, ny, nz))
            for v in (v1, v2, v3):
                f.write(struct.pack("<3f", *v))
            f.write(struct.pack("<H", 0))


def render_bracket_preview(path: Path) -> None:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    width, height, thickness = 60, 35, 6
    verts = [
        [0, 0, 0], [width, 0, 0], [width, thickness, 0], [0, thickness, 0],
        [0, 0, height], [width, 0, height], [width, thickness, height], [0, thickness, height],
    ]
    faces = [
        [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
        [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7],
    ]

    fig = plt.figure(figsize=(8, 6), facecolor="white")
    ax = fig.add_subplot(111, projection="3d")
    poly = Poly3DCollection([[verts[i] for i in face] for face in faces], alpha=0.92)
    poly.set_facecolor("#c45c5c")
    poly.set_edgecolor("#3c0d0d")
    ax.add_collection3d(poly)

    for cx in (15, 45):
        theta = [i * 2 * math.pi / 40 for i in range(41)]
        xs = [cx + 4 * math.cos(t) for t in theta]
        ys = [3 + 4 * math.sin(t) for t in theta]
        zs = [height / 2] * len(theta)
        ax.plot(xs, ys, zs, color="#111", linewidth=1.5)

    ax.set_xlim(0, width)
    ax.set_ylim(0, thickness)
    ax.set_zlim(0, height)
    ax.set_box_aspect((width, thickness, height))
    ax.view_init(elev=24, azim=-58)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("Parametric Mounting Bracket — OpenSCAD Preview", fontsize=12, pad=14)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def svg_to_png(svg_path: Path, png_path: Path, scale: float = 1.5) -> None:
    import xml.etree.ElementTree as ET

    tree = ET.parse(svg_path)
    root = tree.getroot()
    width = int(float(root.attrib.get("width", "1100")) * scale)
    height = int(float(root.attrib.get("height", "850")) * scale)
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
        font_bold = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
        font_bold = font
        font_title = font

    # Raster fallback: embed SVG visually by re-drawing key content from file text labels only.
    # For portfolio speed, copy SVG via PIL by reading pre-rendered instructions from companion metadata.
    # Simpler approach: use macOS qlmanage or just copy SVG as image via cairosvg substitute.
    # We'll draw a white canvas and paste rendered content using matplotlib imread of temporary render.
    # Fallback: render via reportlab ImageReader after converting with built-in minimal parser below.

    ns = {"svg": "http://www.w3.org/2000/svg"}

    def parse_points(s: str):
        return [tuple(map(float, p.split(","))) for p in s.replace(" ", ",").split() if "," in p]

    for elem in root.iter():
        tag = elem.tag.split("}")[-1]
        transform = elem.attrib.get("transform", "")
        tx, ty = 0.0, 0.0
        if "translate" in transform:
            parts = transform.replace("translate(", "").replace(")", "").split(",")
            tx = float(parts[0]) * scale
            ty = float(parts[1]) * scale if len(parts) > 1 else 0.0

        if tag == "rect":
            x = float(elem.attrib.get("x", 0)) * scale + tx
            y = float(elem.attrib.get("y", 0)) * scale + ty
            w = float(elem.attrib.get("width", 0)) * scale
            h = float(elem.attrib.get("height", 0)) * scale
            fill = elem.attrib.get("fill", "none")
            stroke = elem.attrib.get("stroke", None)
            sw = float(elem.attrib.get("stroke-width", 1)) * scale
            if fill not in ("none", "transparent"):
                draw.rectangle([x, y, x + w, y + h], fill=fill, outline=stroke, width=int(sw))
            elif stroke:
                draw.rectangle([x, y, x + w, y + h], outline=stroke, width=int(sw))
        elif tag == "line":
            x1 = float(elem.attrib["x1"]) * scale + tx
            y1 = float(elem.attrib["y1"]) * scale + ty
            x2 = float(elem.attrib["x2"]) * scale + tx
            y2 = float(elem.attrib["y2"]) * scale + ty
            stroke = elem.attrib.get("stroke", "#111")
            sw = float(elem.attrib.get("stroke-width", 1)) * scale
            draw.line([x1, y1, x2, y2], fill=stroke, width=int(sw))
        elif tag == "circle":
            cx = float(elem.attrib["cx"]) * scale + tx
            cy = float(elem.attrib["cy"]) * scale + ty
            r = float(elem.attrib["r"]) * scale
            fill = elem.attrib.get("fill", "none")
            stroke = elem.attrib.get("stroke", "#111")
            sw = float(elem.attrib.get("stroke-width", 1)) * scale
            bbox = [cx - r, cy - r, cx + r, cy + r]
            if fill not in ("none", "transparent"):
                draw.ellipse(bbox, fill=fill, outline=stroke, width=int(sw))
            else:
                draw.ellipse(bbox, outline=stroke, width=int(sw))
        elif tag == "text":
            x = float(elem.attrib.get("x", 0)) * scale + tx
            y = float(elem.attrib.get("y", 0)) * scale + ty
            text = elem.text or ""
            weight = elem.attrib.get("font-weight", "")
            size = int(float(elem.attrib.get("font-size", 14)) * scale * 0.75)
            f = font_title if size >= 18 else (font_bold if weight == "600" or weight == "700" else font)
            draw.text((x, y - size), text, fill=elem.attrib.get("fill", "#111"), font=f)
        elif tag == "path" and "d" in elem.attrib:
            d = elem.attrib["d"]
            if d.startswith("M") and "A" in d:
                # door swing arc only
                parts = d.replace("M", "").replace("A", ",").replace(",", " ").split()
                nums = [float(p) for p in parts if p.replace(".", "", 1).isdigit() or (p[0] == "-" and p[1:].replace(".", "", 1).isdigit())]
                if len(nums) >= 6:
                    x0, y0 = nums[0] * scale + tx, nums[1] * scale + ty
                    x1, y1 = nums[4] * scale + tx, nums[5] * scale + ty
                    draw.arc([min(x0, x1) - 80 * scale, min(y0, y1) - 80 * scale, max(x0, x1), max(y0, y1)], 0, 90, fill="#555", width=2)

    img.save(png_path)


def png_to_pdf(png_path: Path, pdf_path: Path, title: str) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 40, title)
    img = ImageReader(str(png_path))
    iw, ih = Image.open(png_path).size
    max_w, max_h = width - 80, height - 100
    ratio = min(max_w / iw, max_h / ih)
    draw_w, draw_h = iw * ratio, ih * ratio
    c.drawImage(img, 40, height - 60 - draw_h, width=draw_w, height=draw_h, preserveAspectRatio=True)
    c.showPage()
    c.save()


def main() -> None:
    openscad_dir = ROOT / "openscad-parametric-bracket"
    plate_dir = ROOT / "mechanical-mounting-plate"
    office_dir = ROOT / "small-office-floor-plan"

    write_stl(openscad_dir / "mounting_bracket.stl")
    render_bracket_preview(openscad_dir / "mounting_bracket_preview.png")

    plate_svg = plate_dir / "mounting_plate_drawing.svg"
    office_svg = office_dir / "office_floor_plan.svg"
    plate_png = plate_dir / "mounting_plate_drawing.png"
    office_png = office_dir / "office_floor_plan.png"
    svg_to_png(plate_svg, plate_png)
    svg_to_png(office_svg, office_png)
    png_to_pdf(plate_png, plate_dir / "mounting_plate_drawing.pdf", "Mechanical Mounting Plate — 2D CAD Drawing")
    png_to_pdf(office_png, office_dir / "office_floor_plan.pdf", "Small Office Layout — AEC Drafting Sample")

    print("Generated CAD portfolio assets:")
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p.name != "generate_previews.py":
            print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()