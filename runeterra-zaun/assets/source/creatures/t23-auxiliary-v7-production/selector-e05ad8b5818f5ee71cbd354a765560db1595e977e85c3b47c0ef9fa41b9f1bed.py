"""Zaun T5/T7 technical painted-atlas selection, adapted from own Freljord tooling.

This is technical alpha segmentation, not image synthesis: it never warps
limbs, invents a pose or fills missing paint. Ambiguous touching bodies fail.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np
from PIL import Image


class AtlasError(ValueError):
    pass


@dataclass(frozen=True)
class Component:
    identifier: int
    bbox: tuple[int, int, int, int]
    area: int
    centroid: tuple[float, float]


def components(image: Image.Image, *, threshold: int = 128) -> tuple[np.ndarray, list[Component]]:
    """Eight-connected opaque components via scanline runs and union-find."""
    if not 1 <= threshold <= 255:
        raise AtlasError("An explicit nonzero alpha threshold is required")
    alpha = np.asarray(image.convert("RGBA"))[:, :, 3]
    parent = [0]
    runs: list[tuple[int, int, int, int]] = []
    previous: list[tuple[int, int, int]] = []

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for y in range(alpha.shape[0]):
        opaque = alpha[y] >= threshold
        changes = np.diff(np.r_[False, opaque, False].astype(np.int8))
        starts = np.flatnonzero(changes == 1)
        ends = np.flatnonzero(changes == -1)
        current = []
        first_previous = 0
        for start, end in zip(starts.tolist(), ends.tolist()):
            identifier = len(parent)
            parent.append(identifier)
            while first_previous < len(previous) and previous[first_previous][1] < start:
                first_previous += 1
            pos = first_previous
            while pos < len(previous) and previous[pos][0] <= end:
                previous_start, previous_end, other = previous[pos]
                if previous_end >= start:
                    a, b = find(identifier), find(other)
                    if a != b:
                        parent[max(a, b)] = min(a, b)
                pos += 1
            current.append((start, end, identifier))
            runs.append((y, start, end, identifier))
        previous = current
    labels = np.zeros(alpha.shape, dtype=np.int32)
    sums: dict[int, list[float]] = {}
    for y, start, end, identifier in runs:
        identifier = find(identifier)
        labels[y, start:end] = identifier
        length = end - start
        if identifier not in sums:
            sums[identifier] = [start, y, end, y + 1, 0, 0, 0]
        row = sums[identifier]
        row[0] = min(row[0], start); row[1] = min(row[1], y)
        row[2] = max(row[2], end); row[3] = max(row[3], y + 1)
        row[4] += length
        row[5] += (start + end - 1) * length / 2
        row[6] += y * length
    found = [Component(identifier, tuple(int(n) for n in data[:4]), int(data[4]),
                       (data[5] / data[4], data[6] / data[4])) for identifier, data in sums.items()]
    return labels, sorted(found, key=lambda item: (-item.area, item.identifier))


def assign_rows(found: Sequence[Component], row_counts: Sequence[int], *, minimum_area: int = 600) -> tuple[list[list[Component]], list[Component]]:
    """Require exactly the declared painted bodies; do not pad missing cells."""
    if not row_counts or any(type(count) is not int or count <= 0 for count in row_counts):
        raise AtlasError("Explicit positive row pose counts required")
    main = [item for item in found if item.area >= minimum_area]
    extra = [item for item in found if item.area < minimum_area]
    if len(main) != sum(row_counts):
        raise AtlasError(f"Expected {sum(row_counts)} distinct painted bodies; found {len(main)}. Touching, missing or split bodies require explicit repair/review.")
    ordered = sorted(main, key=lambda item: item.centroid[1])
    rows = []
    position = 0
    for count in row_counts:
        row = sorted(ordered[position:position + count], key=lambda item: item.centroid[0])
        position += count
        rows.append(row)
    # Adjacent row centers must be separated; uncertain global ordering fails.
    for upper, lower in zip(rows, rows[1:]):
        if max(item.centroid[1] for item in upper) >= min(item.centroid[1] for item in lower):
            raise AtlasError("Painted row centers overlap; row semantics cannot be inferred safely")
    return rows, extra


def ownership(labels: np.ndarray, mains: Sequence[Component], extras: Sequence[Component]) -> np.ndarray:
    """Partition real atlas cells by distance from their opaque painted bodies.

    This map selects cells only. It never changes the RGBA values inside a cell.
    Detached small painted parts seed their unambiguous nearest body. A released
    projectile may be an explicitly separate main and is then excluded from the
    creature cell, as the native missile animation owns that object.
    """
    ids={item.identifier for item in mains}
    selected=np.where(np.isin(labels,list(ids)),labels,0).astype(np.int32)
    for fragment in extras:
        if fragment.area<3: continue
        distances=[]
        for candidate in mains:
            a,b=fragment.bbox,candidate.bbox
            dx=max(0,a[0]-b[2],b[0]-a[2]);dy=max(0,a[1]-b[3],b[1]-a[3])
            distances.append((math.hypot(dx,dy),candidate.identifier))
        distances.sort()
        if distances[0][0]<=6:
            if len(distances)>1 and distances[1][0]-distances[0][0]<2:
                raise AtlasError("Detached painted fragment has ambiguous neighboring bodies")
            selected[labels==fragment.identifier]=distances[0][1]
    # A four-neighbor distance partition, deterministic on equal distances.
    # All original body seeds are immutable. This is not an alpha-rematting pass.
    sentinel=np.iinfo(np.int32).max
    for _ in range(sum(labels.shape)):
        missing=selected==0
        if not np.any(missing): return selected
        candidates=np.full(labels.shape,sentinel,dtype=np.int32)
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
            neighbor=np.roll(selected,(dy,dx),(0,1))
            if dy<0: neighbor[-1,:]=0
            if dy>0: neighbor[0,:]=0
            if dx<0: neighbor[:,-1]=0
            if dx>0: neighbor[:,0]=0
            candidates=np.minimum(candidates,np.where(neighbor>0,neighbor,sentinel))
        growth=missing & (candidates!=sentinel)
        if not np.any(growth): raise AtlasError("Atlas contains no painted body seeds")
        selected[growth]=candidates[growth]
    raise AtlasError("Atlas cell partition did not converge")


def subject(image: Image.Image, labels: np.ndarray, main: Component, extras: Sequence[Component], all_main: Sequence[Component], *, padding: int = 3, cell_ownership: np.ndarray | None = None) -> tuple[Image.Image, dict]:
    """Select a nonrectangular atlas cell, preserving every selected RGBA byte.

    The distance partition is a technical atlas cut. It does not use alpha as a
    replacement matte: all antialias, painted shadow and haze inside the chosen
    region are retained. Touching opaque figures cannot be separated and fail in
    assign_rows. Boundary evidence remains a visual review input, not acceptance.
    """
    if cell_ownership is None: cell_ownership=ownership(labels,all_main,extras)
    rgba=np.array(image.convert("RGBA"))
    chosen=cell_ownership==main.identifier
    # Excluding another atlas cell is a selection, never a recolor/alpha cleanup.
    rgba[~chosen]=0
    points=np.argwhere(chosen & (rgba[:,:,3]>0))
    if not len(points): raise AtlasError("Selected real painted subject is empty")
    y0,x0=points.min(axis=0);y1,x1=points.max(axis=0)+1
    bbox=(max(0,int(x0)-padding),max(0,int(y0)-padding),min(image.width,int(x1)+padding),min(image.height,int(y1)+padding))
    boundary=np.zeros(chosen.shape,dtype=bool)
    for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
        shifted=np.roll(chosen,(dy,dx),(0,1))
        boundary |= chosen & ~shifted
    # A portrait's shoulders may intentionally leave the original image; that
    # original edge is not a cut through another atlas cell. Record it
    # separately rather than treating numpy roll wraparound as a neighbour.
    boundary[0,:]=False;boundary[-1,:]=False
    boundary[:,0]=False;boundary[:,-1]=False
    alpha=np.asarray(image.convert("RGBA"))[:,:,3]
    max_boundary=int(alpha[boundary].max()) if np.any(boundary) else 0
    if max_boundary>=128: raise AtlasError("Atlas cut crosses opaque body paint; focused source repair required")
    crop=Image.fromarray(rgba).crop(bbox)
    touches_source_edge=main.bbox[0]==0 or main.bbox[1]==0 or main.bbox[2]==image.width or main.bbox[3]==image.height
    return crop,{"opaque_component":main.identifier,"source_bbox":list(bbox),"source_opaque_bbox":list(main.bbox),"source_opaque_area":main.area,"source_centroid":list(main.centroid),"alpha_threshold_for_analysis_only":128,"cell_boundary_max_alpha":max_boundary,"opaque_touches_source_edge":touches_source_edge,"painted_rgba_preserved":True,"technical_selection":"nearest-opaque-body atlas cell, original RGBA retained inside cell"}


def register(part: Image.Image, evidence: dict, *, scale: float, canvas: tuple[int,int]=(450,400), pivot: tuple[int,int]=(197,266), floating: bool=False, anchor: tuple[float,float] | None=None) -> Image.Image:
    """One measured camera scale; never fit each pose to a target body height."""
    if not 0<scale<=4: raise AtlasError("Explicit positive uniform camera scale required")
    bbox=evidence["source_bbox"];opaque=evidence["source_opaque_bbox"]
    anchor_x,anchor_y=anchor if anchor is not None else (evidence["source_centroid"][0],evidence["source_centroid"][1] if floating else opaque[3])
    target_y=pivot[1]-22 if floating else pivot[1]
    size=(max(1,round(part.width*scale)),max(1,round(part.height*scale)))
    result=Image.new("RGBA",canvas)
    origin=(round(pivot[0]-(anchor_x-bbox[0])*scale),round(target_y-(anchor_y-bbox[1])*scale))
    projected=(origin[0]+(opaque[0]-bbox[0])*scale,origin[1]+(opaque[1]-bbox[1])*scale,origin[0]+(opaque[2]-bbox[0])*scale,origin[1]+(opaque[3]-bbox[1])*scale)
    if min(projected[:2])<0 or projected[2]>canvas[0] or projected[3]>canvas[1]:
        raise AtlasError("Registered native canvas would clip real opaque pose paint")
    result.alpha_composite(part.resize(size,Image.Resampling.LANCZOS),origin)
    return result
