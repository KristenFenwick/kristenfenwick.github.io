include <mcsm_config.scad>

function explode_offset(part_index) =
    preview_exploded ? [0, 0, part_index * explode_gap] : [0, 0, 0];

module rounded_box(size, r) {
    minkowski() {
        cube([size.x - 2*r, size.y - 2*r, size.z - 2*r]);
        sphere(r = r);
    }
}

// ── 1. Mounting bracket (wall) ──────────────────────────────────────────

module wall_mount_bracket() {
    difference() {
        union() {
            cube([module_footprint_x, wall_bracket_thick, module_height_z + floor_clearance]);
            for (y = [module_height_z * 0.25, module_height_z * 0.75])
                translate([module_footprint_x/2 - wall_mount_spacing/2, -wall_bracket_tab_h + wall_bracket_thick,
                           floor_clearance + y - wall_bracket_tab_h/2])
                    rounded_box([wall_mount_spacing, wall_bracket_tab_h, wall_bracket_tab_w], 3);
        }
        // Keyhole slots
        for (x = [module_footprint_x/2 - wall_mount_spacing/2 + wall_bracket_tab_w/2,
                  module_footprint_x/2 + wall_mount_spacing/2 - wall_bracket_tab_w/2])
            for (y = [floor_clearance + module_height_z * 0.25,
                      floor_clearance + module_height_z * 0.75])
                translate([x, -wall_bracket_tab_h - 1, y])
                    cube([wall_mount_slot_w, wall_bracket_tab_h + 4, wall_mount_slot_h]);
    }
}

// ── 2. Base plate (trunk mode) ──────────────────────────────────────────

module trunk_base_plate() {
    difference() {
        union() {
            rounded_box([module_footprint_x, module_footprint_y, floor_clearance], 6);
            for (x = [mount_hole_inset_x, module_footprint_x - mount_hole_inset_x])
                for (y = [mount_hole_inset_y, module_footprint_y - mount_hole_inset_y])
                    translate([x, y, 0])
                        cylinder(h = mount_boss_height, d = 14, $fn = 48);
        }
        for (x = [mount_hole_inset_x, module_footprint_x - mount_hole_inset_x])
            for (y = [mount_hole_inset_y, module_footprint_y - mount_hole_inset_y])
                translate([x, y, -1])
                    cylinder(h = mount_boss_height + 2, d = mount_hole_dia, $fn = 36);
        translate([module_footprint_x/2, -1, floor_clearance - 2])
            cube([charger_tie_down_slot_width_mm * 0.35, 8, 4]);
    }
}

module mounting_bracket() {
    if (mount_mode == "wall") wall_mount_bracket();
    else trunk_base_plate();
}

// ── 3. Spool / drum mechanism ───────────────────────────────────────────

module spool_drum_mechanism() {
    z0 = floor_clearance;
    cx = module_footprint_x * 0.36;
    difference() {
        union() {
            translate([cx, drum_axis_y, z0 + drum_width/2])
                rotate([90, 0, 0])
                    cylinder(h = drum_width, r = drum_outer_r, center = true, $fn = 96);
            for (a = [0, 120, 240])
                translate([cx, drum_axis_y, z0 + drum_width/2])
                    rotate([90, 0, a])
                        linear_extrude(height = drum_outer_r - drum_inner_r, center = true, convexity = 4)
                            polygon(points = [
                                [-drum_web_thick/2, -drum_outer_r + 2],
                                [ drum_web_thick/2, -drum_outer_r + 2],
                                [ drum_web_thick/2, -drum_inner_r - 2],
                                [-drum_web_thick/2, -drum_inner_r - 2]
                            ]);
            // Drum flanges
            for (yy = [-1, 1])
                translate([cx, drum_axis_y + yy * (drum_width/2 - 2), z0 + drum_width/2])
                    rotate([90, 0, 0])
                        cylinder(h = 3, r = drum_outer_r + 2, center = true, $fn = 96);
        }
        translate([cx, drum_axis_y, z0 + drum_width/2])
            rotate([90, 0, 0])
                cylinder(h = drum_width + 2, r = drum_inner_r, center = true, $fn = 96);
        translate([cx, drum_axis_y, z0 + drum_width/2])
            rotate([90, 0, 0])
                cylinder(h = drum_width + 4, r = 6, center = true, $fn = 36);
    }
}

