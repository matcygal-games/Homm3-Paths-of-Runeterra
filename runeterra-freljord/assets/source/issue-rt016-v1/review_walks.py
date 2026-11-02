"""Native-size candidate boards, exact twelve-ID matrix, and source closure."""
from pathlib import Path
import json
import sys
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageSequence
import author_walks as a


def rel(path):return path.relative_to(a.PROJECT).as_posix()


def review_images():
    # Same native crop for every image: no per-pose fitting or scale change.
    crop=(150,180,245,280)
    sheet=Image.new('RGB',(1170,580))
    draw=ImageDraw.Draw(sheet)
    for ui,unit in enumerate(a.UNITS):
        root=a.HERE/'candidates'/unit
        selected=a.PROJECT/'assets/source/creatures'/unit/'registered-v3/native/g02-f000.png'
        images=[Image.open(selected).convert('RGBA')]
        for phase in (0,3):
            images.append(Image.open(a.previous.root_for(unit)/'contacts-a'/f'g00-f{phase:03}.png').convert('RGBA'))
        images += [Image.open(root/f'composite-g00-f{phase:03}.png').convert('RGBA') for phase in range(6)]
        labels=('selected idle','previous contact0','previous contact3')+tuple('new '+str(i) for i in range(6))
        for bi,bg in enumerate(((49,55,43),(204,209,198))):
            y=(ui*2+bi)*145
            draw.rectangle((0,y,1170,y+145),fill=bg)
            for i,(image,label) in enumerate(zip(images,labels)):
                sheet.paste(image.crop(crop),(i*130+16,y+32),image.crop(crop))
                draw.text((i*130+3,y+4),label,fill='white' if bi==0 else 'black')
                if i==0:draw.text((i*130+3,y+18),unit,fill='white' if bi==0 else 'black')
    sheet.save(a.REPORT/'native-six-phase-dark-light.png')
    sheet.resize((2340,1160),Image.Resampling.NEAREST).save(a.REPORT/'diagnostic-2x.png')
    loops={}
    for unit in a.UNITS:
        root=a.HERE/'candidates'/unit
        frames=[]
        for i in range(6):
            image=Image.open(root/f'composite-g00-f{i:03}.png').convert('RGBA')
            frame=Image.new('RGBA',(285,140),(49,55,43,255))
            frame.alpha_composite(image.crop(crop),(15,25))
            frame.alpha_composite(a.mirror(image).crop(crop),(160,25))
            d=ImageDraw.Draw(frame)
            d.text((8,5),'surface / mirror only  phase'+str(i),fill='white')
            frames.append(frame)
        path=a.REPORT/(unit+'-mirror-only-loop.apng')
        frames[0].save(path,save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=0,blend=0)
        decoded=Image.open(path)
        exact=[np.array_equal(np.asarray(f.convert('RGBA')),np.asarray(ref)) for f,ref in zip(ImageSequence.Iterator(decoded),frames)]
        assert len(exact)==6 and all(exact)
        loops[unit]={'path':rel(path),'sha256':a.sha(path),'decoded_frames':decoded.n_frames,
                     'lossless_frame_match':exact,'preview_frame_duration_ms':100,
                     'scope':'in-place software loop and reflection only; native clock, facing, translation unobserved'}
    a.write_json(a.REPORT/'preview-proof.json',loops)


