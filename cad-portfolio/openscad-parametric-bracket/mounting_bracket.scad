// Parametric Mounting Bracket — OpenSCAD
// Kristen Fenwick — CAD work sample

width        = 60;   // mm
height       = 35;   // mm
thickness    = 6;    // mm
hole_radius  = 4;    // mm
hole_inset_x = 15;   // mm from left edge
fillet_r     = 2;    // mm (optional corner radius)

$fn = 48;

module mounting_bracket() {
    difference() {
        minkowski() {
            cube([width - 2*fillet_r, thickness - 2*fillet_r, height - 2*fillet_r]);
            sphere(r = fillet_r);
        }
        for (x = [hole_inset_x, width - hole_inset_x]) {
            translate([x, thickness/2, height/2])
                rotate([90, 0, 0])
                    cylinder(h = thickness + 2, r = hole_radius, center = true);
        }
    }
}

mounting_bracket();