"""Candidate-only articulated Hunter surface authoring and small CPU rasterization.

No Blender, game, compiler or shared-file writes. Painted references supply material
microtexture/identity, never cutout anatomy. All pose surfaces are new geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
REPORT = PROJECT / "build/reports/three-town-audit-20261022/walk-repair"
UNITS = ("iceHunter", "veteranIceHunter")
RIGHT = np.array((.722, .692, 0.0))
RIGHT /= np.linalg.norm(RIGHT)
VIEW = np.array((.692, -.722, .18))
VIEW /= np.linalg.norm(VIEW)
UP = np.cross(VIEW, RIGHT)
UP /= np.linalg.norm(UP)
LIGHT = np.array((-.35, -.60, .88))
LIGHT /= np.linalg.norm(LIGHT)
SCALE = 33.5


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(data):
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def candidate_root(unit):
    if unit not in UNITS:
        raise ValueError("unowned creature")
    return PROJECT / "assets/source/creatures" / unit / "walk-v6-offline"


def normalize(v):
    v = np.asarray(v, dtype=float)
    return v / max(float(np.linalg.norm(v)), 1e-12)


def ik(a, b, length_a, length_b, pole):
    """Exact two-bone intersection; refuses unreachable targets rather than scaling."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    axis = b - a
    distance = float(np.linalg.norm(axis))
    if not abs(length_a - length_b) < distance < length_a + length_b:
        raise ValueError(f"unreachable two-bone target {distance:.6f}")
    direction = axis / distance
    bend = np.asarray(pole, float)
    bend = normalize(bend - np.dot(bend, direction) * direction)
    along = (length_a**2 - length_b**2 + distance**2) / (2 * distance)
    return a + direction * along + bend * math.sqrt(max(0, length_a**2 - along**2))


class Surface:
    def __init__(self):
        self.vertices, self.uv, self.faces, self.materials, self.parts = [], [], [], [], []

    def patch(self, rings, material, name, close=True):
        start = len(self.vertices)
        rows, cols = len(rings), len(rings[0])
        for j, ring in enumerate(rings):
            for i, point in enumerate(ring):
                self.vertices.append(np.asarray(point, float))
                self.uv.append((i / cols, j / max(1, rows - 1)))
        for j in range(rows - 1):
            for i in range(cols if close else cols - 1):
                a = start + j * cols + i
                b = start + j * cols + (i + 1) % cols
                c, d = b + cols, a + cols
                for face in ((a, b, c), (a, c, d)):
                    self.faces.append(face)
                    self.materials.append(material)
                    self.parts.append(name)

    def loft(self, centers, widths, depths, material, name, transform=None, sides=14):
        rings = []
        for center, width, depth in zip(centers, widths, depths):
            ring = [np.asarray(center) + np.array((width * math.cos(t), depth * math.sin(t), 0))
                    for t in np.arange(sides) * math.tau / sides]
            rings.append([transform(point) if transform else point for point in ring])
        self.patch(rings, material, name)

    def limb(self, a, b, radius_a, radius_b, material, name, squash=1.0):
        a, b = np.asarray(a, float), np.asarray(b, float)
        axis = normalize(b - a)
        cross = normalize(np.cross(axis, (0, 1, 0)))
        depth = normalize(np.cross(axis, cross))
        rings = []
        for t, bulge in ((0, .83), (.12, 1), (.38, 1.03), (.70, .98), (.94, .88), (1, .78)):
            center = a * (1 - t) + b * t
            radius = ((1 - t) * radius_a + t * radius_b) * bulge
            rings.append([center + radius * (math.cos(q) * cross + math.sin(q) * depth * squash)
                          for q in np.arange(12) * math.tau / 12])
        self.patch(rings, material, name)

    def oval(self, center, radii, material, name, transform=None, sides=14, rows=8):
        centers, widths, depths = [], [], []
        for phi in np.linspace(-math.pi / 2 + .015, math.pi / 2 - .015, rows):
            centers.append(np.array(center) + (0, 0, radii[2] * math.sin(phi)))
            widths.append(radii[0] * math.cos(phi))
            depths.append(radii[1] * math.cos(phi))
        self.loft(centers, widths, depths, material, name, transform, sides)

    def cord(self, points, radius, material, name):
        for a, b in zip(points, points[1:]):
            self.limb(a, b, radius, radius, material, name)

    def export_obj(self, path):
        lines = ["# Own articulated Hunter candidate, not selected or approved", "mtllib materials.mtl"]
        lines += ["v %.7f %.7f %.7f" % tuple(v) for v in self.vertices]
        lines += ["vt %.7f %.7f" % tuple(uv) for uv in self.uv]
        previous = None
        for face, material, part in zip(self.faces, self.materials, self.parts):
            if previous != (material, part):
                lines.extend(("g " + part, "usemtl " + material))
                previous = (material, part)
            lines.append("f " + " ".join(f"{v + 1}/{v + 1}" for v in face))
        path.write_text("\n".join(lines) + "\n", encoding="ascii")


