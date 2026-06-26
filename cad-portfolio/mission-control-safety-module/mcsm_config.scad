// Mission-Control Safety Module (MCSM) — parametric configuration
// Kristen Fenwick — OpenSCAD mechanical design + future IoT/data iteration
//
// Mount modes: "wall" (primary) | "trunk" (2023 Dodge Charger reference)

mount_mode = "wall";  // "wall" or "trunk"

// --- Module envelope ---
module_footprint_x = 320;
module_footprint_y = 240;
module_height_z    = 88;
floor_clearance    = 6;

// --- Vehicle reference (trunk mode) ---
charger_trunk_floor_width_mm   = 991;
charger_trunk_depth_mm         = 914;
charger_tie_down_slot_width_mm = 25;

// --- Wall-mount bracket ---
wall_bracket_thick   = 8;
wall_bracket_tab_w   = 48;
wall_bracket_tab_h   = 22;
wall_mount_slot_w    = 6;
wall_mount_slot_h    = 28;
wall_mount_spacing   = 120;

// --- Floor / trunk base plate ---
mount_hole_dia       = 8.4;
mount_hole_inset_x   = 28;
mount_hole_inset_y   = 28;
mount_boss_height    = 4;
anti_slip_pad_dia    = 22;
anti_slip_pad_height = 2;

// --- Hollow-rim spool/drum (ENGR 216 hollow-rim proposal) ---
drum_outer_r     = 46;
drum_inner_r     = 34;
drum_web_thick   = 3.2;
drum_width       = 62;
drum_axis_y      = module_footprint_y * 0.52;

// --- Modular rope/cable path ---
cable_dia            = 6;
guide_roller_r       = 5;
path_segment_count   = 3;
path_node_r          = 4.5;
deployment_slot_w      = 14;
deployment_slot_len  = 48;
release_channel_w    = 12;
release_channel_d    = 38;

// --- Locking pin ---
lock_pin_dia     = 5;
lock_pin_len     = 28;
lock_pin_head_d  = 10;
lock_pin_bore_d  = 5.4;

// --- Handle / grip ---
grip_length    = 72;
grip_width     = 18;
grip_depth     = 14;
grip_ridge_cnt = 5;

// --- Safety label plate ---
label_plate_w  = 86;
label_plate_h  = 28;
label_plate_t  = 2;
label_text     = "MCSM";

// --- IoT / sensor slot (future data-engineering iteration) ---
sensor_slot_w    = 34;
sensor_slot_h    = 22;
sensor_slot_d    = 12;
sensor_boss_d    = 3.2;   // M3 standoff pattern

// --- Housing / cover ---
cover_thickness  = 4;
cover_hinge_pin  = 3;
latch_tab_w      = 18;
vent_slot_w        = 3;
vent_slot_count    = 7;

// --- Render ---
$fn = 72;
preview_exploded = false;
explode_gap      = 20;