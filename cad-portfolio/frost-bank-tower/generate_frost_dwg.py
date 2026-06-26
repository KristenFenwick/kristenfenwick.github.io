#!/usr/bin/env python3
"""
Frost Bank Tower — AutoCAD-ready DWG export (feet, AIA layers, 346eur colors).
Generates 3D massing + 2D orthographic sheet geometry for AutoCAD 2025 Mac.
"""

from __future__ import annotations

from pathlib import Path

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment
from ezdxf.units import FT

from frost_tower_dimensions import (
    BASE_LENGTH_FT,
    BASE_WIDTH_FT,
    CROWN_HEIGHT_FT,
    CROWN_SETBACKS_FT,
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
    TOTAL_HEIGHT_FT,
    TOWER_SHAFT_TAPER,
)

ROOT = Path(__file__).resolve().parent

# 2D sheet geometry offset from 3D model (feet) — avoids overlap in model space
SHEET_X = 2500.0
SHEET_Y = 0.0

LAYERS = {
    "A-PODIUM": PALETTE_SOFT_LINEN,
    "A-GLASS": PALETTE_BLUE_GREY,
    "A-CROWN": PALETTE_MORNING_BUTTER,
    "A-CORE": PALETTE_CHERRY_BLOSSOM,
    "A-SITE": PALETTE_SOFT_LINEN,
    "A-PARKING": PALETTE_CHERRY_BLOSSOM,
    "A-GRID": "#D8D2C8",
    "A-DIMS": "#2A2A2A",
    "A-TEXT": "#2A2A2A",
    "A-TITLE": "#2A2A2A",
    "A-SECT": PALETTE_MORNING_BUTTER,
    "A-ANNO": "#6E6A65",
    "A-BORDER": "#2A2A2A",
    "DEFPOINTS": "#2A2A2A",
}


def _rgb(hex_color: str) -> int:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return colors.rgb2int((r, g, b))


def _crown_bands() -> list[tuple[float, float, float, float]]:
    bands: list[tuple[float, float, float, float]] = []
    prev_z = CROWN_SETBACKS_FT[0][0]
    for elev, length, width in CROWN_SETBACKS_FT[1:]:
        if elev > prev_z:
            bands.append((prev_z, elev, length, width))
        prev_z = elev
    return bands


def _tower_glass_length() -> float:
    return BASE_LENGTH_FT - 2 * GLASS_SHAFT_INSET_FT


def _tower_glass_width() -> float:
    return BASE_WIDTH_FT - 2 * GLASS_SHAFT_INSET_FT


def _core_size() -> tuple[float, float]:
    return BASE_LENGTH_FT * 0.22, BASE_WIDTH_FT * 0.28


def _setup_doc() -> ezdxf.document.Drawing:
    doc = ezdxf.new("R2018", setup=True)
    doc.units = FT
    doc.header["$INSUNITS"] = 2  # feet
    doc.header["$MEASUREMENT"] = 1  # metric flag off → architectural
    for name, hex_color in LAYERS.items():
        layer = doc.layers.get(name) if name in doc.layers else doc.layers.add(name)
        layer.dxf.true_color = _rgb(hex_color)
    return doc


