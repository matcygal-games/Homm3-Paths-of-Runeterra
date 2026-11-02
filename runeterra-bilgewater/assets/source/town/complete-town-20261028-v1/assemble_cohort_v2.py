"""Adopt exact reviewed technical mattes into a new candidate cohort, not stage."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import json,hashlib,copy,shutil
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/derived-v2'
OUT=HERE/'derived-v2'
V1_PIN='c5eb6af7e638b86a879b51fda03236f0c86eb7f6763724bd4ec6b329139ac0e3'
ORDINARY='contour-repair-v2/revision-v3/proposal-manifest-v3.json'
ORDINARY_PIN='820856f00f40ff401eac742c5329cc006f75246f632e3a5fa92ffb8070d4fea2'
FOUR='physical-contract-v1/technical-mattes-four-v1/revision-v7/proposal-index.json'
FOUR_PIN='7ed40b25b95e9c9dc9f9176ae0d621a14c63dedc11779b25f9e28deed5fc6eb8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def pin(reference):
    p=PROJECT/reference['path']
    if sha(p)!=reference['sha256']:raise ValueError('Selected input changed: '+reference['path'])
    return p
def read_checked(p,checksum):
    if sha(p)!=checksum:raise ValueError('Input index changed: '+str(p))
    return json.loads(p.read_text())
def icon(layer,size):
    crop=layer.crop(layer.getchannel('A').getbbox());crop.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',size);out.alpha_composite(crop,((size[0]-crop.width)//2,(size[1]-crop.height)//2));return out
def main():
    v1=read_checked(HERE/'derived-v1/states.json',V1_PIN)
    ordinary=read_checked(HERE/ORDINARY,ORDINARY_PIN)
    four=read_checked(HERE/FOUR,FOUR_PIN)
    if (OUT/'states.json').exists():raise ValueError('Do not overwrite a released V2 cohort')
    OUT.mkdir(exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    selected={}
    for row in ordinary['states']:
        state=row['state']
        if 'proposed_frame_coordinate_alpha' not in row:raise ValueError('Unfinished ordinary matte: '+state)
        selected[state]={'source':pin(row['source_painting']),'delta':row['delta'],
             'mask':pin(row['proposed_frame_coordinate_alpha']),'proof':rel(HERE/ORDINARY)}
    for state,row in four['states'].items():
        source=PROJECT/row['genuine_source'];mask=PROJECT/row['alpha_mask']
        if sha(source)!=row['genuine_source_sha256'] or sha(mask)!=row['alpha_mask_sha256']:raise ValueError('Four-state source/matte drift')
        selected[state]={'source':source,'delta':row['whole_registration_delta'],'mask':mask,'proof':rel(HERE/FOUR)}
    if set(selected)!=set(v1['states'])-{'grail'}:raise ValueError('Expected all34 ordinary/coast selections exactly')
    frames={};records={};mattes=OUT/'selected-mattes';mattes.mkdir()
    for state,row in selected.items():
        source=Image.open(row['source']).convert('RGBA');registered=Image.new('RGBA',(800,374));registered.alpha_composite(source,tuple(row['delta']))
        alpha=Image.open(row['mask']).convert('L')
        if alpha.size!=(800,374) or set(alpha.getdata())-{0,255}:raise ValueError('Selected matte must be actual binary native contour')
        registered.putalpha(alpha);frames[state]=registered
        matte=mattes/(state+'.png');shutil.copy2(row['mask'],matte)
        old=v1['states'][state]
        entrance=old['entrance']
        if state=='dwellingUpLvl5':entrance=[655,110]
        elif state=='dwellingLvl5':entrance=[655,112]
        elif state in ('shipyard','ship'):entrance=[638,306]
        records[state]={'site':old['site'],'source':rel(row['source']),'source_sha256':sha(row['source']),
          'source_canvas':[800,374],'delta':row['delta'],'alpha_mask':rel(matte),'alpha_mask_sha256':sha(matte),
          'matte_proposal_index':row['proof'],'matte_proposal_index_sha256':sha(PROJECT/row['proof']),
          'entrance':entrance,'entrance_status':'Source proposal; actual supported frontage/approach belongs to the separate physical contract.',
          'z':old['z']}
    g=json.loads((HERE/'grail-registration-v2.json').read_text())
    gpath=PROJECT/g['frame']
    if sha(gpath)!=g['frame_sha256']:raise ValueError('Selected Grail placement drift')
    frames['grail']=Image.open(gpath).convert('RGBA')
    records['grail']={'site':'grail','source':rel(HERE/'complete-town-native-v3.png'),'source_sha256':sha(HERE/'complete-town-native-v3.png'),
       'source_canvas':[800,374],'uniform_scale':.75,'source_root':[751,238],'target_root':[330,313],
       'entrance':[330,313],'z':335,'registration':rel(HERE/'grail-registration-v2.json'),'registration_sha256':sha(HERE/'grail-registration-v2.json')}
    for state,layer in frames.items():
        folder=OUT/'states'/state;folder.mkdir(parents=True,exist_ok=True)
        target=folder/'layer.png'
        if state!='grail':layer.save(target)
        alpha=layer.getchannel('A').point(lambda x:255 if x>=8 else 0)
        area=Image.new('RGBA',layer.size);area.putalpha(alpha);area.save(folder/'area.png')
        edge=ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha.filter(ImageFilter.MinFilter(3)))
        border=Image.new('RGBA',layer.size,(255,235,80,0));border.putalpha(edge);border.save(folder/'border.png')
        icon(layer,(58,64)).save(folder/'campaign.png');icon(layer,(150,70)).save(folder/'construction.png')
        record=records[state];record.update({'alpha_bounds':list(layer.getchannel('A').getbbox()),'visible_pixels':alpha.histogram()[255]})
        for field,name in [('frame','layer.png'),('area','area.png'),('border','border.png'),('campaign','campaign.png'),('construction','construction.png')]:
            record[field]=rel(folder/name);record[field+'_sha256']=sha(folder/name)
    bg=PROJECT/v1['background']
    if sha(bg)!=v1['background_sha256']:raise ValueError('Held background changed')
    def scene(name,states):
        image=Image.open(bg).convert('RGBA')
        for state in sorted(states,key=lambda k:records[k]['z']):image=Image.alpha_composite(image,frames[state])
        image.convert('RGB').save(REPORT/(name+'.png'))
    top=v1['full_scene_states'];base=v1['base_scene_states']
    scene('full-native',top);scene('base-native',base);scene('coast-native',top+['ship','grail']);scene('shipyard-native',top+['shipyard']);scene('early-native',['villageHall','fort','tavern','dwellingLvl1'])
    scene('temple-without-tavern-native',[s for s in top if s!='tavern']);scene('roost-without-temple-native',[s for s in top if s!='dwellingUpLvl4'])
    scene('citadel-without-leviathan-native',[s if s!='castle' else 'citadel' for s in top if s!='dwellingUpLvl7'])
    index={'status':'authored configuration','cohort':'derived-v2-coordinated-source-candidate','background':v1['background'],'background_sha256':v1['background_sha256'],
       'canvas':[800,374],'ordinary_land_sites':16,'optional_coast':1,'grail':1,'state_count':35,'states':records,
       'full_scene_states':top,'base_scene_states':base,'previous_preparation_index_sha256':V1_PIN,
       'selected_ordinary_matte_index':rel(HERE/ORDINARY),'selected_ordinary_matte_index_sha256':ORDINARY_PIN,
       'selected_four_matte_index':rel(HERE/FOUR),'selected_four_matte_index_sha256':FOUR_PIN,
       'physical_layout_status':'Pending actual public consumer and meaningful negative controls against this exact cohort; no unverified full-mod freshness/game claim.',
       'native_verified':False,'release_accepted':False}
    (OUT/'states.json').write_text(json.dumps(index,indent=2)+'\n')
    print(json.dumps({'states':len(records),'index_sha256':sha(OUT/'states.json'),'report':str(REPORT),'background_sha256':index['background_sha256']}))
if __name__=='__main__':main()
