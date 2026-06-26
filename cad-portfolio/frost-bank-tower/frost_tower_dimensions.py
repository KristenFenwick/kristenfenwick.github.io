"""
Frost Bank Tower — Austin, Texas
Reference dimensions for parametric CAD (sources cited inline).

Primary sources:
  - Wikipedia / Emporis summary: 515 ft total, 400 ft roof, 33 floors, crown 99 ft
  - Duda/Paine: rectangular base transitioning to square crown; folded glass setbacks
  - Site: 1.7 acres (Block 42, Congress Ave & 4th St)

Dimensions marked EST are proportional derivations pending survey/CAD verification.
"""

from __future__ import annotations

# --- Official published dimensions (feet) ---
TOTAL_HEIGHT_FT = 515
ROOF_HEIGHT_FT = 400
CROWN_HEIGHT_FT = 99
FLOOR_COUNT = 33
LEASABLE_SQFT = 525_000

# --- Site ---
SITE_ACRES = 1.7
SITE_SQFT = SITE_ACRES * 43_560  # 74,052 sf
SITE_ADDRESS = "401 Congress Avenue, Austin, TX"
COORDINATES = (30.266489, -97.742689)

# --- Footprint (EST: derived from leasable area / floor count) ---
# 525,000 / 33 ≈ 15,900 sf typical plate → ~126 ft square equivalent
TYPICAL_FLOOR_SQFT = LEASABLE_SQFT / FLOOR_COUNT
TYPICAL_FLOOR_SIDE_FT = (TYPICAL_FLOOR_SQFT ** 0.5)  # ~126.1 ft

# Rectangular base per architect description (EST proportions from imagery)
BASE_LENGTH_FT = 186  # long axis along Congress (EST)
BASE_WIDTH_FT = 128   # short axis (EST)
CROWN_TOP_SIDE_FT = 84  # square crown top (EST from setback imagery)

# --- Vertical zoning ---
PODIUM_FLOORS = 3
PODIUM_HEIGHT_FT = 42  # limestone base (EST ~14 ft/floor)
TOWER_FLOOR_HEIGHT_FT = ROOF_HEIGHT_FT / FLOOR_COUNT  # ~12.12 ft avg
PARKING_LEVELS = 11

# --- Crown setback schedule (EST — folded pane rhythm from elevation photos) ---
# Heights above grade where tower footprint steps inward
CROWN_SETBACKS_FT = [
    (ROOF_HEIGHT_FT - 0, BASE_LENGTH_FT, BASE_WIDTH_FT),
    (ROOF_HEIGHT_FT + 18, 156, 118),
    (ROOF_HEIGHT_FT + 36, 138, 108),
    (ROOF_HEIGHT_FT + 54, 122, 100),
    (ROOF_HEIGHT_FT + 72, 108, 96),
    (ROOF_HEIGHT_FT + 88, 96, 92),
    (TOTAL_HEIGHT_FT, CROWN_TOP_SIDE_FT, CROWN_TOP_SIDE_FT),
]

# --- Drawing scale ---
DRAWING_SCALE = 1 / 64  # 1" = 64'-0" architectural study scale
UNITS = "ft"