"""Private fixed-camera renderer; explicit baked part paint, no double lighting.

Unedited source_upperbody retains the old sampler exactly. New opaque UV islands
use clamped bilinear sampling; geometry alone determines alpha and contact.
"""
import numpy as np
from PIL import Image


def render(mesh, materials, fit, original):
    crop = (150, 180, 245, 280)
    ss, width, height = 3, 285, 300
    vertices = np.asarray(mesh.vertices)
    screen = np.stack((197 + vertices @ fit.RIGHT * fit.SCALE,
                       266 - vertices @ fit.UP * fit.SCALE,
                       vertices @ fit.VIEW), axis=1)
    screen[:, :2] = (screen[:, :2] - crop[:2]) * ss
    uv = np.asarray(mesh.uv)
    rgba = np.zeros((height, width, 4), np.uint8)
    zbuffer = np.full((height, width), -np.inf)
    for face, name in zip(mesh.faces, mesh.materials):
        ids = list(face)
        tri = screen[ids]
        lo = np.maximum(np.floor(tri[:, :2].min(0)).astype(int), 0)
        hi = np.minimum(np.ceil(tri[:, :2].max(0)).astype(int), (width-1, height-1))
        if np.any(hi < lo):
            continue
        a, b, c = tri
        determinant = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(determinant) < 1e-8:
            continue
        yy, xx = np.mgrid[lo[1]:hi[1]+1, lo[0]:hi[0]+1]
        wa = ((b[1]-c[1])*(xx+.5-c[0])+(c[0]-b[0])*(yy+.5-c[1]))/determinant
        wb = ((c[1]-a[1])*(xx+.5-c[0])+(a[0]-c[0])*(yy+.5-c[1]))/determinant
        wc = 1-wa-wb
        z = wa*a[2]+wb*b[2]+wc*c[2]
        zdest = zbuffer[lo[1]:hi[1]+1, lo[0]:hi[0]+1]
        visible = (wa >= 0) & (wb >= 0) & (wc >= 0) & (z > zdest)
        if not visible.any():
            continue
        coords = np.stack((wa[visible], wb[visible], wc[visible]), axis=1) @ uv[ids]
        spec = materials[name]
        tex = spec['pixels']
        if name == 'source_upperbody':
            tx = np.clip(coords[:, 0]*tex.shape[1], 0, tex.shape[1]-1).astype(int)
            ty = np.clip((1-coords[:, 1])*tex.shape[0], 0, tex.shape[0]-1).astype(int)
            color = tex[ty, tx]
        elif spec.get('baked'):
            x = np.clip(coords[:, 0], 0, 1)*(tex.shape[1]-1)
            y = (1-np.clip(coords[:, 1], 0, 1))*(tex.shape[0]-1)
            x0, y0 = x.astype(int), y.astype(int)
            x1, y1 = np.minimum(x0+1, tex.shape[1]-1), np.minimum(y0+1, tex.shape[0]-1)
            fx, fy = (x-x0)[:, None], (y-y0)[:, None]
            color = ((1-fx)*tex[y0, x0]+fx*tex[y0, x1])*(1-fy)+((1-fx)*tex[y1, x0]+fx*tex[y1, x1])*fy
        else:
            tx = ((coords[:, 0]*2 % 1)*63).astype(int)
            ty = ((coords[:, 1]*2 % 1)*63).astype(int)
            normal = original.normalize(np.cross(vertices[ids[1]]-vertices[ids[0]], vertices[ids[2]]-vertices[ids[0]]))
            if normal @ fit.VIEW < 0:
                normal = -normal
            color = tex[ty, tx]*(.54+.68*max(0, normal @ original.LIGHT))
        dest = rgba[lo[1]:hi[1]+1, lo[0]:hi[0]+1]
        dest[visible, :3] = np.clip(color, 0, 255).astype(np.uint8)
        dest[visible, 3] = 255
        zdest[visible] = z[visible]
    tile = Image.fromarray(rgba).resize((95, 100), Image.Resampling.LANCZOS)
    image = Image.new('RGBA', (450, 400))
    image.alpha_composite(tile, crop[:2])
    return image
