"""Painted guide-alpha assisted TG1 candidate; approved source RGB is unchanged."""
import importlib.util,json
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter,ImageDraw

HERE=Path(__file__).resolve().parent
V5=HERE.parent/'approved-tg1-implementation-20261030-v5'
GUIDES=HERE.parent/'approved-tg1-implementation-20261030-v11'
V7=HERE.parent/'approved-tg1-implementation-20261030-v7'
spec=importlib.util.spec_from_file_location('tg1_ownership_helpers',V5/'finish_sources.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
PROJECT=core.PROJECT;REPORT=core.WORKSPACE/'reports/targon-tg1-implementation-20261030-v15'

def guided_upper(old_alpha,guide,site,lower):
    # A guide is reliable for roof/sky separation, not the invented flattened
    # contact line of its detached sprite. Preserve the genuine original native
    # lower frontage rather than import its shortened steps/ground.
    threshold={'sunhawks':94,'civic':112,'reliquary':125,'guild':109,
      'solariTemple':122,'fortifications':126,'trailguard':171,'archers':178,
      'ibex':209,'stellacorns':180,'sunforgers':231,'lunari':235,
      'silo':285,'marketplace':325,'blacksmith':237,'tavern':319,
      'monastery':314,'starforge':317,'lunariShrine':319,'grail':265}[site]
    upper=ImageChops.multiply(old_alpha,guide.filter(ImageFilter.MaxFilter(3)))
    lower=ImageChops.multiply(old_alpha,lower.filter(ImageFilter.MaxFilter(3)))
    crop=lower.crop((0,threshold,800,374));upper.paste(crop,(0,threshold))
    return upper

def main():
    index=core.read(V5/'candidate-frames.json');registration=core.read(GUIDES/'registration.json')
    guide_for={(r['tag'],site):r for r in registration['records']for site in r['sites']}
    layers={};records=[];new_union=Image.new('L',(800,374));old_union=new_union.copy()
    for state,row in index['states'].items():
        old=core.image(PROJECT/row['frame']['path']);old_alpha=old.getchannel('A')
        if row['source_tag']=='middle':
            # The enlarged middle guide is not registered; refuse its alpha.
            # Its states retain manually reviewed native contour assistance.
            alpha=core.image(V7/'frames'/(state+'.png')).getchannel('A');method='manual-native-contour-middle-guide-not-admitted'
        elif(row['source_tag'],row['site'])in guide_for:
            guide=guide_for[row['source_tag'],row['site']]
            mask=core.image(PROJECT/guide['mask']).convert('L')
            alpha=guided_upper(old_alpha,mask,row['site'],core.image(V7/'frames'/(state+'.png')).getchannel('A'))
            if state=='dwellingUpLvl5':
                extra=Image.new('L',(800,374));ImageDraw.Draw(extra).polygon([(164,11),(172,10),(178,15),(177,27),(174,28),(174,46),(170,46),(170,26),(164,24)],fill=255)
                alpha=ImageChops.lighter(alpha,ImageChops.multiply(extra,old_alpha))
            method='registered-guide-upper-alpha64-1px-budget-native-contour-lower-contact'
        else:
            alpha=core.image(V7/'frames'/(state+'.png')).getchannel('A');method='manual-native-contour'
        layer=core.image(PROJECT/row['painting']['path']);layer.putalpha(alpha);layers[state]=layer
        if state=='capitol':
            spike=Image.new('L',(800,374));ImageDraw.Draw(spike).polygon([(300,26),(306,20),(307,18),(311,18),(314,24),(314,40),(302,42)],fill=255)
            alpha=ImageChops.lighter(alpha,spike);layer.putalpha(alpha)
        records.append({'state':state,'method':method,'removed_pixels':ImageChops.subtract(old_alpha,alpha).histogram()[255]})
        if state in index['complete_scene_states']:
            new_union=ImageChops.lighter(new_union,alpha);old_union=ImageChops.lighter(old_union,old_alpha)
    for record in index['hidden_face_ownership']:
        if record['kind']!='genuine-painted-hidden-face':continue
        state=record['behind_state'];layer=layers[state]
        budget=ImageChops.multiply(layer.getchannel('A'),layers[record['front_complete_state']].getchannel('A'))
        alpha=layer.getchannel('A');layer.paste(core.image(PROJECT/record['painted_source']['path']),(0,0),budget);layer.putalpha(alpha)
    approved=core.image(core.ORIGINAL/'approved-full-native.png')
    background=core.image(PROJECT/index['background']['path']);background.paste(approved,(0,0),ImageChops.subtract(old_union,new_union))
    full=background.copy()
    for state in index['complete_scene_states']:full.alpha_composite(layers[state])
    if full.tobytes()!=approved.tobytes():raise ValueError('Approved TG1 changed')
    core.save(HERE/'background-native.png',background);core.save(HERE/'fully-built.png',full)
    for state,layer in layers.items():core.save(HERE/'frames'/(state+'.png'),layer)
    # Versioned all-state selection for candidate geometry and converter replay.
    for state,row in index['states'].items():
        row['frame']=core.ref(HERE/'frames'/(state+'.png'));row['bbox']=list(layers[state].getchannel('A').getbbox())
    index.update(background=core.ref(HERE/'background-native.png'),source_ancestor=core.ref(V5/'candidate-frames.json'),
      approved_full_RGBA_changes=0,physical_pass=False,native_verified=False)
    core.dump(HERE/'candidate-frames.json',index)
    core.dump(HERE/'factions-candidate.json',core.read(V5/'factions-candidate.json'))
    core.dump(HERE/'matte-assistance.json',{'status':'authored configuration','auxiliary_only':True,
      'registered_guide':core.ref(GUIDES/'registration.json'),'approved_RGBA_changes':0,'records':records,
      'physical_pass':False,'native_verified':False})
    REPORT.mkdir(parents=True,exist_ok=True)
    for site in core.read(core.ORIGINAL/'site-plan-v1.json')['sites']:
        canvas=Image.new('RGB',(400,160*len(site['states'])),(28,31,30));draw=ImageDraw.Draw(canvas)
        for n,state in enumerate(site['states']):
            layer=layers[state];bg=Image.new('RGBA',layer.size,(57,59,61,255));bg.alpha_composite(layer)
            crop=bg.crop(layer.getchannel('A').getbbox());crop.thumbnail((390,130),Image.Resampling.NEAREST)
            canvas.paste(crop.convert('RGB'),((400-crop.width)//2,n*160+24));draw.text((5,n*160+5),state,fill='white')
        core.save(REPORT/(site['id']+'-states.png'),canvas)
    print(json.dumps({'states':len(layers),'full_RGBA_changes':0,'physical_pass':False}))

if __name__=='__main__':main()