// ── 4. Locking pin ──────────────────────────────────────────────────────

module locking_pin() {
    z0 = floor_clearance + module_height_z - 14;
    px = module_footprint_x * 0.72;
    py = module_footprint_y - 36;
    rotate([0, 90, 0])
        union() {
            cylinder(h = lock_pin_len, r = lock_pin_dia/2, $fn = 36);
            translate([0, 0, lock_pin_len - 2])
                cylinder(h = 3, r = lock_pin_head_d/2, $fn = 36);
        }
    // Bore in housing (visual alignment)
    translate([px, py, z0])
        rotate([0, 90, 0])
            cylinder(h = lock_pin_len + 4, r = lock_pin_bore_d/2, center = true, $fn = 32);
}

module locking_pin_bore() {
    z0 = floor_clearance + module_height_z - 14;
    translate([module_footprint_x * 0.72, module_footprint_y - 36, z0])
        rotate([0, 90, 0])
            cylinder(h = lock_pin_len + 6, r = lock_pin_bore_d/2, center = true, $fn = 32);
}

// ── 5. Handle / grip ────────────────────────────────────────────────────

module deployment_handle() {
    z0 = floor_clearance + 18;
    translate([module_footprint_x/2 - grip_length/2, -grip_depth + 2, z0])
        difference() {
            rounded_box([grip_length, grip_depth, grip_width], 4);
            for (i = [0 : grip_ridge_cnt - 1])
                translate([8 + i * (grip_length - 16)/(grip_ridge_cnt - 1), grip_depth - 4, 4])
                    cube([2, 6, grip_width - 6]);
        }
}

module handle_grip_recess() {
    z0 = floor_clearance + 16;
    translate([module_footprint_x/2 - grip_length/2 - 2, -1, z0])
        rounded_box([grip_length + 4, grip_depth + 2, grip_width + 2], 3);
}

// ── 6. Guided release channel ───────────────────────────────────────────

module guided_release_channel() {
    z0 = floor_clearance + module_height_z - 20;
    difference() {
        translate([module_footprint_x - 64, module_footprint_y - 72, z0])
            rounded_box([56, 62, 18], 3);
        // Release throat
        translate([module_footprint_x - 34, module_footprint_y - 44, z0 - 1])
            cube([release_channel_w, release_channel_d, 22]);
        translate([module_footprint_x - 34, module_footprint_y - 44, z0 + 10])
            rotate([0, 50, 0])
                cylinder(h = 22, r = cable_dia/2 + 0.8, $fn = 32);
    }
}

// ── 7. Modular rope/cable path ──────────────────────────────────────────

module cable_guide_roller(cx, cy, cz) {
    translate([cx, cy, cz])
        rotate([0, 90, 0])
            difference() {
                cylinder(h = 10, r = guide_roller_r, center = true, $fn = 48);
                cylinder(h = 12, r = guide_roller_r - 2.2, center = true, $fn = 48);
            }
}

module path_node(cx, cy, cz) {
    translate([cx, cy, cz])
        sphere(r = path_node_r, $fn = 24);
}

module modular_cable_path() {
    z0 = floor_clearance + 10;
    cx = module_footprint_x * 0.36;
    // Segmented path nodes (modular segments)
    path_points = [
        [cx, drum_axis_y - drum_outer_r - 4, z0],
        [module_footprint_x * 0.50, drum_axis_y - 14, z0 + 6],
        [module_footprint_x * 0.66, module_footprint_y - 56, z0 + 12],
        [module_footprint_x - 36, module_footprint_y - 44, z0 + 14]
    ];
    for (i = [0 : len(path_points) - 2])
        hull() {
            translate(path_points[i]) sphere(r = cable_dia/2 + 1.2, $fn = 20);
            translate(path_points[i + 1]) sphere(r = cable_dia/2 + 1.2, $fn = 20);
        }
    for (p = path_points)
        path_node(p.x, p.y, p.z);
    cable_guide_roller(module_footprint_x * 0.50, drum_axis_y - 10, z0 + 4);
    cable_guide_roller(module_footprint_x * 0.66, module_footprint_y - 54, z0 + 10);
}

// ── 8. Safety label plate ───────────────────────────────────────────────

