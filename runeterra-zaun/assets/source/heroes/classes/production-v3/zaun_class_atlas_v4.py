"""Technical preparation of genuine painted Zaun class action atlases.

This module never paints/recolours or fabricates poses. Each source pose is a
complete connected painting. Only integer crop/translation plus one shared
uniform scale per whole master are permitted. Recipes are written only through
an explicit separate handoff after native visual review by the coordinator.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / 'build/reports/art-implementation/20261021-class-completion-v3'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(alpha, threshold=64, min_area=100):
    """Find opaque painted bodies using run-length connected components.

    Alpha is inspected only, never rewritten. Tiny detached particles are not
    bodies; every crop retains the original alpha pixels inside its rectangle.
    """
    mask = np.asarray(alpha) >= threshold
    parents, boxes, areas, previous = [], [], [], []

    def find(n):
        while parents[n] != n:
            parents[n] = parents[parents[n]]
            n = parents[n]
        return n

    for y, row in enumerate(mask):
        d = np.diff(np.r_[False, row, False].astype(np.int8))
        starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        current = []
        k = 0
        for left, right in zip(starts.tolist(), ends.tolist()):
            label = len(parents)
            parents.append(label)
            boxes.append([left, y, right, y + 1])
            areas.append(right - left)
            while k < len(previous) and previous[k][1] < left:
                k += 1
            j = k
            while j < len(previous) and previous[j][0] <= right:
                root = find(previous[j][2])
                parents[root] = label
                j += 1
            current.append((left, right, label))
        previous = current
    totals = {}
    for n, box in enumerate(boxes):
        root = find(n)
        if root not in totals:
            totals[root] = [box[:], 0]
        b, count = totals[root]
        totals[root][0] = [min(b[0], box[0]), min(b[1], box[1]), max(b[2], box[2]), max(b[3], box[3])]
        totals[root][1] += areas[n]
    return sorted(({'box': b, 'area': area} for b, area in totals.values() if area >= min_area), key=lambda x: -x['area'])


def inspect_sources():
    saved = json.loads((REPORT / 'saved-masters-current.json').read_text())
    out = []
    for row in saved:
        path = PROJECT / row['saved_master']
        with Image.open(path) as im:
            cs = components(im.getchannel('A'))
        out.append({**row, 'components': cs})
    target = REPORT / 'component-inspection.json'
    target.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps([{'id': x['class_id'] + '-' + x['cohort'] + '-' + x['action'], 'bodies': len(x['components']), 'boxes': [c['box'] for c in x['components'][:12]]} for x in out]))


def order_bodies(cs, count, columns):
    if len(cs) != count:
        raise ValueError(f'Expected {count} independently isolated paintings, found {len(cs)}')
    rows = []
    # A centroid sort is stable even when the arm or horse head changes the top.
    pending = sorted(cs, key=lambda c: (c['box'][1] + c['box'][3]) / 2)
    while pending:
        row, pending = pending[:columns], pending[columns:]
        rows.extend(sorted(row, key=lambda c: c['box'][0]))
    return rows


def prepare_padded_defeat_guides():
    out = []
    for cid in ('zaunMachinist', 'zaunChemist'):
        for sex in ('battleMale', 'battleFemale'):
            root = PROJECT / 'assets/source/heroes/classes' / cid / sex / 'painted-v3-complete'
            source = root / 'raw/defeat.png'
            with Image.open(source) as im:
                im.load()
                bodies = order_bodies(components(im.getchannel('A')), 11, 3)
                scale = 360 / (bodies[0]['box'][3] - bodies[0]['box'][1])
                guide = Image.new('RGBA', (1536, 2048))
                pins = []
                for n, body in enumerate(bodies):
                    b = body['box']
                    if b[0] == 0 or b[1] == 0 or b[2] == im.width or b[3] == im.height:
                        raise ValueError(f'Body {n} touches source edge: {source}')
                    crop = im.crop(b)
                    crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.LANCZOS)
                    xy = ((n % 3) * 512 + 256 - crop.width // 2, (n // 3) * 512 + 440 - crop.height)
                    guide.alpha_composite(crop, xy)
                    pins.append({'pose': n, 'original_box': b, 'guide_xy': list(xy), 'uniform_scale': scale})
            path = root / 'raw/defeat-padded-input.png'
            guide.save(path)
            desc = {'source': source.relative_to(PROJECT).as_posix(), 'source_sha256': sha(source), 'output': path.relative_to(PROJECT).as_posix(), 'sha256': sha(path), 'method': 'Technical complete-pose crop/resampling and registration only; no painting, alpha change, recolouring, limb warp or invented pose. All poses use one uniform whole-master scale.', 'poses': pins}
            (root / 'raw/defeat-padded-input.json').write_text(json.dumps(desc, indent=2) + '\n')
            out.append(desc)
    (REPORT / 'padded-defeat-inputs.json').write_text(json.dumps(out, indent=2) + '\n')
    return out


def prepare_targeted_guides():
    out = []
    for cid, sex, action, count, columns, rows in (
        ('zaunMachinist', 'battleMale', 'cast-palette', 8, 4, 2),
        ('zaunMachinist', 'battleMale', 'victory-palette', 11, 3, 4),
        ('zaunChemist', 'battleMale', 'victory-palette', 11, 3, 4),
        ('zaunMachinist', 'battleFemale', 'cast-palette', 8, 4, 2),
        ('zaunChemist', 'battleMale', 'cast-palette', 8, 4, 2),
        ('zaunChemist', 'battleFemale', 'cast-palette', 8, 4, 2),
        ('zaunChemist', 'battleFemale', 'victory-palette', 11, 3, 4),
    ):
        root = PROJECT / 'assets/source/heroes/classes' / cid / sex / 'painted-v3-complete'
        source = root / 'raw' / (action + '.png')
        with Image.open(source) as im:
            im.load()
            bodies = order_bodies(components(im.getchannel('A')), count, columns)
            scale = 330 / (bodies[0]['box'][3] - bodies[0]['box'][1])
            guide = Image.new('RGBA', (columns * 512, rows * 512))
            pins = []
            for n, body in enumerate(bodies):
                b = body['box']
                crop = im.crop(b)
                crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.LANCZOS)
                xy = ((n % columns) * 512 + 256 - crop.width // 2, (n // columns) * 512 + 430 - crop.height)
                guide.alpha_composite(crop, xy)
                pins.append({'pose': n, 'original_box': b, 'guide_xy': list(xy), 'uniform_scale': scale, 'source_edge_contact': b[0] == 0 or b[1] == 0 or b[2] == im.width or b[3] == im.height})
        path = root / 'raw' / (action + '-spaced-input.png')
        guide.save(path)
        desc = {'source': source.relative_to(PROJECT).as_posix(), 'source_sha256': sha(source), 'output': path.relative_to(PROJECT).as_posix(), 'sha256': sha(path), 'method': 'Technical cropped/resampled own-painting layout only. Edge-contact parts explicitly require genuine painting repair; this guide is not a delivered asset.', 'poses': pins}
        (root / 'raw' / (action + '-spaced-input.json')).write_text(json.dumps(desc, indent=2) + '\n')
        out.append(desc)
    (REPORT / 'targeted-spaced-inputs.json').write_text(json.dumps(out, indent=2) + '\n')
    return out


def native_from_master(path: Path, count: int, columns: int, canvas=(150, 175), height=111, baseline=146, center=72):
    """Register actual painted poses with shared scale and measured hoof pivots.

    All poses in a master use the first quiet pose's uniform scale. The lower
    silhouette supplies translation/contact only; the animated arms/heads never
    resize or recentre the horse. This does not create animation from stills.
    """
    with Image.open(path) as im:
        im.load()
        bodies = order_bodies(components(im.getchannel('A'), threshold=64, min_area=4000), count, columns)
        first = bodies[0]['box']
        scale = height / (first[3] - first[1])
        frames, evidence = [], []
        for n, body in enumerate(bodies):
            b = body['box']
            if b[0] == 0 or b[1] == 0 or b[2] == im.width or b[3] == im.height:
                raise ValueError(f'Visible subject touches master edge: {path}: {n}: {b}')
            # Include antialiased margins while never cutting another body.
            cropbox = [max(0, b[0]-3), max(0, b[1]-3), min(im.width, b[2]+3), min(im.height, b[3]+3)]
            for other in bodies:
                if other is body:
                    continue
                q = other['box']
                if min(cropbox[2], q[2]) > max(cropbox[0], q[0]) and min(cropbox[3], q[3]) > max(cropbox[1], q[1]):
                    raise ValueError(f'Pose rectangle overlaps another painting: {path}: {n}')
            lowtop = b[1] + round((b[3]-b[1])*.7)
            low = im.getchannel('A').crop((b[0], lowtop, b[2], b[3])).point(lambda a: 255 if a>=64 else 0).getbbox()
            anchor = b[0] + (low[0]+low[2])/2
            crop = im.crop(cropbox)
            size = (round(crop.width*scale), round(crop.height*scale))
            xy = (round(center-(anchor-cropbox[0])*scale), round(baseline-(b[3]-cropbox[1])*scale))
            if xy[0] < 0 or xy[1] < 0 or xy[0]+size[0]>canvas[0] or xy[1]+size[1]>canvas[1]:
                raise ValueError(f'Uniform registered pose leaves native canvas: {path}: {n}')
            result = Image.new('RGBA', canvas)
            result.alpha_composite(crop.resize(size, Image.Resampling.LANCZOS), xy)
            frames.append(result)
            evidence.append({'pose': n, 'painted_body_box': b, 'complete_crop_box': cropbox, 'uniform_master_scale': scale, 'source_hoof_anchor': [anchor, b[3]], 'native_hoof_anchor': [center, baseline], 'native_translation': list(xy), 'native_resample_size': list(size), 'no_per_frame_stretch': True})
    return frames, evidence


def prepare_battles(only=None):
    out = []
    for cid in ('zaunMachinist', 'zaunChemist'):
        for sex in ('battleMale', 'battleFemale'):
            if only is not None and (cid, sex) != only:
                continue
            root = PROJECT / 'assets/source/heroes/classes' / cid / sex / 'painted-v3-complete'
            actions = [('idle-palette', 5, 3), ('defeat-spaced-palette', 11, 3), ('victory-palette-repaired' if sex=='battleMale' or cid=='zaunChemist' else 'victory-palette', 11, 3), ('cast-palette-repaired', 8, 4)]
            all_groups, masters = [], []
            frames_by_group = {}
            for action, count, columns in actions:
                path = root / 'raw' / (action+'.png')
                provenance = json.loads((root / 'raw' / (action+'-generation.json')).read_text())
                if provenance['source_sha256'] != sha(path):
                    raise ValueError(f'Master source pin changed: {path}')
                frames, registration = native_from_master(path, count, columns)
                if action == 'idle-palette':
                    allocated = [(0, frames[:1], registration[:1]), (1, frames[1:], registration[1:])]
                else:
                    group = 2 if action.startswith('defeat') else 3 if action.startswith('victory') else 4
                    allocated = [(group, frames, registration)]
                masters.append({'path':path.relative_to(PROJECT).as_posix(), 'sha256':sha(path), 'provenance':(root/'raw'/(action+'-generation.json')).relative_to(PROJECT).as_posix(), 'pose_count':count, 'technical_registration':registration})
                for group, sequence, regs in allocated:
                    targets = []
                    for n, frame in enumerate(sequence):
                        target = root / 'native' / f'g{group:02d}' / f'g{group:02d}-f{n:03d}.png'
                        target.parent.mkdir(parents=True, exist_ok=True)
                        frame.save(target)
                        targets.append({'source':target.relative_to(PROJECT).as_posix(),'sha256':sha(target)})
                    all_groups.append({'group':group,'action':('HOLDING','IDLE','DEFEAT','VICTORY','CAST_SPELL')[group],'frames':targets})
                    frames_by_group[group] = sequence
            cohort={'heroClass':cid,'cohort':sex,'status':'authored configuration','visual_approval_granted':False,'rights_acceptance':False,'native_canvas':[150,175],'method':'Genuine whole-pose paintings; one uniform scale per master; measured hoof-contact translation only. No limb warp, recolouring, mirrored pixels, synthetic pose or duplicated idle action.','masters':masters,'groups':sorted(all_groups,key=lambda g:g['group'])}
            (root/'cohort-v3.json').write_text(json.dumps(cohort,indent=2)+'\n')
            review = REPORT / 'native' / (cid+'-'+sex)
            review.mkdir(parents=True,exist_ok=True)
            sheet=Image.new('RGB',(11*150,5*195),(45,45,45));d=ImageDraw.Draw(sheet)
            for g,seq in frames_by_group.items():
                for n,frame in enumerate(seq):
                    xy=(n*150,g*195);sheet.paste(frame,xy,frame);d.text((xy[0]+2,xy[1]+177),f'g{g} f{n}',fill='white')
                duration=200 if g==1 else 110
                seq[0].save(review/f'g{g:02d}.webp',save_all=True,append_images=seq[1:],duration=duration,loop=0,lossless=True)
            sheet.save(review/'native-contact.png')
            out.append({'heroClass':cid,'cohort':sex,'source':(root/'cohort-v3.json').relative_to(PROJECT).as_posix(),'source_sha256':sha(root/'cohort-v3.json'),'frames':sum(len(g['frames']) for g in all_groups),'groups':{str(g['group']):len(g['frames']) for g in all_groups},'native_review_sheet':(review/'native-contact.png').relative_to(PROJECT).as_posix(),'native_review_sheet_sha256':sha(review/'native-contact.png'),'recipe_changed':False,'selected':False})
    (REPORT/'battle-preparation.json').write_text(json.dumps(out,indent=2)+'\n')
    return out


if __name__ == '__main__':
    import sys
    if '--pad-defeat' in sys.argv:
        print(json.dumps(prepare_padded_defeat_guides()))
    elif '--pad-targeted' in sys.argv:
        print(json.dumps(prepare_targeted_guides()))
    elif '--prepare-battles' in sys.argv:
        print(json.dumps(prepare_battles()))
    else:
        inspect_sources()
