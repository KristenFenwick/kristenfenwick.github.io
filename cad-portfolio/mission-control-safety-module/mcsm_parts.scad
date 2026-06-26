include <mcsm_config.scad>

function explode_offset(part_index) =
    preview_exploded ? [0, 0, part_index * explode_gap] : [0, 0, 0];

module rounded_box(size, r) {
    minkowski() {
        cube([size.x - 2*r, size.y - 2*r, size.z - 2*r]);
        sphere(r = r);
    }
}

module mounting_boss(x, y) {
    translate([x, y, 0])
        cylinder(h = mount_boss_height, d = 14, $fn = 48);
}

module anti_slip_pad(x, y) {
    translate([x, y, -anti_slip_pad_height])
        cylinder(h = anti_slip_pad_height, d = anti_slip_pad_dia, $fn = 48);
}

module base_plate() {
    difference() {
        union() {
            rounded_box([module_footprint_x, module_footprint_y, floor_clearance], 6);
            for (x = [mount_hole_inset_x, module_footprint_x - mount_hole_inset_x])
                for (y = [mount_hole_inset_y, module_footprint_y - mount_hole_inset_y])
                    mounting_boss(x, y);
        }
        for (x = [mount_hole_inset_x, module_footprint_x - mount_hole_inset_x])
            for (y = [mount_hole_inset_y, module_footprint_y - mount_hole_inset_y])
                translate([x, y, -1])
                    cylinder(h = mount_boss_height + 2, d = mount_hole_dia, $fn = 36);
        // Charger trunk tie-down slot relief (parametric)
        translate([module_footprint_x/2, -1, floor_clearance - 2])
            cube([charger_tie_down_slot_width_mm * 0.35, 8, 4]);
    }
    for (x = [mount_hole_inset_x, module_footprint_x - mount_hole_inset_x])
        for (y = [mount_hole_inset_y, module_footprint_y - mount_hole_inset_y])
            anti_slip_pad(x, y);
}

module hollow_rim_drum() {
    z0 = floor_clearance;
    difference() {
        union() {
            translate([module_footprint_x * 0.36, drum_axis_y, z0 + drum_width/2])
                rotate([90, 0, 0])
                    cylinder(h = drum_width, r = drum_outer_r, center = true, $fn = 96);
            // Side webs (hollow-rim structure)
            for (a = [0, 120, 240])
                translate([module_footprint_x * 0.36, drum_axis_y, z0 + drum_width/2])
                    rotate([90, 0, a])
                        linear_extrude(height = drum_outer_r - drum_inner_r, center = true, convexity = 4)
                            polygon(points = [
                                [-drum_web_thick/2, -drum_outer_r + 2],
                                [ drum_web_thick/2, -drum_outer_r + 2],
                                [ drum_web_thick/2, -drum_inner_r - 2],
                                [-drum_web_thick/2, -drum_inner_r - 2]
                            ]);
        }
        translate([module_footprint_x * 0.36, drum_axis_y, z0 + drum_width/2])
            rotate([90, 0, 0])
                cylinder(h = drum_width + 2, r = drum_inner_r, center = true, $fn = 96);
        // Axle bore
        translate([module_footprint_x * 0.36, drum_axis_y, z0 + drum_width/2])
            rotate([90, 0, 0])
                cylinder(h = drum_width + 4, r = 6, center = true, $fn = 36);
    }
}

module cable_guide_roller(cx, cy, cz) {
    translate([cx, cy, cz])
        rotate([0, 90, 0])
            difference() {
                cylinder(h = 10, r = guide_roller_r, center = true, $fn = 48);
                cylinder(h = 12, r = guide_roller_r - 2.2, center = true, $fn = 48);
            }
}

