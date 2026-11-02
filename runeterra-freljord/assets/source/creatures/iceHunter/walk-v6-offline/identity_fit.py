"""Finite source-aware upper-body surface fit; independent of preserved v6 attempts.

Projected source color is a material on actual volume/cloth/arm surfaces. No source
foot/leg silhouette, alpha-cutout contact, or whole-frame sprite is composited.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image

import author_cohort as original

HERE = Path(__file__).resolve().parent
PROJECT = original.PROJECT
REPORT = original.REPORT / "identity-fit-finite-pass"
RIGHT = original.normalize((.885, .466, 0))
VIEW = original.normalize((.466, -.885, .18))
UP = original.normalize(np.cross(VIEW, RIGHT))
SCALE = 27.2
TEXTURE_CROP = (165, 188, 240, 245)


def project(point):
    point = np.asarray(point)
    return np.array((197 + point @ RIGHT * SCALE, 266 - point @ UP * SCALE))


def unproject(x, y, depth):
    return RIGHT * ((x - 197) / SCALE) + UP * ((266 - y) / SCALE) + VIEW * depth


def fill_texture(image):
    """Extend RGB into transparent texels, without using alpha to trim geometry."""
    pixels = np.asarray(image.convert("RGBA"), float)
    rgb = pixels[:, :, :3].copy()
    known = pixels[:, :, 3] >= 128
    for _ in range(35):
        if known.all():
            break
        colors = np.zeros_like(rgb)
        weights = np.zeros_like(known, dtype=float)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shifted = np.roll(known, (dy, dx), (0, 1))
            shifted_rgb = np.roll(rgb, (dy, dx), (0, 1))
            if dy < 0:
                shifted[-1] = False
            if dy > 0:
                shifted[0] = False
            if dx < 0:
                shifted[:, -1] = False
            if dx > 0:
                shifted[:, 0] = False
            colors += shifted_rgb * shifted[:, :, None]
            weights += shifted
        update = ~known & (weights > 0)
        rgb[update] = colors[update] / weights[update, None]
        known[update] = True
    rgb[~known] = (80, 60, 41)
    return rgb


def subset(mesh, wanted):
    result = original.Surface()
    mapping = {}
    for face, mat, part in zip(mesh.faces, mesh.materials, mesh.parts):
        if not wanted(part):
            continue
        newface = []
        for index in face:
            if index not in mapping:
                mapping[index] = len(result.vertices)
                result.vertices.append(mesh.vertices[index].copy())
                result.uv.append(mesh.uv[index])
            newface.append(mapping[index])
        result.faces.append(tuple(newface))
        result.materials.append(mat)
        result.parts.append(part)
    return result


def append_reference(mesh, rest, posed=None):
    posed = posed or rest
    if len(rest.vertices) != len(posed.vertices):
        raise ValueError("source/posed surface topology changed")
    start = len(mesh.vertices)
    mesh.vertices.extend(posed.vertices)
    for vertex in rest.vertices:
        x, y = project(vertex)
        mesh.uv.append(((x - TEXTURE_CROP[0]) / (TEXTURE_CROP[2] - TEXTURE_CROP[0]),
                        1 - (y - TEXTURE_CROP[1]) / (TEXTURE_CROP[3] - TEXTURE_CROP[1])))
    mesh.faces.extend(tuple(i + start for i in face) for face in posed.faces)
    mesh.materials.extend(["source_upperbody"] * len(posed.faces))
    mesh.parts.extend(posed.parts)


def posed_copy(rest, transform):
    result = copy.copy(rest)
    result.vertices = [transform(vertex) for vertex in rest.vertices]
    return result


def rings_surface(profiles, name, center_depth, radius_depth):
    surface = original.Surface()
    rings = []
    for y, cx, rx in profiles:
        rings.append([unproject(cx + rx * math.cos(a), y,
                                center_depth + radius_depth * math.sin(a))
                      for a in np.arange(24) * math.tau / 24])
    surface.patch(rings, "source_upperbody", name)
    # Closed end faces retain actual volume rather than a cutout sprite plane.
    for ring_index, direction in ((0, -1), (len(rings) - 1, 1)):
        base = ring_index * 24
        center = len(surface.vertices)
        surface.vertices.append(np.mean(rings[ring_index], axis=0))
        surface.uv.append((.5, .5))
        for i in range(24):
            face = (center, base + i, base + (i + 1) % 24)
            surface.faces.append(face if direction > 0 else face[::-1])
            surface.materials.append("source_upperbody")
            surface.parts.append(name)
    return surface


def body_transform(t):
    pivot = unproject(197, 239, 0)
    angle = .022 * math.cos(math.tau * t)
    def transform(point):
        x, y, z = np.asarray(point) - pivot
        return pivot + np.array((math.cos(angle) * x - math.sin(angle) * y,
                                 math.sin(angle) * x + math.cos(angle) * y, z))
    return transform


def author(t, unit, landmarks, approach):
    old_mesh, old_joints = original.author(t, unit == "veteranIceHunter")
    leg_names = ("thigh", "knee_cap", "shaped_calf_boot", "boot_cuff", "foot_instep", "toe", "boot_binding")
    mesh = subset(old_mesh, lambda name: any(name.startswith(side + "_" + part)
                  for side in ("near", "far") for part in leg_names))
    original_leg_vertices = np.asarray(mesh.vertices).copy()
    move = body_transform(t)
    for key, depth, radius in (("head", .12, .155), ("torso", .035, .165)):
        rest = rings_surface(landmarks[key], "fitted_" + key + "_closed_surface", depth, radius)
        append_reference(mesh, rest, posed_copy(rest, move))

    cape = original.Surface()
    rings = []
    for j, (y, left, right) in enumerate(landmarks["cape"]):
        rings.append([unproject(left + (right - left) * i / 12, y,
                                -.18 + .018 * math.cos(i * math.pi / 2)) for i in range(13)])
    cape.patch(rings, "source_upperbody", "source_matched_folded_mantle", close=False)
    def cape_move(point):
        result = move(point)
        falloff = max(0, (project(point)[1] - 212) / 30)
        return result + RIGHT * (.012 * math.sin(math.tau * t) * falloff)
    append_reference(mesh, cape, posed_copy(cape, cape_move))

    joints = copy.deepcopy(old_joints)
    joints["arms"] = {}
    for side in ("far", "near"):
        depth = .25 if side == "near" else -.015
        s, e, w = [unproject(*xy, depth) for xy in landmarks[side + "_arm"]]
        length_a, length_b = float(np.linalg.norm(e - s)), float(np.linalg.norm(w - e))
        shoulder = move(s)
        wrist = move(w) + RIGHT * ((.7 if side == "near" else .22) * math.cos(math.tau * t) / SCALE)
        elbow = original.ik(shoulder, wrist, length_a, length_b, e - (s + w) / 2)
        rest, posed = original.Surface(), original.Surface()
        for model, a, b, c in ((rest, s, e, w), (posed, shoulder, elbow, wrist)):
            model.limb(a, b, .072, .058, "source_upperbody", side + "_actual_upper_arm")
            model.limb(b, c, .059, .047, "source_upperbody", side + "_actual_forearm")
            model.oval(c, (.050, .044, .061), "source_upperbody", side + "_actual_hand")
        append_reference(mesh, rest, posed)
        joints["arms"][side] = {"shoulder": shoulder.tolist(), "elbow": elbow.tolist(),
                                "wrist": wrist.tolist(), "upper_length": length_a, "fore_length": length_b}
        if side == "far":
            rest_bow_hand, actual_bow_hand = w, wrist
    bow = original.Surface()
    bow_points = [unproject(*xy, -.015) for xy in landmarks["bow"]]
    bow.cord(bow_points, .014, "source_upperbody", "reference_fitted_actual_bow")
    bow.cord([bow_points[0], bow_points[-1]], .003, "source_upperbody", "actual_bow_string")
    delta = actual_bow_hand - rest_bow_hand
    append_reference(mesh, bow, posed_copy(bow, lambda point: point + delta))
    handle = bow_points[landmarks["bow_grip_index"]] + delta
    joints["bow"] = {"handle": handle.tolist(), "hand_side": "far",
                     "attachment_error": float(np.linalg.norm(handle - actual_bow_hand))}

    quiver = original.Surface()
    points = [unproject(*xy, -.12) for xy in landmarks["quiver"]]
    quiver.limb(*points, .068, .082, "source_upperbody", "reference_fitted_quiver")
    for tip in landmarks["arrow_tips"]:
        top = unproject(*tip, -.10)
        quiver.limb(points[0], top, .006, .006, "source_upperbody", "actual_arrow_shaft")
        quiver.oval(top, (.022, .012, .045), "source_upperbody", "actual_arrow_fletching", sides=8, rows=5)
    append_reference(mesh, quiver, posed_copy(quiver, move))
    joints["fit_camera"] = {"right": RIGHT.tolist(), "up": UP.tolist(), "view": VIEW.tolist(), "scale": SCALE}
    joints["old_leg_vertices_unchanged"] = bool(np.array_equal(np.asarray(mesh.vertices)[:len(original_leg_vertices)], original_leg_vertices))
    return mesh, joints


def raster(mesh, materials):
    crop = (150, 180, 245, 280)
    ss, width, height = 3, 285, 300
    vertices = np.asarray(mesh.vertices)
    screen = np.stack((197 + vertices @ RIGHT * SCALE, 266 - vertices @ UP * SCALE,
                       vertices @ VIEW), axis=1)
    screen[:, :2] = (screen[:, :2] - crop[:2]) * ss
    uv = np.asarray(mesh.uv)
    rgba = np.zeros((height, width, 4), np.uint8)
    zbuffer = np.full((height, width), -np.inf)
    for face, matname in zip(mesh.faces, mesh.materials):
        ids = list(face)
        tri = screen[ids]
        lo = np.maximum(np.floor(tri[:, :2].min(0)).astype(int), 0)
        hi = np.minimum(np.ceil(tri[:, :2].max(0)).astype(int), (width - 1, height - 1))
        if np.any(hi < lo):
            continue
        a, b, c = tri
        determinant = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(determinant) < 1e-8:
            continue
        yy, xx = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        wa = ((b[1] - c[1]) * (xx + .5 - c[0]) + (c[0] - b[0]) * (yy + .5 - c[1])) / determinant
        wb = ((c[1] - a[1]) * (xx + .5 - c[0]) + (a[0] - c[0]) * (yy + .5 - c[1])) / determinant
        wc = 1 - wa - wb
        z = wa * a[2] + wb * b[2] + wc * c[2]
        zdest = zbuffer[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        visible = (wa >= 0) & (wb >= 0) & (wc >= 0) & (z > zdest)
        if not visible.any():
            continue
        weights = np.stack((wa[visible], wb[visible], wc[visible]), axis=1)
        coords = weights @ uv[ids]
        tex = materials[matname]["pixels"]
        if matname == "source_upperbody":
            tx = np.clip(coords[:, 0] * tex.shape[1], 0, tex.shape[1] - 1).astype(int)
            ty = np.clip((1 - coords[:, 1]) * tex.shape[0], 0, tex.shape[0] - 1).astype(int)
            # Own painted lighting remains baked into the transferred material.
            color = tex[ty, tx]
        else:
            tx = ((coords[:, 0] * 2 % 1) * 63).astype(int)
            ty = ((coords[:, 1] * 2 % 1) * 63).astype(int)
            normal = original.normalize(np.cross(vertices[ids[1]] - vertices[ids[0]], vertices[ids[2]] - vertices[ids[0]]))
            if normal @ VIEW < 0:
                normal = -normal
            shade = .54 + .68 * max(0, normal @ original.LIGHT)
            color = tex[ty, tx] * shade
        dest = rgba[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        dest[visible, :3] = np.clip(color, 0, 255).astype(np.uint8)
        dest[visible, 3] = 255
        zdest[visible] = z[visible]
    tile = Image.fromarray(rgba).resize((95, 100), Image.Resampling.LANCZOS)
    image = Image.new("RGBA", (450, 400))
    image.alpha_composite(tile, crop[:2])
    return image


def run(unit, approach):
    start = time.perf_counter()
    root = original.candidate_root(unit) / ("identity-fit-approach" + str(approach))
    root.mkdir(exist_ok=False)
    report = REPORT / unit / root.name
    report.mkdir(parents=True, exist_ok=False)
    configpath = HERE / "identity-fit-landmarks.json"
    landmarks = json.loads(configpath.read_text(encoding="utf-8"))[unit]
    reference = PROJECT / "assets/source/creatures" / unit / "registered-v3/native/g02-f000.png"
    native = Image.open(reference).convert("RGBA")
    source_texture = fill_texture(native.crop(TEXTURE_CROP))
    Image.fromarray(source_texture.astype(np.uint8)).save(root / "source-upperbody-rgb.png")
    config = json.loads((original.candidate_root(unit) / "cohort.json").read_text())
    material = original.materials(config, root)
    material["source_upperbody"] = {"pixels": source_texture}
    with (root / "materials.mtl").open("a", encoding="ascii") as file:
        file.write("\nnewmtl source_upperbody\nKd 1 1 1\nmap_Kd source-upperbody-rgb.png\n")
    frames, records = [], []
    for phase in (0, 3):
        mesh, joints = author(phase / 6, unit, landmarks, approach)
        output = root / f"g00-f{phase:03d}.png"
        raster(mesh, material).save(output)
        mesh.export_obj(root / f"phase{phase}.obj")
        records.append({"phase": phase, "png": output.relative_to(PROJECT).as_posix(),
                        "sha256": original.digest(output), "mesh_sha256": original.digest(root / f"phase{phase}.obj"),
                        "triangles": len(mesh.faces), "joints": joints})
        frames.append(output)
    original.contact_sheet(unit, frames, report / "selected-idle-versus-identity-fit-native.png", root.name)
    receipt = {"unit": unit, "approach": approach, "status": "built-unreviewed", "selected": False,
               "production_ready": False, "human_visual_approval": False, "independent_review_pass": False,
               "canvas": [450,400], "pivot": [197,266], "only_contact_phases_rendered": [0,3],
               "method": "Actual closed cross-section head/torso volumes, draped mantle, re-IKed upper-arm surfaces and fitted bow/quiver; projective UV from own painted upperbody only. Legs remain the proven actual v6 geometry. No texture alpha clips geometry or fakes foot contact.",
               "source_texture_crop": list(TEXTURE_CROP), "seconds": time.perf_counter() - start,
               "inputs": {reference.relative_to(PROJECT).as_posix(): original.digest(reference),
                          configpath.relative_to(PROJECT).as_posix(): original.digest(configpath),
                          Path(__file__).relative_to(PROJECT).as_posix(): original.digest(Path(__file__)),
                          Path(original.__file__).relative_to(PROJECT).as_posix(): original.digest(original.__file__)},
               "landmarks": landmarks, "phases": records,
               "limitations": ["One-view baked material transfer, not a fully textured multi-view production sculpt", "Contact identity and arm/body UV seams require independent image inspection", "No cycle expansion or selection from a similarity score"]}
    for folder in (root, report):
        (folder / "receipt.json").write_text(original.encoded(receipt), encoding="utf-8")
    (root / "authoring-inputs.json").write_text(original.encoded({"helper_source": Path(__file__).read_text(),
                                                                "landmarks": landmarks}), encoding="utf-8")
    print(json.dumps({"unit": unit, "approach": approach, "seconds": receipt["seconds"],
                      "receipt_sha256": original.digest(root / "receipt.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("unit", choices=original.UNITS)
    parser.add_argument("approach", type=int, choices=(1,2))
    args = parser.parse_args()
    run(args.unit, args.approach)