def foot_pose(t, side):
    phase = (t + (0 if side == "near" else .5)) % 1
    stance = phase <= .5
    if stance:
        x, lift = .34 - 1.36 * phase, 0.0
        pitch = .52 * max(0, (phase - .38) / .12)
    else:
        swing = (phase - .5) * 2
        x = -.34 + .68 * (3 * swing**2 - 2 * swing**3)
        lift = .23 * math.sin(math.pi * swing)
        # Return from toe-off to a flat landing without dipping a tilted sole
        # below its authored clearance plane near the end of the swing.
        pitch = .52 * (1 - swing)**2
    y = -.145 if side == "near" else .145
    def transform(point):
        px, py, pz = point
        return np.array((x + .18 + math.cos(pitch) * (px - .18) + math.sin(pitch) * pz,
                         y + py, lift - math.sin(pitch) * (px - .18) + math.cos(pitch) * pz))
    return transform, {"local_phase": phase, "stance": stance, "sole_lift": lift,
                       "pitch": pitch, "track_x": x, "ankle": transform((0, 0, .145)).tolist(),
                       "contact_toe": transform((.18, 0, 0)).tolist()}


def author(t, veteran):
    mesh = Surface()
    bob = -.015 * math.cos(4 * math.pi * t)
    yaw = -.15 + .055 * math.sin(math.tau * t)
    def body(point):
        x, y, z = point
        return np.array((math.cos(yaw) * x - math.sin(yaw) * y,
                         math.sin(yaw) * x + math.cos(yaw) * y, z + bob - .07))
    joints = {"root_local": [0, 0, 0], "reference_root_world_x": 1.36 * t,
              "pelvis_bob": bob, "torso_yaw": yaw, "legs": {}, "arms": {}}
    for side in ("far", "near"):
        foot, record = foot_pose(t, side)
        hip = np.array((0, -.145 if side == "near" else .145, 1.025 + bob))
        ankle = np.array(record["ankle"])
        knee = ik(hip, ankle, .480, .480, (1, 0, 0))
        record.update(hip=hip.tolist(), knee=knee.tolist(), thigh_length=.480, shin_length=.480)
        joints["legs"][side] = record
        mesh.limb(hip, knee, .105, .078, "cloth", side + "_thigh", .90)
        mesh.oval(knee, (.085, .080, .080), "iron", side + "_knee_cap")
        boot_top = ankle * .10 + knee * .90
        mesh.limb(boot_top, ankle, .097, .067, "leather", side + "_shaped_calf_boot")
        mesh.limb(knee, boot_top, .077, .085, "leather", side + "_boot_cuff")
        # A surfaced heel, instep, toe and separate sole, not a warped painted boot.
        profiles = [(0.0, .160, .066, .020), (.035, .165, .071, .020),
                    (.090, .140, .065, .000), (.145, .074, .059, -.005),
                    (.190, .057, .055, -.012)]
        rings = []
        for z, rx, ry, offset in profiles:
            ring = []
            for a in np.arange(16) * math.tau / 16:
                ring.append(foot((offset + rx * math.cos(a), ry * math.sin(a), z)))
            rings.append(ring)
        mesh.patch(rings, "leather", side + "_foot_instep")
        mesh.oval(foot((.110, 0, .045)), (.120, .067, .045), "leather", side + "_toe")
        # Leather bindings follow this bone's local frame, not screen positions.
        for j, amount in enumerate((.20, .47, .74)):
            point = ankle * (1 - amount) + boot_top * amount
            mesh.oval(point, (.083, .073, .013), "strap", side + "_boot_binding_" + str(j))

    mesh.loft([(0, 0, z) for z in (1.00, 1.10, 1.22, 1.37, 1.53, 1.70, 1.83, 1.91)],
              [.16, .225, .225, .17, .18, .235, .245, .12],
              [.18, .22, .20, .15, .18, .23, .25, .105], "cloth", "fitted_tunic", body)
    # Separate overlapping iron corset panels with shaped waist and chest.
    for i, angle in enumerate(np.linspace(0, math.tau, 10, endpoint=False)):
        rings = []
        for z, radius in ((1.34, .178), (1.49, .190), (1.66, .242), (1.79, .234)):
            rings.append([body((radius * math.cos(q), radius * .92 * math.sin(q), z))
                          for q in (angle - .25, angle, angle + .25)])
        mesh.patch(rings, "iron", "corset_panel_" + str(i), close=False)
    for y in (-.108, .108):
        mesh.oval(body((.168, y, 1.697)), (.108, .112, .107), "iron", "contoured_breastplate")
    mesh.cord([body((.19, -.06, 1.39)), body((.245, -.015, 1.58)),
               body((.205, .07, 1.81))], .022, "leather", "diagonal_cuirass_binding")
    for i, angle in enumerate(np.linspace(0, math.tau, 9, endpoint=False)):
        rings = []
        for z, radius in ((1.35, .19), (1.23, .245), (1.06, .29)):
            rings.append([body((radius * math.cos(q), radius * .85 * math.sin(q),
                                z + .012 * math.cos(3 * q)))
                          for q in (angle - .28, angle, angle + .28)])
        mesh.patch(rings, "iron" if i % 3 == 0 else "cloth", "split_tunic_tab_" + str(i), close=False)
        mesh.cord(rings[-1], .012, "trim", "tab_hem_" + str(i))
    mesh.loft([(0, 0, z) for z in (1.335, 1.375)], [.202, .198], [.168, .164],
              "leather", "waist_belt", body)
    mesh.oval(body((.194, -.048, 1.355)), (.035, .047, .034), "gold", "belt_buckle")
    mesh.oval(body((.205, -.045, 1.355)), (.019, .027, .020), "leather", "buckle_inset")

    # Drape is a connected, folded cloth surface with an enlarged Veteran mantle.
    cape = []
    for j in range(9):
        length = j / 8
        row = []
        for i in range(15):
            a = -1.35 + i / 14 * 2.70
            width = (.34 + (.19 if veteran else .12) * length)
            x = -.22 - .20 * length - .05 * math.cos(a) + .025 * math.cos(7 * a) * length
            x -= .025 * math.sin(math.tau * t - length) * length
            y = width * math.sin(a)
            z = 1.91 - (.87 if veteran else .77) * length + .035 * math.cos(5 * a) * length
            row.append(body((x, y, z)))
        cape.append(row)
    mesh.patch(cape, "cape", "folded_patchwork_mantle", close=False)
    mesh.cord(cape[-1], .016, "trim", "mantle_hem")
    for side in (-1, 1):
        mesh.oval(body((-.025, side * .24, 1.825)), (.18, .135, .073), "iron", "segmented_pauldron")
        if veteran:
            for k in range(7):
                a = k / 6 * math.pi
                mesh.oval(body((-.02 + .15 * math.cos(a), side * (.21 + .04 * math.sin(a)), 1.90)),
                          (.063, .060, .041), "fur", "mantle_fur_tuft", sides=9, rows=6)

    bow_hand = None
    for side in ("far", "near"):
        far = side == "far"
        shoulder = body((.025, .235 if far else -.235, 1.805))
        hand = body((.32, .08, 1.10)) if far else body((-.01 + .075 * math.cos(math.tau * t), -.30, 1.10))
        upper, fore = (.40, .40) if far else (.38, .38)
        elbow = ik(shoulder, hand, upper, fore, (-1, -.1, 0) if not far else (.3, .3, -.1))
        mesh.limb(shoulder, elbow, .079, .060, "skin", side + "_exposed_upper_arm")
        mesh.limb(elbow, hand, .062, .045, "skin", side + "_forearm")
        mesh.limb(elbow * .68 + hand * .32, elbow * .08 + hand * .92,
                  .066, .050, "leather", side + "_leather_bracer")
        mesh.oval(hand, (.052, .045, .068), "skin", side + "_hand")
        for k in range(3):
            mesh.oval(hand + (.014 + k * .010, -.023, -.015), (.018, .022, .033),
                      "skin", side + "_grip_finger", sides=8, rows=5)
        joints["arms"][side] = {"shoulder": shoulder.tolist(), "elbow": elbow.tolist(),
                                "wrist": hand.tolist(), "upper_length": upper, "fore_length": fore}
        if far:
            bow_hand = hand
    bow = []
    for i in range(25):
        s = i / 24
        x = .22 * (1 - math.sin(math.pi * s)) + .50 * (s - .5)
        if veteran:
            x -= .075 * math.exp(-((s - .06) / .08)**2) + .075 * math.exp(-((s - .94) / .08)**2)
        bow.append(bow_hand + (x, 0, (s - .5) * 1.03))
    mesh.cord(bow, .016 if not veteran else .019, "wood", "carried_bow")
    mesh.cord([bow[0], bow[-1]], .0038, "string", "bow_string")
    mesh.limb(bow_hand - (0, 0, .055), bow_hand + (0, 0, .055), .023, .023, "leather", "bow_grip")
    if veteran:
        mesh.cord(bow[:3], .019, "ivory", "upper_recurve_tip")
        mesh.cord(bow[-3:], .019, "ivory", "lower_recurve_tip")
    joints["bow"] = {"handle": bow[12].tolist(), "hand_side": "far",
                     "attachment_error": float(np.linalg.norm(bow[12] - bow_hand))}

    mesh.limb(body((-.21, .14, 1.48)), body((-.31, .14, 2.005)),
              .080, .094, "leather", "back_quiver")
    for i in range(5):
        end = body((-.32 - .045 * i, .15 + .01 * i, 2.175 + .01 * math.sin(i)))
        mesh.limb(body((-.26, .15, 1.82)), end, .008, .008, "wood", "arrow_shaft")
        mesh.oval(end - (0, 0, .025), (.025, .012, .062), "fletching", "arrow_fletching", sides=8, rows=5)

    mesh.limb(body((.035, 0, 1.86)), body((.07, 0, 2.01)), .072, .075, "skin", "neck")
    mesh.loft([(.105, -.012, z) for z in (1.985, 2.025, 2.10, 2.19, 2.27, 2.315)],
              [.055, .105, .136, .142, .124, .06], [.045, .090, .105, .110, .10, .055],
              "skin", "sculpted_face_and_cranium", body, sides=18)
    mesh.oval(body((.244, -.018, 2.14)), (.045, .038, .077), "skin", "nose_bridge")
    mesh.oval(body((.275, -.025, 2.115)), (.038, .040, .029), "skin", "nose_tip")
    mesh.oval(body((.226, -.051, 2.056)), (.028, .043, .012), "lips", "closed_mouth", sides=10, rows=5)
    mesh.oval(body((.217, -.085, 2.174)), (.023, .014, .010), "shadow", "near_eye_socket", sides=10, rows=5)
    mesh.oval(body((.231, -.086, 2.175)), (.008, .010, .007), "eye", "near_eye", sides=8, rows=5)
    mesh.cord([body((.191, -.093, 2.194)), body((.229, -.081, 2.193))], .009, "hair", "eyebrow")
    hood = []
    for z, rx, ry in ((1.985, .17, .15), (2.08, .21, .18), (2.22, .225, .19),
                      (2.33, .16, .155), (2.365, .035, .045)):
        hood.append([body((.045 + rx * math.cos(a), ry * math.sin(a), z))
                     for a in np.linspace(1.65, math.tau - 1.65, 19)])
    mesh.patch(hood, "hood", "open_fitted_hood", close=False)
    mesh.cord([ring[0] for ring in hood], .013, "hood_trim", "hood_near_opening")
    mesh.cord([ring[-1] for ring in hood], .013, "hood_trim", "hood_far_opening")
    for side in (-1, 1):
        for i in range(3):
            mesh.cord([body((.105 - i * .025, side * .12, 2.20)),
                       body((.12 - i * .025, side * .135, 2.06)),
                       body((.065 - i * .025, side * .15, 1.99))],
                      .016, "hair", "hood_hair_strand")
    return mesh, joints


