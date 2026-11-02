"""Complete construction seams and separately retained own-entry soles.

Public terrace fascia is not a foot. Real separately retained column/pedestal
soles are structural even where their bounds overlap an entry observation;
they are never removed by the own-entry role subtraction.
"""
from pathlib import Path
import json
import hashlib
import importlib.util
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'ownership-contact-roles-v2'
OUT.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('binder',HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
index_path = HERE / 'localized-ground-selection-v1/states.json'
index = json.loads(index_path.read_text())
separation_path = HERE / 'ownership-separation-v3/plan.json'
separation = json.loads(separation_path.read_text())
original_annotation_path = HERE / 'semantic-candidate-v6/annotations.json'
annotation = json.loads(original_annotation_path.read_text())
literal_contacts = json.loads((HERE / 'structural-contacts-v3/annotations.json').read_text())['states']

def ref(path):
    return {'path':path.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def points(mask):
    box = mask.getbbox()
    return [[x,y] for y in range(box[1],box[3]) for x in range(box[0],box[2]) if mask.getpixel((x,y))] if box else []

def polygon_mask(polygon):
    image = Image.new('L',(800,374))
    ImageDraw.Draw(image).polygon(list(map(tuple,polygon)),fill=255)
    return image

def lower_contact(alpha,region):
    selected = ImageChops.multiply(alpha,region)
    bounds = selected.getbbox()
    result = Image.new('L',(800,374))
    if bounds:
        for x in range(bounds[0],bounds[2]):
            ys = [y for y in range(bounds[1],bounds[3]) if selected.getpixel((x,y))]
            if ys:
                result.putpixel((x,max(ys)),255)
    return result

roles = {}
for key,row in index['states'].items():
    plan = separation['states'][key]
    frame = Image.open(PROJECT / row['frame']).convert('RGBA')
    alpha = frame.getchannel('A').point(lambda p:255 if p>=8 else 0)
    if plan.get('retain_all') or key in ('dwellingLvl7','dwellingUpLvl7'):
        structural = binder.trace(literal_contacts[key]['foundation'])
        if ImageChops.subtract(structural,alpha).getbbox():
            raise ValueError('A separately retained real foot was removed: '+key)
    else:
        structural = Image.new('L',(800,374))
        if key not in ('dwellingUpLvl4','special2','dwellingLvl3','dwellingUpLvl3'):
            seam = [[x,y-1] for x,y in plan['boundary']]
            draw = ImageDraw.Draw(structural)
            draw.line(list(map(tuple,seam)),fill=255,width=1)
            structural = ImageChops.multiply(structural,alpha)
        for region in plan.get('structural_contact_regions',[]):
            structural = ImageChops.lighter(structural,lower_contact(alpha,polygon_mask(region)))
    entry = Image.new('L',(800,374))
    if plan.get('own_entry_region'):
        x0,y0,x1,y1 = plan['own_entry_region']
        region = Image.new('L',(800,374))
        ImageDraw.Draw(region).rectangle((x0,y0,x1-1,y1-1),fill=255)
        entry = ImageChops.subtract(lower_contact(alpha,region),structural)
    complete = ImageChops.lighter(structural,entry)
    if not structural.getbbox():
        raise ValueError('Every real state requires actual structural contacts: '+key)
    if ImageChops.multiply(structural,entry).getbbox():
        raise ValueError('Complete contact roles must be disjoint, not a foot waiver')
    folder = OUT / key
    folder.mkdir()
    structural.save(folder / 'structural-foundation.png')
    entry.save(folder / 'own-entry-contact.png')
    complete.save(folder / 'complete-contact.png')
    annotation['states'][key]['foundation'] = {'pixels':points(structural)}
    annotation['states'][key]['contact_interpretation'] = 'Complete actual construction seam plus separately retained real column/sculpture/pier soles. Permanent public terrace/quay fascia is scenery. The complete contact union retains own entrance-step soles in a disjoint entry role; structural feet are never subtracted because they overlap an entry observation.'
    # A legacy frontage brush is bounded to the current actual source canvas.
    # This clips an observation, never architectural anatomy or a real foot.
    old_door = binder.trace(annotation['states'][key]['door'])
    bounds = alpha.getbbox()
    envelope = Image.new('L',(800,374))
    ImageDraw.Draw(envelope).rectangle((bounds[0],bounds[1],bounds[2]-1,bounds[3]-1),fill=255)
    bounded_door = ImageChops.multiply(old_door,envelope)
    annotation['states'][key]['door'] = {'pixels':points(bounded_door)}
    roles[key] = {'structural_foundation':ref(folder / 'structural-foundation.png'),
        'own_entry_contact':ref(folder / 'own-entry-contact.png'),'complete_contact':ref(folder / 'complete-contact.png'),
        'structural_contact_pixels':len(points(structural)),'own_entry_contact_pixels':len(points(entry)),
        'complete_contact_pixels':len(points(complete)),
        'partition':'Disjoint union, with all separately retained structural column/pedestal/pier soles kept in the structural role, never waived as entry.'}
annotation['background'] = {'path':index['background'],'sha256':index['background_sha256']}
annotation['state_index_sha256'] = ref(index_path)['sha256']
annotation['complete_scene_states'] = index['full_scene_states']
annotation['contact_role_partition'] = roles
annotation['selected_editable_sources'] = [ref(index_path),ref(separation_path),ref(original_annotation_path),ref(Path(__file__))]
annotation['cannon_contact_correction'] = 'Native actor-only view confirms the outer outline crosses raised cannon muzzle and suspended barrel/chassis, not ground bearings. Omit that artificial seam; retain the complete separately authored wheel/cradle/pavilion-post sole windows, including all detached supporting material. This source-anatomy classification does not read terrain or desired passing masks.'
annotation['review_limits'] = 'Actual native source ownership and complete-contact role candidate. The unchanged complete consumer, actual connected source streets, controlled source mutations and independent anatomy review must still execute. No geometry or appearance pass is inferred from full-image preservation.'
(OUT / 'annotations.json').write_text(json.dumps(annotation,indent=2,sort_keys=True)+'\n',encoding='utf-8')
(OUT / 'role-receipt.json').write_text(json.dumps({'status':'design proposal','cohort':ref(index_path),'separation':ref(separation_path),'states':roles,'all35states_retained':len(roles)==35,'support_mask_or_desired_result_used':False,'structural_foot_subtracted_as_entry':False},indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({key:{'structural':row['structural_contact_pixels'],'own_entry':row['own_entry_contact_pixels']} for key,row in roles.items()}))
