"""PRIVATE original-game comparison pixels; excluded from all distributed bundles."""
from pathlib import Path
import hashlib
import importlib.util
import json
from PIL import Image,ImageDraw,ImageOps

root=Path(__file__).resolve().parents[5]
spec=importlib.util.spec_from_file_location('animals',root/'scripts/targon_animal_art.py')
animals=importlib.util.module_from_spec(spec);spec.loader.exec_module(animals)
folder=Path(__file__).parent
background=Image.open(folder/'cmbkgrmt.png').convert('RGBA')
board=Image.new('RGB',(2000,930));draw=ImageDraw.Draw(board);rows=[]
for row,unit in enumerate(('crystalIbex','solariSunhawk','stellacorn')):
    recipe=json.loads((root/'assets/recipes/creatures/animals'/unit/'battle.json').read_text())
    frame=next(group for group in recipe['groups'] if group['group']==0)['frames'][2]
    original=Image.open(root/frame['raw_render_source']).convert('RGBA')
    final=Image.open(root/frame['source']).convert('RGBA')
    assembled,stats=animals.native_image(original,'battle')
    assert assembled.tobytes()==final.tobytes()
    columns=[]
    for facing,raw,clean,pivot in (('right',original,final,218),('left',ImageOps.mirror(original),ImageOps.mirror(final),232)):
        for label,image in (('raw',raw),('native',clean)):
            composed=background.copy();composed.alpha_composite(image,(400-pivot,380-267))
            path=folder/(unit+'-'+facing+'-'+label+'.png');composed.save(path)
            crop=composed.crop((150,210,650,520)).convert('RGB');column=len(columns)
            board.paste(crop,(column*500,row*310));draw.text((column*500+6,row*310+6),unit+' '+facing+' '+label,fill=(255,255,220))
            columns.append({'image':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    rows.append({'unit':unit,'group':0,'frame':2,'alpha_proof':stats,'comparisons':columns})
board.save(folder/'both-facing-before-after-alpha-v14.png')
(folder/'both-facing-before-after-alpha-v14.json').write_text(json.dumps({
    'status':'authored configuration','private_reference_only':True,
    'exclude_from_all_source_and_release_bundles':True,'rows':rows,
    'limits':'Static compositing on the actual original battle background. Not native Targon gameplay or clock playback. No opaque/near-body AA loss; manual native-size comparison still required for unprotected thin translucent features.'},indent=2,sort_keys=True)+'\n')

# Read actual selected source backgrounds rather than assume their named dimensions.
preview_groups={0,2,3,4,12,18,20,21}
results=[]
subjects=[('targon:'+u,None) for u in animals.UNITS]+[('original:'+u,u) for u in ('croc','cpegas','cunico')]
for name,control in subjects:
    if control:
        frames=[(int(p.stem[1:3]),p) for p in (root/'references/native-20261023-v1/frames'/control).glob('g*-f*.png')]
    else:
        unit=name.split(':')[1];recipe=json.loads((root/'assets/recipes/creatures/animals'/unit/'battle.json').read_text())
        frames=[(group['group'],root/frame['source']) for group in recipe['groups'] for frame in group['frames']]
    for label in ('120','130'):
        bgpath=root/('assets/source/town/ui/creatureBackground'+label+'.png')
        with Image.open(bgpath) as bg:w,h=bg.size
        crop=(170,155,170+w,155+h);entries=[]
        for group,path in frames:
            if group not in preview_groups:continue
            image=Image.open(path).convert('RGBA');bound=image.getchannel('A').point(lambda a:255 if a>=192 else 0).getbbox()
            if bound:
                over=[max(0,crop[0]-bound[0]),max(0,crop[1]-bound[1]),max(0,bound[2]-crop[2]),max(0,bound[3]-crop[3])]
                entries.append({'group':group,'frame':path.name,'opaque_bounds':bound,'crop_overflow_ltrb':over})
        results.append({'subject':name,'background_canvas':[w,h],'crop':crop,'frames':entries,
            'overflow_frame_count':sum(any(e['crop_overflow_ltrb']) for e in entries)})
(folder/'actual-native-preview-controls-v14.json').write_text(json.dumps({
    'status':'authored configuration','actual_backgrounds':True,'results':results,
    'consumer':'vcmi-develop/vcmi-develop/client/widgets/Images.cpp:CCreatureAnim::loopPreview and MiscWidgets.cpp:CCreaturePic',
    'limits':'Executed static alpha192 crop comparison for actual eligible preview action groups, including moving/start/end. Neither native playback nor automatic whole-cohort resizing; original controls intentionally also clip some actions.'},indent=2,sort_keys=True)+'\n')
print('Private native-background alpha and actual preview-control reports written')
