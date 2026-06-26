// Mission-Control Safety Module (MCSM)
// Compact Emergency Deployment System — 2023 Dodge Charger trunk mount
//
// Kristen Fenwick | OpenSCAD parametric mechanical design
// Portfolio case study: hollow-rim drum geometry, cable routing, latch, assembly
//
// Tools: OpenSCAD, parametric modeling, STL export
// Use case: trunk-mounted safety module for controlled cable/strap deployment
//
// Fellowship relevance: parametric CAD, mechanical constraints, digital assets

use <mcsm_parts.scad>

mcsm_assembly();

// --- 2D drawing export (uncomment in OpenSCAD for technical drawing) ---
// projection(cut = true)
//     translate([0, 0, -floor_clearance - 20])
//         mcsm_assembly();