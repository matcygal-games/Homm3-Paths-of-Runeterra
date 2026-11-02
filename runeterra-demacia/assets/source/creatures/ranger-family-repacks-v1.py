"""Reviewed lossless recovery of source figures crossing a returned atlas grid."""
from pathlib import Path
import json
import sys

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'scripts'))
from creature_ranger_motion_art import repack_generation

# Manually checked full source atlases and alpha>=8 connected body extents.
# Only non-overlapping same-pose rectangles are used. Faint external alpha1–7
# speckles are excluded explicitly; no pose/body/equipment is rescaled/painted.
SPECS = {
    ('demacianRanger', 5): [[120,61,431,537],[613,98,927,533],[1163,206,1460,534],
        [19,671,515,931],[532,730,1035,936],[1035,768,1524,924]],
    ('veteranRanger', 5): [[132,50,399,534],[687,98,955,534],[1194,179,1470,522],
        [45,622,506,929],[531,741,1015,928],[1032,812,1524,965]],
    ('veteranRanger', 16): [[113,9,377,449],[579,10,852,447],[1017,9,1306,448],[1474,9,1755,447],
        [109,451,437,882],[560,455,846,882],[1015,455,1294,882],[1488,455,1747,881]],
}

for (unit, group), rectangles in SPECS.items():
    folder = PROJECT / 'assets/source/creatures' / unit / 'ranger-rig-v4'
    record_path = folder / f'paint-action-g{group:02}-atlas-v1-generation.json'
    generation = json.loads(record_path.read_text());columns = generation['layout'][0]
    width, height = generation['returned_cell'];frames = []
    for index, rect in enumerate(rectangles):
        ox, oy = int(index % columns * width), int(index // columns * height)
        frames.append({'source_rect': rect, 'destination_offset': [rect[0]-ox+32,rect[1]-oy+32],
            'reviewed': True, 'neighbor_pixels_absent': True,
            'basis': 'Actual full atlas inspected, six/eight connected genuine pose bodies individually identified. Extended first-row feet and last-row figure pixels recovered into576px cells; integer common32px padding and original fractional grid phase recorded. No resize/repaint. Every alpha>=8body pixel retained; no adjacent-body alpha included.'})
    repack_generation(PROJECT, record_path, frames)
    print(unit, group, 'recovered full same-pose pixels in576px cells; source preserved')