def materials(config, root):
    source = PROJECT / config["painted_identity_source"]
    image = Image.open(source).convert("RGB")
    result = {}
    folder = root / "materials"
    folder.mkdir(exist_ok=True)
    lines = ["# Material colors/textures derived from own painted identity reference"]
    for name, spec in config["materials"].items():
        crop = image.crop(spec["source_patch"]).resize((64, 64), Image.Resampling.BICUBIC)
        sample = np.asarray(crop, float)
        luminance = sample @ np.array((.2126, .7152, .0722))
        detail = np.clip((luminance / max(1, float(np.median(luminance))) - 1) * .24, -.22, .22)
        yy, xx = np.mgrid[:64, :64]
        grain = np.sin(xx * 1.72 + yy * .71) * np.cos(yy * 1.39 - xx * .31) * .035
        texture = np.clip(np.array(spec["rgb"])[None, None, :] * (1 + detail[:, :, None] + grain[:, :, None]), 0, 255)
        path = folder / (name + ".png")
        Image.fromarray(texture.astype(np.uint8)).save(path)
        result[name] = {"pixels": texture, "metallic": spec.get("metallic", 0)}
        lines.extend(("newmtl " + name, "Kd " + " ".join(str(round(c / 255, 5)) for c in spec["rgb"]),
                      "map_Kd materials/" + name + ".png", ""))
    (root / "materials.mtl").write_text("\n".join(lines), encoding="ascii")
    return result