module cable_channel() {
    z0 = floor_clearance + 8;
    hull() {
        translate([module_footprint_x * 0.36, drum_axis_y - drum_outer_r - 6, z0])
            sphere(r = cable_dia/2 + 1.5, $fn = 24);
        translate([module_footprint_x * 0.78, module_footprint_y - 36, z0 + 12])
            sphere(r = cable_dia/2 + 1.5, $fn = 24);
    }
    cable_guide_roller(module_footprint_x * 0.52, drum_axis_y - 8, z0 + 4);
    cable_guide_roller(module_footprint_x * 0.68, module_footprint_y - 52, z0 + 10);
}

module deployment_gate() {
    z0 = floor_clearance + module_height_z - 18;
    difference() {
        translate([module_footprint_x - 58, module_footprint_y - 70, z0])
            rounded_box([52, 58, 16], 3);
        translate([module_footprint_x - 32, module_footprint_y - 42, z0 - 1])
            cube([deployment_slot_w, deployment_slot_len, 20]);
        translate([module_footprint_x - 32, module_footprint_y - 42, z0 + 8])
            rotate([0, 45, 0])
                cylinder(h = 20, r = cable_dia/2 + 0.6, $fn = 32);
    }
}

module ratchet_latch() {
    z0 = floor_clearance + module_height_z - 10;
    difference() {
        translate([module_footprint_x * 0.58, module_footprint_y - 28, z0])
            rounded_box([latch_tab_w, 28, 8], 2);
        translate([module_footprint_x * 0.58 + 6, module_footprint_y - 20, z0 - 1])
            cube([4, 14, 10]);
    }
    // Pawl tooth
    translate([module_footprint_x * 0.58 + latch_tab_w - 2, module_footprint_y - 22, z0 + 2])
        rotate([0, 0, -25])
            cube([8, 3, 5]);
}

module housing_shell() {
    z0 = floor_clearance;
    difference() {
        union() {
            translate([8, 8, z0])
                rounded_box([module_footprint_x - 16, module_footprint_y - 16, module_height_z - cover_thickness], 5);
            deployment_gate();
            ratchet_latch();
        }
        // Drum clearance cavity
        translate([module_footprint_x * 0.36, drum_axis_y, z0 + module_height_z/2])
            rotate([90, 0, 0])
                cylinder(h = drum_width + 10, r = drum_outer_r + 5, center = true, $fn = 96);
        // Cable channel cut
        translate([module_footprint_x * 0.36, drum_axis_y - drum_outer_r, z0 + 6])
            cube([module_footprint_x * 0.5, 24, module_height_z]);
        // Ventilation slots
        for (i = [0 : vent_slot_count - 1])
            translate([24 + i * 38, 4, z0 + module_height_z - cover_thickness - 6])
                cube([vent_slot_w, module_footprint_y - 8, 8]);
        // Handle recess
        translate([module_footprint_x/2 - 35, -1, z0 + 20])
            rounded_box([70, 10, 28], 4);
    }
    cable_channel();
}

module hinged_cover() {
    z0 = floor_clearance + module_height_z - cover_thickness;
    difference() {
        translate([8, 8, z0])
            rounded_box([module_footprint_x - 16, module_footprint_y - 16, cover_thickness], 4);
        // Deployment window
        translate([module_footprint_x - 62, module_footprint_y - 66, z0 - 0.5])
            cube([46, 52, cover_thickness + 1]);
        // Engraving pocket (mission ID)
        translate([28, 28, z0 - 0.6])
            linear_extrude(height = 0.8)
                text("MCSM", size = 8, font = "Helvetica:style=Bold", halign = "left", valign = "bottom");
    }
    // Hinge pins
    for (y = [20, module_footprint_y - 20])
        translate([10, y, z0 + cover_thickness/2])
            rotate([0, 90, 0])
                cylinder(h = cover_hinge_pin * 2 + 6, r = cover_hinge_pin/2, center = true, $fn = 24);
}

module mcsm_assembly() {
    translate(explode_offset(0)) base_plate();
    translate(explode_offset(1)) hollow_rim_drum();
    translate(explode_offset(2)) housing_shell();
    translate(explode_offset(3)) hinged_cover();
}