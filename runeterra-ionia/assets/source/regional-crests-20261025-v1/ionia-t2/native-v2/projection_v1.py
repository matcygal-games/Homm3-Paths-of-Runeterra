"""Pure fixed affine projection from current Ionia native consumer helper; no artwork production."""
from PIL import Image
CANVAS=(96,64)
ANCHOR=(80,60)
def affine(pivot, scale, mirrored=False, anchor=ANCHOR):
    """Pillow inverse mapping; source pivot maps exactly to native anchor."""
    sx = -scale if mirrored else scale
    return (1 / sx, 0, pivot[0] - anchor[0] / sx,
            0, 1 / scale, pivot[1] - anchor[1] / scale)

def project(image, pivot, scale, mirrored=False, canvas=CANVAS, anchor=ANCHOR):
    return image.convert('RGBA').transform(canvas, Image.Transform.AFFINE,
        affine(pivot, scale, mirrored, anchor), Image.Resampling.BICUBIC)

def bounds(image, threshold=8):
    return image.getchannel('A').point(lambda a: 255 if a >= threshold else 0).getbbox()

def measure(image, pivot, scale, mirrored=False):
    """Render into oversized audit canvas, measure every excluded alpha pixel."""
    pad = 128
    expanded = project(image, pivot, scale, mirrored,
        (CANVAS[0] + pad * 2, CANVAS[1] + pad * 2),
        (ANCHOR[0] + pad, ANCHOR[1] + pad))
    a = expanded.getchannel('A')
    total = sum(v >= 8 for v in a.tobytes())
    inside = a.crop((pad, pad, pad + CANVAS[0], pad + CANVAS[1]))
    b = bounds(expanded)
    return {'source_alpha8_bbox': bounds(image),
        'projected_alpha8_bbox_unclipped': [v - pad for v in b],
        'opaque_pixels_outside_canvas': total - sum(v >= 8 for v in inside.tobytes()),
        'projected_opaque_pixels': total}
