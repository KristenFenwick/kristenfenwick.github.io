# Frost Bank Tower CAD — Restart Handoff (paste into new chat)

**User:** Kristen Fenwick · Portfolio: https://kristenfenwick.github.io/

## Copy-paste prompt for new conversation

```
Continue my Frost Bank Tower architectural CAD study.

Project root:
/Users/kriswick/kristenfenwick.github.io/cad-portfolio/frost-bank-tower/

Desktop copies (easy open):
~/Desktop/Frost_Bank_Tower_Study.dxf
~/Desktop/frost_setup.scr
~/Desktop/frost_save_dwg.scr
~/Desktop/frost_tower.lsp

AutoCAD: 2027 Mac (or 2025 if 2027 not installed yet). Open the .dxf NOT .dwg.

In AutoCAD after opening DXF:
1. SCRIPT → frost_setup.scr (zoom to 2D sheet)
2. APPLOAD → frost_tower.lsp → KFFROST (sheet) or KF3D (3D massing)
3. Optional: SCRIPT → frost_save_dwg.scr (save native .dwg)

Regenerate everything:
cd /Users/kriswick/kristenfenwick.github.io/cad-portfolio/frost-bank-tower
python3 generate_frost_tower.py

Key files:
- frost_tower_dimensions.py — all dimensions (515ft, 186x128ft footprint EST)
- generate_frost_tower.py — PNG sheets + GLB
- generate_frost_dwg.py — AutoCAD DXF
- frost_tower_massing.glb — web 3D viewer
- frost_drawing_sheet.png — multi-view technical sheet
- methodology.html — sources & uncertainty

346eur palette: Blue Grey #7298C7 glass, Soft Linen #F5F1E6 podium,
Morning Butter #F3D98F crown, Cherry Blossom #F5A8A8 core/parking.

3D model: layered massing, folded crown facets, hollow curtain wall,
parking as horizontal strata (no protruding pink box).

Prior issue fixed: old frost_tower_study.dwg was invalid (fake DWG).
Use frost_tower_study.dxf only.
```

## File locations

| What | Path |
|------|------|
| **AutoCAD file (open this)** | `frost_tower_study.dxf` |
| **Desktop shortcut** | `~/Desktop/Frost_Bank_Tower_Study.dxf` |
| **Repo folder** | `.../kristenfenwick.github.io/cad-portfolio/frost-bank-tower/` |
| **Portfolio live** | https://kristenfenwick.github.io/ |

## AutoCAD quick steps

1. **File → Open** → `Frost_Bank_Tower_Study.dxf` from Desktop
2. Command line: `SCRIPT` → pick `frost_setup.scr`
3. `APPLOAD` → `frost_tower.lsp` → type `KFFROST` or `KF3D`

## Inside the DXF

- **3D massing** at origin (0,0,0) — feet, use 3DORBIT
- **2D drawings** at X = 2500 ft — elevation, section A-A, floor plan, site plan
- **Layers:** A-PODIUM, A-GLASS, A-CROWN, A-CORE, A-PARKING, A-SITE

## Do NOT open

- `frost_tower_study.dwg` (removed — was invalid)