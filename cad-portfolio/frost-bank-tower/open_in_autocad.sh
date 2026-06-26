#!/bin/bash
# Open Frost Bank Tower DXF in AutoCAD Mac (2027 or 2025)
DXF="/Users/kriswick/kristenfenwick.github.io/cad-portfolio/frost-bank-tower/frost_tower_study.dxf"
DESKTOP_DXF="$HOME/Desktop/Frost_Bank_Tower_Study.dxf"

# Keep Desktop copy in sync
cp "$DXF" "$DESKTOP_DXF" 2>/dev/null

for APP in "AutoCAD 2027" "AutoCAD 2025"; do
  if [ -d "/Applications/Autodesk/$APP/$APP.app" ]; then
    open -a "$APP" "$DXF"
    echo "Opened in $APP:"
    echo "  $DXF"
    echo "Desktop copy: $DESKTOP_DXF"
    echo ""
    echo "Next: SCRIPT → frost_setup.scr"
    echo "      APPLOAD → frost_tower.lsp → KFFROST or KF3D"
    exit 0
  fi
done

echo "AutoCAD not found. Install 2027, then open manually:"
echo "  $DESKTOP_DXF"
open "$HOME/Desktop"
exit 1