def raster(mesh, material, supersample=3):
    # Only a 132x132 native region is rasterized. This is a small CPU operation.
    crop = (140, 155, 272, 287)
    width = height = 132 * supersample
    vertices = np.asarray(mesh.vertices)
    screen = np.stack((197 + vertices @ RIGHT * SCALE, 266 - vertices @ UP * SCALE,
                       vertices @ VIEW), axis=1)
    screen[:, :2] -= crop[:2]
    screen[:, :2] *= supersample
    normals = np.zeros_like(vertices)
    for face in mesh.faces:
        a, b, c = vertices[list(face)]
        normal = normalize(np.cross(b - a, c - a))
        center = (a + b + c) / 3
        if normal @ (center - np.array((0, 0, center[2]))) < 0:
            normal = -normal
        for i in face:
            normals[i] += normal
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-9)
    rgba = np.zeros((height, width, 4), np.uint8)
    depth = np.full((height, width), -np.inf)
    uv = np.asarray(mesh.uv)
    for face, matname in zip(mesh.faces, mesh.materials):
        ids = list(face)
        tri = screen[ids]
        lo = np.maximum(np.floor(tri[:, :2].min(0)).astype(int), 0)
        hi = np.minimum(np.ceil(tri[:, :2].max(0)).astype(int), (width - 1, height - 1))
        if np.any(hi < lo):
            continue
        a, b, c = tri
        denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(denominator) < 1e-8:
            continue
        yy, xx = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        x, y = xx + .5, yy + .5
        wa = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / denominator
        wb = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / denominator
        wc = 1 - wa - wb
        z = wa * a[2] + wb * b[2] + wc * c[2]
        tile_depth = depth[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        visible = (wa >= 0) & (wb >= 0) & (wc >= 0) & (z > tile_depth)
        if not visible.any():
            continue
        weights = np.stack((wa[visible], wb[visible], wc[visible]), axis=1)
        n = weights @ normals[ids]
        n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-8)
        shade = .34 + .83 * np.maximum(0, n @ LIGHT)
        shade += .09 * np.maximum(0, n[:, 2])
        coords = weights @ uv[ids]
        tex = material[matname]["pixels"]
        tx = ((coords[:, 0] * 2.0 % 1) * 63).astype(int)
        ty = ((coords[:, 1] * 2.0 % 1) * 63).astype(int)
        color = tex[ty, tx] * shade[:, None]
        half = normalize(LIGHT + VIEW)
        spec = np.maximum(0, n @ half)**22 * material[matname]["metallic"] * 100
        color += spec[:, None]
        tile = rgba[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        tile[visible, :3] = np.clip(color, 0, 255).astype(np.uint8)
        tile[visible, 3] = 255
        tile_depth[visible] = z[visible]
    tile = Image.fromarray(rgba).resize((132, 132), Image.Resampling.LANCZOS)
    image = Image.new("RGBA", (450, 400))
    image.alpha_composite(tile, crop[:2])
    return image


def contact_sheet(unit, frames, output, label):
    paths = [PROJECT / "assets/source/creatures" / unit / "registered-v3/native/g02-f000.png"]
    paths += frames
    sheet = Image.new("RGB", (175 * len(paths), 166), (66, 72, 59))
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        image = Image.open(path).convert("RGBA").crop((125, 155, 300, 295))
        draw.line((175 * i, 135, 175 * i + 174, 135), fill=(126, 130, 111))
        sheet.paste(image, (175 * i, 24), image)
        draw.text((175 * i + 3, 4), "selected idle" if i == 0 else path.stem, fill="white")
    sheet.save(output)
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.Resampling.NEAREST).save(output.with_name(output.stem + "-3x-diagnostic.png"))