def matrix():
    active={row['unit']:row for row in json.loads((a.PROJECT/'assets/production/creatures/selection-v1.json').read_text())['active']}
    needs={
      'troll':'Editable long-arm heavy-jaw Troll anatomy, separate club/hand grip, iron bindings and greater Rime shoulder mass, textured limb/foot surfaces and fixed-chain opposite supports.',
      'ursine':'Editable bear-altered muzzle, claws, shoulders and torso with distinct Storm mane/forearm transformation, weight-bearing feet and fixed-chain opposite supports.',
      'walker':'Editable masked body, staff/stone grip, mantle and bindings, coherent gray Primal fur, opposite-support legs with continuous joint/foot materials.',
      'rider':'Selected-like textured squat boar anatomy, four fixed-chain limbs/hooves, tusks and shag, saddle/rider/reins/weapon attachment, upgrade barding and distinct rider kit; existing colored primitive guides are insufficient.',
      'yeti':'Editable massive ape-beast anatomy with distinct Ancient shoulder/brow/hand/mane masses, genuine planted soles and knuckle/arm weight transfer; preserve Ancient boulder action identity.'}
    rows=[]
    for unit in a.GAPS:
        row=active[unit]
        source=a.PROJECT/row['source']
        recipe=a.PROJECT/'assets/recipes/creatures'/(unit+'-battle.json')
        base=a.PROJECT/'assets/source/creatures'/unit
        geometry=[p for p in base.rglob('*') if p.is_file() and p.suffix.lower() in ('.blend','.obj','.fbx','.glb','.gltf')]
        producers=[p for p in base.rglob('*.py')]
        frames=[]
        for i in range(6):
            path=base/'registered-v3/native'/f'g00-f{i:03}.png'
            generated=a.PROJECT/'assets/generated/Content/Sprites/runeterra/freljord/creatures'/unit/'battle-frames'/path.name
            staged=a.PROJECT/'build/Mods/runeterra-freljord/Content/Sprites/runeterra/freljord/creatures'/unit/'battle-frames'/path.name
            frames.append({'phase':i,'selected_source':rel(path),'selected_sha256':a.sha(path),
              'generated':rel(generated),'generated_sha256':a.sha(generated) if generated.is_file() else None,
              'staged':rel(staged),'staged_sha256':a.sha(staged) if staged.is_file() else None})
        entry={'unit':unit,'family':row['family'],'selected_master':rel(source),'selected_master_sha256':a.sha(source),
           'selected_recipe':rel(recipe),'selected_recipe_sha256':a.sha(recipe),'selected_frames':frames,
           'existing_editable_geometry':[{ 'path':rel(p),'sha256':a.sha(p),'bytes':p.stat().st_size} for p in geometry],
           'existing_geometry_producers':[{ 'path':rel(p),'sha256':a.sha(p)} for p in producers],
           'selected_walking_gap':'pending','native_verified':False,'art_approval':False}
        if unit in a.UNITS:
            root=a.HERE/'candidates'/unit
            receipt=json.loads((root/'receipt.json').read_text())
            entry.update({'candidate':'authored configuration','candidate_selected':False,
                'candidate_receipt':rel(root/'receipt.json'),'candidate_receipt_sha256':a.sha(root/'receipt.json'),
                'candidate_phase_matrix':[{k:v for k,v in f.items() if k!='joints'} for f in receipt['frames']],
                'candidate_recipe':rel(a.HERE/'finish-source.json'),'candidate_recipe_sha256':a.sha(a.HERE/'finish-source.json'),
                'remaining':'Independent native-size artistic review, shoulder/waist/boot continuity judgment, coordinator selection/fresh publication, safe RT-017 native cadence/facing/contact/shadow evidence and human approval.'})
        else:
            # Enumerate rather than manufacture empty action/entity sources.
            family=('troll' if unit in ('frostTroll','rimeTroll') else
                    'ursine' if unit in ('ursineWarrior','stormChosen') else
                    'walker' if unit in ('spiritWalker','primalShaman') else
                    'rider' if unit in ('druvaskRider','winterOutrider') else 'yeti')
            entry.update({'candidate_created_this_pass':False,'editable_source_prerequisite':needs[family],
                 'geometry_observation':'Druvask neutral/red/blue primitive pose-guide meshes only; no selected textured model' if geometry else 'No .blend/.obj/.fbx/.glb/.gltf found in actual unit source tree',
                 'remaining':'Authored coherent six-phase family action surfaces or genuinely working identity-coherent generator, independent art review, selection/publication and native evidence.'})
        rows.append(entry)
    a.write_json(a.REPORT/'twelve-id-exact-hash-matrix.json',{'scope':'Current selected bytes and unselected Hunter candidates; all twelve selected gaps remain pending',
       'selection_sha256':a.sha(a.PROJECT/'assets/production/creatures/selection-v1.json'),'units':rows,
       'selected_generated_staged_bytes_match':all(f['selected_sha256']==f['generated_sha256']==f['staged_sha256'] for row in rows for f in row['selected_frames'])})


if __name__=='__main__':
    review_images()
    matrix()
    print('Review contacts, lossless loops and twelve-ID matrix written')