module safety_label_plate() {
    z0 = floor_clearance + module_height_z - cover_thickness - label_plate_t;
    translate([20, module_footprint_y - label_plate_h - 18, z0])
        difference() {
            rounded_box([label_plate_w, label_plate_h, label_plate_t], 2);
            translate([6, 6, -0.2])
                linear_extrude(height = 0.6)
                    text("SAFETY", size = 5, font = "Helvetica:style=Bold", halign = "left", valign = "bottom");
            translate([6, 14, -0.2])
                linear_extrude(height = 0.6)
                    text("DEPLOY", size = 4, font = "Helvetica:style=Regular", halign = "left", valign = "bottom");
        }
}

// ── 9. IoT sensor slot (future data iteration) ──────────────────────────

module sensor_slot() {
    z0 = floor_clearance + 12;
    translate([module_footprint_x - sensor_slot_w - 20, 20, z0])
        difference() {
            cube([sensor_slot_w, sensor_slot_h, sensor_slot_d]);
            translate([4, 4, -1])
                cube([sensor_slot_w - 8, sensor_slot_h - 8, sensor_slot_d + 2]);
            // M3 standoff bosses
            for (dx = [6, sensor_slot_w - 6])
                for (dy = [6, sensor_slot_h - 6])
                    translate([dx, dy, sensor_slot_d - 4])
                        cylinder(h = 5, d = sensor_boss_d, $fn = 24);
        }
}

module sensor_slot_cutout() {
    z0 = floor_clearance + 10;
    translate([module_footprint_x - sensor_slot_w - 22, 18, z0])
        cube([sensor_slot_w + 4, sensor_slot_h + 4, sensor_slot_d + 2]);
}

// ── Wall-mounted storage housing ──────────────────────────────────────────

module wall_storage_housing() {
    z0 = floor_clearance;
    difference() {
        union() {
            translate([8, wall_bracket_thick, z0])
                rounded_box([module_footprint_x - 16, module_footprint_y - wall_bracket_thick - 8,
                             module_height_z - cover_thickness], 5);
            guided_release_channel();
            // Ratchet pawl tab
            translate([module_footprint_x * 0.58, module_footprint_y - 30, z0 + module_height_z - 12])
                rounded_box([latch_tab_w, 26, 8], 2);
        }
        translate([module_footprint_x * 0.36, drum_axis_y, z0 + module_height_z/2])
            rotate([90, 0, 0])
                cylinder(h = drum_width + 10, r = drum_outer_r + 5, center = true, $fn = 96);
        translate([module_footprint_x * 0.36, drum_axis_y - drum_outer_r, z0 + 6])
            cube([module_footprint_x * 0.5, 24, module_height_z]);
        for (i = [0 : vent_slot_count - 1])
            translate([24 + i * 38, wall_bracket_thick + 4, z0 + module_height_z - cover_thickness - 6])
                cube([vent_slot_w, module_footprint_y - wall_bracket_thick - 12, 8]);
        handle_grip_recess();
        locking_pin_bore();
        sensor_slot_cutout();
    }
    modular_cable_path();
    deployment_handle();
    safety_label_plate();
    sensor_slot();
}

module housing_cover() {
    z0 = floor_clearance + module_height_z - cover_thickness;
    y0 = wall_bracket_thick;
    difference() {
        translate([8, y0, z0])
            rounded_box([module_footprint_x - 16, module_footprint_y - y0 - 8, cover_thickness], 4);
        translate([module_footprint_x - 66, module_footprint_y - 68, z0 - 0.5])
            cube([48, 54, cover_thickness + 1]);
        translate([28, y0 + 20, z0 - 0.6])
            linear_extrude(height = 0.8)
                text(label_text, size = 8, font = "Helvetica:style=Bold", halign = "left", valign = "bottom");
    }
    for (yy = [y0 + 20, module_footprint_y - 20])
        translate([10, yy, z0 + cover_thickness/2])
            rotate([0, 90, 0])
                cylinder(h = cover_hinge_pin * 2 + 6, r = cover_hinge_pin/2, center = true, $fn = 24);
}

// ── Full assembly ─────────────────────────────────────────────────────────

module mcsm_assembly() {
    translate(explode_offset(0)) mounting_bracket();
    translate(explode_offset(1)) spool_drum_mechanism();
    translate(explode_offset(2)) wall_storage_housing();
    translate(explode_offset(3)) housing_cover();
    translate(explode_offset(4)) locking_pin();
}