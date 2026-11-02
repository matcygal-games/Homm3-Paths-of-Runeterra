"""Technical whole-component isolation reused from a prior clean2D helper. No artwork generation."""
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
def alpha_components(alpha, threshold=128, minimum=500):
    """Four-connected run-length components, with exact opaque support runs."""
    parents, runs, previous = [], [], []
    def find(label):
        while parents[label] != label:
            parents[label] = parents[parents[label]]
            label = parents[label]
        return label
    def union(left, right):
        parents[find(right)] = find(left)
    for y, row in enumerate(alpha >= threshold):
        edge = np.diff(np.pad(row.astype(np.int8), (1, 1)))
        current = []
        for start, end in zip(np.where(edge == 1)[0], np.where(edge == -1)[0]):
            label = len(parents)
            parents.append(label)
            start, end = int(start), int(end)
            for old_start, old_end, old_label in previous:
                if old_end > start and end > old_start:
                    union(label, old_label)
            current.append((start, end, label))
            runs.append((y, start, end, label))
        previous = current
    grouped = {}
    for y, start, end, label in runs:
        group = grouped.setdefault(find(label), {"pixels": 0, "box": [start, y, end, y + 1], "runs": []})
        group["pixels"] += end - start
        box = group["box"]
        group["box"] = [min(box[0], start), min(box[1], y), max(box[2], end), max(box[3], y + 1)]
        group["runs"].append((y, start, end))
    return [group for group in grouped.values() if group["pixels"] >= minimum]

def ordered_components(image, columns, rows):
    array = np.asarray(image)
    components = alpha_components(array[:, :, 3])
    if len(components) != columns * rows:
        raise ValueError(f"Whole-figure component count {len(components)} != {columns * rows}; merged/missing body requires new painting")
    by_row = [[] for _ in range(rows)]
    for component in components:
        box = component["box"]
        if box[0] <= 1 or box[1] <= 1 or box[2] >= image.width - 1 or box[3] >= image.height - 1:
            raise ValueError("Whole figure intersects canvas boundary: " + str(box))
        row = min(rows - 1, int(((box[1] + box[3]) / 2) / (image.height / rows)))
        by_row[row].append(component)
    if any(len(row) != columns for row in by_row):
        raise ValueError("Whole-figure intended row counts disagree: " + str([len(row) for row in by_row]))
    return [component for row in by_row for component in sorted(row, key=lambda component: component["box"][0])]

def isolate(image, component):
    """Retain component RGB/alpha and four-pixel AA fringe; exclude neighbors."""
    box = component["box"]
    crop_box = [max(0, box[0] - 4), max(0, box[1] - 4), min(image.width, box[2] + 4), min(image.height, box[3] + 4)]
    core = Image.new("L", (crop_box[2] - crop_box[0], crop_box[3] - crop_box[1]), 0)
    draw = ImageDraw.Draw(core)
    for y, start, end in component["runs"]:
        draw.line((start - crop_box[0], y - crop_box[1], end - crop_box[0] - 1, y - crop_box[1]), fill=255)
    support = core.filter(ImageFilter.MaxFilter(9))
    crop = image.crop(crop_box)
    array = np.array(crop)
    keep = np.asarray(support) > 0
    # Other opaque figures must never be captured by a padded rectangular crop.
    local_core = np.asarray(core) > 0
    other_core = (array[:, :, 3] >= 128) & ~local_core
    if np.any(other_core):
        # Separate low-alpha fringes may meet although bodies are independent.
        # Attribute AA to the nearest opaque component, never a grid rectangle.
        own_distance = np.full(local_core.shape, 5, dtype=np.uint8)
        other_distance = np.full(local_core.shape, 5, dtype=np.uint8)
        own_distance[local_core] = 0
        other_distance[other_core] = 0
        growing_own = core
        growing_other = Image.fromarray(other_core.astype(np.uint8) * 255)
        for distance in range(1, 5):
            growing_own = growing_own.filter(ImageFilter.MaxFilter(3))
            growing_other = growing_other.filter(ImageFilter.MaxFilter(3))
            own_distance[(np.asarray(growing_own) > 0) & (own_distance == 5)] = distance
            other_distance[(np.asarray(growing_other) > 0) & (other_distance == 5)] = distance
        keep &= (own_distance < other_distance) | local_core
        support = Image.fromarray(keep.astype(np.uint8) * 255)
    array[~keep] = 0
    array[array[:, :, 3] == 0] = 0  # Hidden gutter RGB is not painted content.
    return Image.fromarray(array), support, crop_box

def support_x(component):
    box = component["box"]
    strips = [(start, end) for y, start, end in component["runs"] if y >= box[3] - max(3, round((box[3] - box[1]) * .04))]
    return (min(start for start, _ in strips) + max(end for _, end in strips) - 1) / 2