def _add_3d_box(msp, layer: str, ox: float, oy: float, oz: float,
                lx: float, ly: float, lz: float) -> None:
    c = [
        (ox, oy, oz), (ox + lx, oy, oz), (ox + lx, oy + ly, oz), (ox, oy + ly, oz),
        (ox, oy, oz + lz), (ox + lx, oy, oz + lz), (ox + lx, oy + ly, oz + lz), (ox, oy + ly, oz + lz),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    for face in faces:
        msp.add_3dface([c[i] for i in face], dxfattribs={"layer": layer})


def _add_rect(msp, layer: str, x: float, y: float, w: float, h: float, closed: bool = True) -> None:
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    msp.add_lwpolyline(pts, close=closed, dxfattribs={"layer": layer})


def _add_hatch_rect(msp, layer: str, x: float, y: float, w: float, h: float, pattern: str = "ANSI31") -> None:
    hatch = msp.add_hatch(dxfattribs={"layer": layer, "color": 256})
    hatch.set_pattern_fill(pattern, scale=3.0, angle=45)
    hatch.paths.add_polyline_path(
        [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
        is_closed=True,
    )


def _add_text(msp, layer: str, text: str, x: float, y: float, height: float = 3.0) -> None:
    ent = msp.add_text(text, dxfattribs={"layer": layer, "height": height})
    ent.set_placement((x, y), align=TextEntityAlignment.LEFT)


def build_3d_model(msp) -> None:
    """3D massing centered at origin — open in AutoCAD with 3DORBIT."""
    hl, hw = BASE_LENGTH_FT / 2, BASE_WIDTH_FT / 2
    _add_3d_box(msp, "A-PODIUM", -hl, -hw, 0, BASE_LENGTH_FT, BASE_WIDTH_FT, PODIUM_HEIGHT_FT)

    gi = GLASS_SHAFT_INSET_FT
    shaft_h = ROOF_HEIGHT_FT - PODIUM_HEIGHT_FT
    segments = 6
    for i in range(segments):
        t = i / segments
        seg_l = _tower_glass_length() * (1 - (1 - TOWER_SHAFT_TAPER) * t)
        seg_w = _tower_glass_width() * (1 - (1 - TOWER_SHAFT_TAPER) * t)
        seg_h = shaft_h / segments
        z0 = PODIUM_HEIGHT_FT + shaft_h * t
        _add_3d_box(msp, "A-GLASS", -seg_l / 2, -seg_w / 2, z0, seg_l, seg_w, seg_h)

    cl, cw = _core_size()
    _add_3d_box(msp, "A-CORE", -cl / 2, -cw / 2, 0, cl, cw, ROOF_HEIGHT_FT)

    layer_h = PARKING_STRATA_DEPTH_FT / PARKING_STRATA_COUNT
    for i in range(PARKING_STRATA_COUNT):
        inset = i * 2.0
        pl = BASE_LENGTH_FT * 0.94 - inset
        pw = BASE_WIDTH_FT * 0.94 - inset
        z0 = -PARKING_STRATA_DEPTH_FT + i * layer_h
        _add_3d_box(msp, "A-PARKING", -pl / 2, -pw / 2, z0, pl, pw, layer_h * 0.82)

    for z0, z1, length, width in _crown_bands():
        _add_3d_box(msp, "A-CROWN", -length / 2, -width / 2, z0, length, width, z1 - z0)


def build_elevation_2d(msp, ox: float, oy: float) -> None:
    _add_rect(msp, "A-PODIUM", ox, oy, BASE_LENGTH_FT, PODIUM_HEIGHT_FT)
    glass_l = _tower_glass_length()
    gx = ox + (BASE_LENGTH_FT - glass_l) / 2
    tower_h = ROOF_HEIGHT_FT - PODIUM_HEIGHT_FT
    _add_rect(msp, "A-GLASS", gx, oy + PODIUM_HEIGHT_FT, glass_l, tower_h)
    floors = FLOOR_COUNT - PODIUM_FLOORS
    for i in range(1, floors):
        fy = oy + PODIUM_HEIGHT_FT + tower_h * i / floors
        msp.add_line((gx, fy), (gx + glass_l, fy), dxfattribs={"layer": "A-GRID"})

    cx = ox + BASE_LENGTH_FT / 2
    for z0, z1, length, _ in _crown_bands():
        x0 = cx - length / 2
        _add_rect(msp, "A-CROWN", x0, oy + z0, length, z1 - z0)

    msp.add_line((cx, oy - 5), (cx, oy + TOTAL_HEIGHT_FT + 5), dxfattribs={"layer": "A-ANNO"})
    _add_text(msp, "A-DIMS", f"{TOTAL_HEIGHT_FT}'-0\"", ox - 18, oy + TOTAL_HEIGHT_FT / 2, 4)
    _add_text(msp, "A-DIMS", f"{BASE_LENGTH_FT}'-0\"", ox + BASE_LENGTH_FT / 2 - 15, oy - 12, 4)
    _add_text(msp, "A-TEXT", "NORTH ELEVATION", ox, oy + TOTAL_HEIGHT_FT + 15, 5)


def build_section_2d(msp, ox: float, oy: float) -> None:
    _add_hatch_rect(msp, "A-SECT", ox, oy, BASE_WIDTH_FT, PODIUM_HEIGHT_FT, "ANSI37")
    cl, _ = _core_size()
    cx = ox + BASE_WIDTH_FT / 2
    _add_hatch_rect(msp, "A-CORE", cx - cl / 2, oy, cl, ROOF_HEIGHT_FT, "ANSI31")
    gw = BASE_WIDTH_FT - 2 * GLASS_SHAFT_INSET_FT
    _add_rect(msp, "A-GLASS", cx - gw / 2, oy + PODIUM_HEIGHT_FT, gw, ROOF_HEIGHT_FT - PODIUM_HEIGHT_FT)
    for z0, z1, _, width in _crown_bands():
        _add_hatch_rect(msp, "A-CROWN", cx - width / 2, oy + z0, width, z1 - z0, "ANSI32")
    msp.add_line((cx, oy - 5), (cx, oy + TOTAL_HEIGHT_FT + 5), dxfattribs={"layer": "A-ANNO"})
    msp.add_line((ox - 8, oy + ROOF_HEIGHT_FT), (ox + BASE_WIDTH_FT + 8, oy + ROOF_HEIGHT_FT),
                 dxfattribs={"layer": "A-ANNO", "linetype": "DASHED"})
    _add_text(msp, "A-TEXT", "SECTION A-A", ox, oy + TOTAL_HEIGHT_FT + 15, 5)
    _add_text(msp, "A-ANNO", "A", ox - 5, oy + ROOF_HEIGHT_FT + 2, 4)
    _add_text(msp, "A-ANNO", "A", ox + BASE_WIDTH_FT + 3, oy + ROOF_HEIGHT_FT + 2, 4)


def build_floor_plan_2d(msp, ox: float, oy: float) -> None:
    _add_rect(msp, "A-GLASS", ox, oy, BASE_LENGTH_FT, BASE_WIDTH_FT)
    cl, cw = _core_size()
    cx = ox + (BASE_LENGTH_FT - cl) / 2
    cy = oy + (BASE_WIDTH_FT - cw) / 2
    _add_hatch_rect(msp, "A-CORE", cx, cy, cl, cw, "ANSI31")
    _add_text(msp, "A-TEXT", "CORE", cx + cl / 2 - 4, cy + cw / 2, 3.5)
    for i in range(14):
        x = ox + 3 + i * (BASE_LENGTH_FT - 6) / 13
        msp.add_line((x, oy + 2), (x, oy + BASE_WIDTH_FT - 2), dxfattribs={"layer": "A-GRID"})
    for i in range(9):
        y = oy + 3 + i * (BASE_WIDTH_FT - 6) / 8
        msp.add_line((ox + 2, y), (ox + BASE_LENGTH_FT - 2, y), dxfattribs={"layer": "A-GRID"})
    msp.add_line((ox + BASE_LENGTH_FT / 2, oy - 5), (ox + BASE_LENGTH_FT / 2, oy + BASE_WIDTH_FT + 5),
                 dxfattribs={"layer": "A-ANNO"})
    _add_text(msp, "A-TEXT", "TYPICAL FLOOR", ox, oy + BASE_WIDTH_FT + 12, 5)


def build_site_plan_2d(msp, ox: float, oy: float) -> None:
    site_l, site_w = 280.0, 220.0
    msp.add_lwpolyline(
        [(ox, oy), (ox + site_l, oy), (ox + site_l, oy + site_w), (ox, oy + site_w)],
        close=True,
        dxfattribs={"layer": "A-SITE", "linetype": "DASHED"},
    )
    bx = ox + (site_l - BASE_LENGTH_FT) / 2
    by = oy + (site_w - BASE_WIDTH_FT) / 2
    _add_hatch_rect(msp, "A-PODIUM", bx, by, BASE_LENGTH_FT, BASE_WIDTH_FT, "ANSI37")
    park_w = BASE_LENGTH_FT * 0.38
    msp.add_lwpolyline(
        [(bx + 4, by + 4), (bx + 4 + park_w, by + 4), (bx + 4 + park_w, by + BASE_WIDTH_FT - 4),
         (bx + 4, by + BASE_WIDTH_FT - 4)],
        close=True,
        dxfattribs={"layer": "A-PARKING", "linetype": "DASHED"},
    )
    _add_text(msp, "A-TEXT", f"PARKING {PARKING_LEVELS} LVLS", bx + park_w / 2, by + BASE_WIDTH_FT / 2, 3)
    _add_text(msp, "A-TEXT", "SITE PLAN", ox, oy + site_w + 12, 5)


def build_title_block(msp, ox: float, oy: float) -> None:
    w, h = 186.0, 48.0
    _add_rect(msp, "A-TITLE", ox, oy, w, h)
    _add_text(msp, "A-TITLE", "FROST BANK TOWER — ARCHITECTURAL CAD STUDY", ox + 4, oy + h - 10, 5)
    _add_text(msp, "A-TITLE", "DWG NO. KF-FT-001  |  REV B  |  SCALE 1/64\"=1'-0\"", ox + 4, oy + h - 20, 3.5)
    _add_text(msp, "A-TITLE", f"AUTHOR: Kristen Fenwick  |  {SITE_ADDRESS}", ox + 4, oy + h - 28, 3.5)
    _add_text(msp, "A-TITLE", "UNITS: FEET  |  PROJECTION: THIRD ANGLE  |  PALETTE: 346EUR/CFD", ox + 4, oy + h - 36, 3.5)
    _add_text(msp, "A-ANNO", "REGIONS: ORIGIN=3D MODEL  |  X>2000=SHEET VIEWS  |  RUN frost_setup.scr", ox + 4, oy + 6, 3)


def build_sheet_border(msp, ox: float, oy: float) -> None:
    bw, bh = 700.0, 620.0
    _add_rect(msp, "A-BORDER", ox, oy, bw, bh)


def write_autocad_script(dwg_path: Path) -> None:
    scr = ROOT / "frost_setup.scr"
    scr.write_text(
        f"; Frost Bank Tower — AutoCAD 2025 Mac setup\n"
        f"; Open {dwg_path.name} then run: SCRIPT frost_setup.scr\n"
        "INSUNITS\n2\n"
        "UNITS\n2\n2\n2\n2\n0\n"
        "-LAYER\nM\nA-GLASS\nC\n5\nA-GLASS\n"
        "-LAYER\nM\nA-PODIUM\nC\n254\nA-PODIUM\n"
        "-LAYER\nM\nA-CROWN\nC\n2\nA-CROWN\n"
        "-LAYER\nM\nA-CORE\nC\n6\nA-CORE\n"
        "-VIEW\nS\nKF-3D\n"
        "-0,0,250\n"
        "1,1,1\n"
        "0,1,0\n"
        "50\n"
        "0,0,0\n"
        "KF-3D\n"
        "-VIEW\nS\nKF-SHEET\n"
        f"{SHEET_X + 350}\n"
        f"{SHEET_Y + 300}\n"
        "0,0,1\n"
        "0,1,0\n"
        "0\n"
        f"{SHEET_X + 350}\n"
        f"{SHEET_Y + 300}\n"
        "0\n"
        "KF-SHEET\n"
        "ZOOM\nE\n"
        "ZOOM\nW\n"
        f"{SHEET_X - 20}\n"
        f"{SHEET_Y - 30}\n"
        f"{SHEET_X + 720}\n"
        f"{SHEET_Y + 640}\n"
        "ZOOM\nP\n"
        "QSAVE\n"
        "_.REDRAW\n",
        encoding="utf-8",
    )


def write_autolisp() -> None:
    lisp = ROOT / "frost_tower.lsp"
    lisp.write_text(
        r"""; Frost Bank Tower — AutoCAD 2025 Mac helper
; APPLOAD frost_tower.lsp  then type KFFROST

(defun kf-layer (name aci / )
  (command "._-LAYER" "M" name "C" (itoa aci) "" "")
)

(defun c:KFFROST ()
  (princ "\n[Kristen Fenwick] Frost Bank Tower setup...")
  (kf-layer "A-GLASS" 5)
  (kf-layer "A-PODIUM" 254)
  (kf-layer "A-CROWN" 2)
  (kf-layer "A-CORE" 6)
  (kf-layer "A-PARKING" 6)
  (kf-layer "A-SITE" 254)
  (kf-layer "A-GRID" 8)
  (kf-layer "A-DIMS" 7)
  (kf-layer "A-TEXT" 7)
  (kf-layer "A-TITLE" 7)
  (kf-layer "A-SECT" 2)
  (kf-layer "A-ANNO" 8)
  (kf-layer "A-BORDER" 7)
  (command "._ZOOM" "_W" "2470,0" "3220,640")
  (princ "\nZoomed to 2D sheet. Use view KF-3D for massing, KF-SHEET for drawings.")
  (princ)
)

(defun c:KF3D ()
  (command "._ZOOM" "_W" "-120,-90" "120,530")
  (princ "\n3D model region (feet). Use 3DORBIT.")
  (princ)
)

(princ "\nFrost Tower LISP loaded. Commands: KFFROST, KF3D")
(princ)
""",
        encoding="utf-8",
    )


def write_open_script(dwg_path: Path) -> None:
    sh = ROOT / "open_in_autocad.sh"
    sh.write_text(
        f"""#!/bin/bash
# Open Frost Bank Tower DWG in AutoCAD 2025 Mac
open -a "AutoCAD 2025" "{dwg_path}"
echo "Opened {dwg_path.name}"
echo "In AutoCAD: SCRIPT → frost_setup.scr"
echo "Or APPLOAD → frost_tower.lsp → type KFFROST"
""",
        encoding="utf-8",
    )
    sh.chmod(0o755)


def generate_dwg() -> Path:
    doc = _setup_doc()
    msp = doc.modelspace()

    build_3d_model(msp)

    sx, sy = SHEET_X, SHEET_Y
    build_sheet_border(msp, sx, sy)
    build_elevation_2d(msp, sx + 30, sy + 40)
    build_section_2d(msp, sx + 260, sy + 40)
    build_floor_plan_2d(msp, sx + 430, sy + 40)
    build_site_plan_2d(msp, sx + 430, sy + 220)
    build_title_block(msp, sx + 30, sy + 520)

    out = ROOT / "frost_tower_study.dwg"
    doc.saveas(out)
    write_autocad_script(out)
    write_autolisp()
    write_open_script(out)
    return out


def main() -> None:
    path = generate_dwg()
    print(f"AutoCAD DWG written: {path}")
    print(f"  frost_setup.scr   — run via SCRIPT command in AutoCAD")
    print(f"  frost_tower.lsp   — APPLOAD then KFFROST / KF3D")
    print(f"  open_in_autocad.sh — launch DWG in AutoCAD 2025 Mac")


if __name__ == "__main__":
    main()