def run(unit, mode, attempt):
    root = candidate_root(unit)
    configpath = root / "cohort.json"
    config = json.loads(configpath.read_text(encoding="utf-8"))
    if not attempt.isalnum():
        raise ValueError("attempt must be an alphanumeric new output suffix")
    stamp = mode + "-" + attempt
    output = root / stamp
    if output.exists():
        raise ValueError("Preserve previous attempt: output already exists")
    output.mkdir()
    (output / "authoring-source-archive.json").write_text(encoded({
        "source_utf8": Path(__file__).read_text(encoding="utf-8"),
        "sha256": digest(Path(__file__)), "config": config}), encoding="utf-8")
    material = materials(config, output)
    report = REPORT / unit / stamp
    report.mkdir(parents=True, exist_ok=False)
    frames, records = [], []
    phases = (0, 3) if mode == "contacts" else range(6)
    start = time.perf_counter()
    for phase in phases:
        mesh, joints = author(phase / 6, unit == "veteranIceHunter")
        path = output / f"g00-f{phase:03d}.png"
        raster(mesh, material).save(path)
        mesh.export_obj(output / f"phase{phase}.obj")
        record = {"phase": phase, "t": phase / 6, "joints": joints,
                  "vertices": len(mesh.vertices), "triangles": len(mesh.faces),
                  "png": path.relative_to(PROJECT).as_posix(), "png_sha256": digest(path),
                  "mesh_sha256": digest(output / f"phase{phase}.obj"),
                  "bounds_alpha128": Image.open(path).getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()}
        records.append(record)
        frames.append(path)
    contact_sheet(unit, frames, report / "selected-idle-versus-candidate-native.png", stamp)
    receipt = {"unit": unit, "status": "built-unreviewed", "selected": False,
               "human_visual_approval": False, "production_ready": False,
               "canvas": [450, 400], "pivot": [197, 266], "facing": "right",
               "method": "New surfaced articulated anatomy; own painted material microtexture; fixed orthographic lightweight CPU rasterizer. No cutout limbs or body-only raster transforms.",
               "identity_contact_gate": "NOT PASSED: head/hood, body silhouette, material fidelity and camera relationship differ from selected painted holding. Six-phase outputs are mechanical diagnostics only, never an approved repaired cohort.",
               "source_sha256": {config["painted_identity_source"]: digest(PROJECT / config["painted_identity_source"]),
                                 "author_cohort.py": digest(Path(__file__)), "cohort.json": digest(configpath)},
               "supersample": 3, "seconds": time.perf_counter() - start, "phases": records,
               "remaining": ["Independent identity/native-scale art review", "Compare sculpted surface/material fidelity with selected painted cohort", "Native foot-slip/timing and both-facing validation by assigned operator", "Rights and final human approval"]}
    (output / "receipt.json").write_text(encoded(receipt), encoding="utf-8")
    (report / "receipt.json").write_text(encoded(receipt), encoding="utf-8")
    print(json.dumps({"unit": unit, "attempt": stamp, "frames": len(records), "seconds": receipt["seconds"],
                      "triangles": records[0]["triangles"], "receipt_sha256": digest(output / "receipt.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("unit", choices=UNITS)
    parser.add_argument("mode", choices=("contacts", "diagnostic"))
    parser.add_argument("--attempt", default="attempt01")
    args = parser.parse_args()
    run(args.unit, args.mode, args.attempt)
