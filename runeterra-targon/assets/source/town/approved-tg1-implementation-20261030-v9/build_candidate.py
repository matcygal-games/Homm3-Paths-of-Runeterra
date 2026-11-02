"""Source-only TG1 alpha refinement, native-format production and preservation.

No region content/recipes/generated/stages or game inputs are modified.
Architecture RGB comes from original painted sources; technique creates masks,
registration, outlines and icons only. Genuine hidden faces are independently
painted sources, never flattened neighbour pixels claimed as another building.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from PIL import Image,ImageChops,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'approved-tg1-implementation-20261030-v7'
V5=HERE.parent/'approved-tg1-implementation-20261030-v5'
spec=importlib.util.spec_from_file_location('tg1_source_helpers',V5/'finish_sources.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
PROJECT=core.PROJECT;WORKSPACE=core.WORKSPACE
REPORT=WORKSPACE/'reports/targon-tg1-implementation-20261030-v9'

# Native-pixel source annotation, limited to skyline/holes. Blue heraldry in
# lower facades is intentionally outside these windows. These are technical
# alpha annotations, not a declaration of physical or human art acceptance.
SKY_WINDOWS={
 'sunhawks':[(33,0,210,76)], 'civic':[(235,0,366,76)],
 'guild':[(418,15,494,81)], 'fortifications':[(599,0,776,105),(671,105,702,133)],
 'solariTemple':[(486,0,554,106)], 'reliquary':[(349,70,414,114)],
}
KEEP={
 'sunhawks':[(130,48,142,94),(163,8,179,46),(42,62,55,95)],
 'guild':[(450,73,463,108)],
}

def sky_alpha(image,site):
    """Remove bounded cool sky pixels, retaining explicitly painted banners."""
    alpha=image.getchannel('A').copy();pixels=image.load();out=alpha.load()
    removed=Image.new('L',image.size);rp=removed.load()
    for x0,y0,x1,y1 in SKY_WINDOWS.get(site,[]):
        for y in range(y0,y1):
            for x in range(x0,x1):
                if any(a<=x<c and b<=y<d for a,b,c,d in KEEP.get(site,[])):continue
                r,g,b,_=pixels[x,y]
                if out[x,y] and g>=95 and b>r+12 and g>r+4 and b>g+3:
                    out[x,y]=0;rp[x,y]=255
    return alpha,removed

def binary(path,mask):
    core.save(path,mask.convert('RGB'));return core.ref(path)

def source_inventory():
    selected=[Path(__file__),PRIOR/'refine_mattes.py',V5/'finish_sources.py',
      HERE.parent/'approved-tg1-implementation-20261030-v4/contours.json',
      core.ORIGINAL/'approved-full-raw.png',core.ORIGINAL/'approved-full-native.png',
      core.ORIGINAL/'empty-recovery-native.png',core.ORIGINAL/'site-plan-v1.json']
    selected.extend(core.ORIGINAL/(tag+'-states-native.png')for tag in ('early','middle','late'))
    selected.extend(core.HIDDEN/name for name in ('approved-rear-native.png','early-rear-native.png',
      'middle-rear-native.png','late-rear-native.png','temple-front-native.png'))
    return [core.ref(path)for path in sorted(selected)]

def produce():
    prior=core.read(V5/'candidate-frames.json');index=json.loads(json.dumps(prior))
    plan=core.read(core.ORIGINAL/'site-plan-v1.json')
    layers={};cuts={}
    for state,row in index['states'].items():
        im=core.image(PROJECT/row['frame']['path'])
        alpha,cut=sky_alpha(im,row['site']);im.putalpha(alpha);layers[state]=im;cuts[state]=cut
    # Matte changes alter foreground ownership budgets: regenerate hidden faces
    # only under new exact full-state foreground coverage, never an old mask.
    for state,row in index['states'].items():
        original=core.image(PROJECT/row['painting']['path']);original.putalpha(layers[state].getchannel('A'));layers[state]=original
    for row in prior['hidden_face_ownership']:
        if row['kind']!='genuine-painted-hidden-face':continue
        state=row['behind_state'];layer=layers[state]
        mask=ImageChops.multiply(layer.getchannel('A'),layers[row['front_complete_state']].getchannel('A'))
        alpha=layer.getchannel('A');layer.paste(core.image(PROJECT/row['painted_source']['path']),(0,0),mask);layer.putalpha(alpha)
    union=Image.new('L',(800,374))
    for state in index['complete_scene_states']:union=ImageChops.lighter(union,layers[state].getchannel('A'))
    approved=core.image(core.ORIGINAL/'approved-full-native.png')
    if core.sha(core.ORIGINAL/'approved-full-native.png')!=core.APPROVED_SHA:raise ValueError('Approved TG1 changed')
    background=core.image(PROJECT/prior['background']['path'])
    old_union=Image.new('L',(800,374))
    for state in index['complete_scene_states']:
        old_union=ImageChops.lighter(old_union,core.image(PROJECT/prior['states'][state]['frame']['path']).getchannel('A'))
    background.paste(approved,(0,0),ImageChops.subtract(old_union,union))
    full=background.copy()
    for state in index['complete_scene_states']:full.alpha_composite(layers[state])
    if full.tobytes()!=approved.tobytes():raise ValueError('Approved complete RGBA changed')
    core.save(HERE/'background-native.png',background);core.save(HERE/'fully-built.png',full)
    index['background']=core.ref(HERE/'background-native.png')
    for state,row in index['states'].items():
        im=layers[state];alpha=im.getchannel('A')
        frame=HERE/'frames'/(state+'.png');core.save(frame,im)
        body=HERE/'masks'/(state+'-body.png');core.save(body,alpha)
        binary(HERE/'masks'/(state+'-sky-cut.png'),cuts[state])
        area=Image.new('RGBA',im.size);area.putalpha(alpha)
        border=Image.new('RGBA',im.size,(245,210,85,0));border.putalpha(ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha))
        for suffix,img in [('area',area),('border',border),('campaign',core.icon(im,(58,64)))]:
            path=HERE/'derived'/(state+'_'+suffix+'.png');core.save(path,img);row[suffix]=core.ref(path)
        path=HERE/'construction'/(state+'.png');core.save(path,core.icon(im,(150,70)))
        row.update(frame=core.ref(frame),body=core.ref(body),construction=core.ref(path),bbox=list(alpha.getbbox()))
    index.update(source_ancestor=core.ref(V5/'candidate-frames.json'),
        provenance_inputs=source_inventory(),physical_admission_pass=False,
        source_matte_policy={'sky_windows':SKY_WINDOWS,'protected_heraldry_windows':KEEP,
          'cold_pixel_rule':'G>=95; B>R+12; G>R+4; B>G+3; only inside explicit skyline windows'},
        scope='Candidate, not selected. Exact full-town replay and native converter evidence do not approve masks, physical geometry or native play.')
    core.dump(HERE/'candidate-frames.json',index)
    core.dump(HERE/'factions-candidate.json',core.read(V5/'factions-candidate.json'))
    # Existing compiler supports checksummed source provenance. Include no raw
    # workstation/provider output hints in the selected project-relative ledger.
    core.dump(HERE/'source-ownership-ledger.json',{
      'status':'authored configuration','candidate_only':True,
      'inputs':source_inventory(),'raw_normalization':{'source_canvas':[1836,857],
        'native_canvas':[800,374],'method':'whole-canvas LANCZOS','uniform_scale':False,
        'note':'Rounded provider canvas ratio differs slightly from target. Never treat it as camera geometry.'},
      'rgb_policy':'Genuine painted architecture; bounded genuine hidden-face sources only under actual full foreground alpha.',
      'alpha_policy':index['source_matte_policy'],'approval':'No physical, native or release acceptance.'})
    return index,layers,plan

def compile_sources(index):
    # Reuse an established source-only recipe generator with exact current data.
    # Override paths only in this private loaded module, never canonical files.
    core.HERE=HERE;core.REPORT=REPORT
    catalog=core.compile_candidate(index)
    return catalog

def gallery(index,layers,plan):
    REPORT.mkdir(parents=True,exist_ok=True)
    relative='../../'+HERE.relative_to(WORKSPACE).as_posix()
    parts=['<!doctype html><meta charset="utf-8"><title>Targon TG1 candidate V9</title>',
      '<style>body{font:17px Georgia;color:#eee;background:#202423;max-width:1100px;margin:auto}img{max-width:100%}</style>',
      '<h1>Targon TG1 source candidate V9</h1><p>Authored configuration. Approved fully built pixels retained exactly. Physical masks and native play remain unapproved.</p>']
    for name,title in [('background-native.png','Empty source plate'),('fully-built.png','Exact approved fully built')]:parts.append('<h2>'+title+'</h2><img width="800" height="374" src="'+relative+'/'+name+'">')
    for site in plan['sites']:
        canvas=Image.new('RGB',(400,160*len(site['states'])),(28,31,30));draw=ImageDraw.Draw(canvas)
        for n,state in enumerate(site['states']):
            im=layers[state];bg=Image.new('RGBA',im.size,(57,59,61,255));bg.alpha_composite(im)
            crop=bg.crop(im.getchannel('A').getbbox());crop.thumbnail((390,130),Image.Resampling.NEAREST)
            canvas.paste(crop.convert('RGB'),((400-crop.width)//2,n*160+24));draw.text((5,n*160+5),state,fill='white')
        name=site['id']+'-states.png';core.save(REPORT/name,canvas);parts.append('<h2>'+site['id']+'</h2><img src="'+name+'">')
    core.write(REPORT/'index.html',('\n'.join(parts)+'\n').encode())

if __name__=='__main__':
    index,layers,plan=produce();catalog=compile_sources(index);gallery(index,layers,plan)
    print(json.dumps({'states':len(layers),'RGBA_changes':0,'recipes':catalog['recipe_count'],'outputs':catalog['native_output_count'],
       'physical_pass':False,'native_verified':False}))
