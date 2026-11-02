"""Bounded crest-aware icon registration; no production or stage writes."""
from pathlib import Path
import hashlib
import json
from PIL import Image


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(project, item):
    name = item['path']
    if not isinstance(name, str) or ':' in name or '\\' in name or any(p in ('', '.', '..') for p in name.split('/')):
        raise ValueError('Unsafe contract path')
    path = (project / name).resolve()
    if not path.is_relative_to(project.resolve()) or not path.is_file() or sha(path) != item['sha256']:
        raise ValueError('Missing/stale registration input: ' + name)
    return path


def load_roles(project, contract):
    """Validate local, hash-bound physical mask -> receipt -> plan -> source links."""
    roles = {}
    for unit, entries in contract['units'].items():
        roles[unit] = {}
        for role, entry in entries.items():
            paths = {key: checked(project, value) for key, value in entry.items() if isinstance(value, dict) and 'path' in value}
            plan = json.loads(paths['plan'].read_text())
            receipt = json.loads(paths['receipt'].read_text())
            match = [e for e in plan['attachments'] if e['candidate'] == entry['candidate']['path']]
            records = [e for e in receipt['records'] if e['candidate'] == entry['candidate']['path']]
            if len(match) != 1 or len(records) != 1:
                raise ValueError('Ambiguous physical context')
            authored, actual = match[0], records[0]
            for key, name in [('source', 'parent'), ('mask', 'mask'), ('candidate', 'candidate')]:
                if actual[key] != entry[name]['path'] or actual[key + '_sha256'] != entry[name]['sha256'] or authored[key] != actual[key]:
                    raise ValueError('Physical source/receipt link differs')
            if authored['source_sha256'] != entry['parent']['sha256']:
                raise ValueError('Parent hash differs')
            if receipt['plan_sha256'] != entry['plan']['sha256'] or receipt['plan'] != entry['plan']['path']:
                raise ValueError('Plan/receipt link differs')
            if receipt['producer'] != entry['composer']['path'] or receipt['producer_sha256'] != entry['composer']['sha256']:
                raise ValueError('Composer/receipt link differs')
            replay = paths['replay'].read_text()
            # Full replay closure remains the frozen original packet; this contract pins it.
            if not replay or not actual['original_alpha_exact'] or not actual['outside_attachment_RGBA_exact']:
                raise ValueError('Unverified physical source')
            closure = {e['path']: e['sha256'] for e in json.loads(paths['replay_inputs'].read_text())['dependencies']}
            for name in ('parent', 'candidate', 'mask', 'plan', 'receipt', 'composer'):
                if closure.get(entry[name]['path']) != entry[name]['sha256']:
                    raise ValueError('Role absent from frozen replay closure: ' + name)
            active = json.loads(paths['active_recipe'].read_text())
            if active['source'] != entry['candidate']['path'] or active['source_sha256'] != entry['candidate']['sha256'] or active.get('fit') != 'exact' or active.get('size') != [64, 64]:
                raise ValueError('Active recipe no longer selects exact checked icon')
            parent = Image.open(paths['parent']).convert('RGBA')
            mask = Image.open(paths['mask']).convert('L')
            if parent.size != (64, 64) or mask.size != parent.size or set(mask.tobytes()) - {0, 255}:
                raise ValueError('Invalid physical mask')
            roles[unit][role] = {'parent': parent, 'mask': mask, 'entry': entry}
    return roles


def validate_pair(images, roles):
    """Exact alpha/root and body preservation; only pinned physical material can differ."""
    for role in ('attackLeft', 'attackRight'):
        im, parent, mask = images[role], roles[role]['parent'], roles[role]['mask']
        if im.size != (64, 64):
            raise ValueError('Icon canvas changed')
        for x, y in ((x, y) for y in range(64) for x in range(64)):
            actual, before, allowed = im.getpixel((x, y)), parent.getpixel((x, y)), mask.getpixel((x, y))
            if actual[3] != before[3]:
                raise ValueError('Original alpha/root changed')
            if not allowed and actual != before:
                raise ValueError('Body RGBA outside physical crest mask changed')
            if allowed and before[3] < 248:
                raise ValueError('Mask extends outside opaque physical carrier')
    left, right = images['attackLeft'], images['attackRight']
    lp, rp = roles['attackLeft']['parent'], roles['attackRight']['parent']
    lm, rm = roles['attackLeft']['mask'], roles['attackRight']['mask']
    for y in range(64):
        for x in range(64):
            sx = 96 - x
            old = rp.getpixel((sx, y)) if 0 <= sx < 64 else (0, 0, 0, 0)
            base = lp.getpixel((x, y))
            if base[3] != old[3] or (old[3] and base != old):
                raise ValueError('Original before-body no longer mirrors about native x=48')
            actual = left.getpixel((x, y))
            reflected = right.getpixel((sx, y)) if 0 <= sx < 64 else (0, 0, 0, 0)
            union = lm.getpixel((x, y)) or (0 <= sx < 64 and rm.getpixel((sx, y)))
            if actual[3] != reflected[3]:
                raise ValueError('Whole-image alpha does not mirror about native x=48')
            if old[3] and not union and actual != reflected:
                raise ValueError('Mirrored body RGB differs outside physical mask union')
    return True
