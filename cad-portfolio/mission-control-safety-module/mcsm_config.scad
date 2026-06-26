// Mission-Control Safety Module (MCSM) — vehicle configuration
// 2023 Dodge Charger (LD) trunk-mount reference envelope
// Kristen Fenwick — OpenSCAD parametric mechanical design

// --- Vehicle reference (parametric, documented for AI/CAD review) ---
charger_trunk_floor_width_mm   = 991;   // between wheel wells (39 in)
charger_trunk_depth_mm         = 914;   // floor to trunk opening (~36 in)
charger_tie_down_slot_width_mm = 25;

// --- Module envelope (fits rear-trunk corner, clears subfloor) ---
module_footprint_x = 320;
module_footprint_y = 240;
module_height_z    = 88;
floor_clearance    = 6;

// --- Mounting (M8 trunk tie-down compatible pattern) ---
mount_hole_dia       = 8.4;
mount_hole_inset_x   = 28;
mount_hole_inset_y   = 28;
mount_boss_height    = 4;
anti_slip_pad_dia    = 22;
anti_slip_pad_height = 2;

// --- Hollow-rim drum (from ENGR 216 hollow-rim proposal) ---
drum_outer_r     = 46;
drum_inner_r     = 34;
drum_web_thick   = 3.2;
drum_width       = 62;
drum_axis_y      = module_footprint_y * 0.52;

// --- Cable path / deployment ---
cable_dia          = 6;
guide_roller_r       = 5;
deployment_slot_w    = 14;
deployment_slot_len  = 48;

// --- Latch / cover ---
cover_thickness  = 4;
cover_hinge_pin  = 3;
latch_tab_w      = 18;
vent_slot_w        = 3;
vent_slot_count    = 7;

// --- Render quality ---
$fn = 72;
preview_exploded = false;
explode_gap      = 18;