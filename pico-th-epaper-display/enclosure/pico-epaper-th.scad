// ---------- PARAMETERS ----------
size_x = 50;
size_y = 50;
corner_r = 5;

base_thickness = 4;
wall_thickness = 4;
wall_height = 20;

// post + screw
post_d = 8;
hole_d = 3.2;     // M3 clearance
csk_d = 6.5;      // countersink diameter
csk_depth = 2;

// positioning
edge_margin = -3.5;   // distance from wall to post edge

$fn = 64;

// ---------- DERIVED ----------
post_r = post_d / 2;

// symmetric placement near corners
px1 = wall_thickness + post_r + edge_margin;
px2 = size_x - (wall_thickness + post_r + edge_margin);

py1 = wall_thickness + post_r + edge_margin;
py2 = size_y - (wall_thickness + post_r + edge_margin);

// ---------- MODULES ----------

// Rounded rectangle (2D)
module rounded_rect_2d(x, y, r) {
    r = min(r, min(x, y)/2);

    hull() {
        translate([r, r]) circle(r);
        translate([x - r, r]) circle(r);
        translate([x - r, y - r]) circle(r);
        translate([r, y - r]) circle(r);
    }
}

// Base + hollow walls
module enclosure_body() {
    union() {

        // base plate
        linear_extrude(base_thickness)
            rounded_rect_2d(size_x, size_y, corner_r);

        // walls
        translate([0, 0, base_thickness])
            linear_extrude(wall_height)
                difference() {

                    // outer
                    rounded_rect_2d(size_x, size_y, corner_r);

                    // inner cavity (correct offset)
                    translate([wall_thickness, wall_thickness])
                        rounded_rect_2d(
                            size_x - 2*wall_thickness,
                            size_y - 2*wall_thickness,
                            max(corner_r - wall_thickness, 0.01)
                        );
                }
    }
}

// Corner posts with holes
module corner_posts() {

    positions = [
        [px1, py1],
        [px2, py1],
        [px2, py2],
        [px1, py2]
    ];

    for (p = positions) {
        translate([p[0], p[1], base_thickness])
            difference() {

                // post body
                cylinder(h = wall_height, d = post_d);

                // through hole
                translate([0,0,-0.1])
                    cylinder(h = wall_height + 0.2, d = hole_d);

                // countersink (top side for lid screws)
                translate([0,0,wall_height - csk_depth])
                    cylinder(h = csk_depth + 0.1, d1 = csk_d, d2 = hole_d);
            }
    }
}

// ---------- FINAL ----------
union() {
    enclosure_body();
    corner_posts();
}