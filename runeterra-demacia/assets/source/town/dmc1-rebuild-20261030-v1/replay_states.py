"""DMC1 candidate all-state source assembly. No current selections are changed."""
from pathlib import Path
import argparse,hashlib,json,shutil,sys
from PIL import Image,ImageChops,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
WORKSPACE=HERE
GEOMETRY=HERE/'geometry-v3'
EARLIER=WORKSPACE/'reports/demacia-dmc1-states-20261030-v1/portable-fit-v1'
SIZE=(800,374)
GOLD=(225,190,80,255);SHADOW=(38,29,15,208)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def load(p):return Image.open(p).convert('RGBA')
def poly(items):
    mask=Image.new('L',SIZE);d=ImageDraw.Draw(mask)
    for points in items:d.polygon([tuple(q) for q in points],fill=255)
    return mask
def binary(a):return a.point(lambda q:255 if q>=128 else 0)
def border(mask):
    near=mask.filter(ImageFilter.MaxFilter(3));far=mask.filter(ImageFilter.MaxFilter(5));out=Image.new('RGBA',SIZE)
    for color,a in ((SHADOW,ImageChops.subtract(far,near).point(lambda q:208 if q else 0)),(GOLD,ImageChops.subtract(near,mask))):
        layer=Image.new('RGBA',SIZE,color);layer.putalpha(a);out.alpha_composite(layer)
    return out
def visible(town,built):
    groups={}
    for key in town['structures']:
        if key not in built:continue
        chain=[key]
        while town['buildings'][chain[-1]].get('upgrades'):chain.append(town['buildings'][chain[-1]]['upgrades'])
        if chain[-1] not in groups or len(chain)>groups[chain[-1]][0]:groups[chain[-1]]=(len(chain),key)
    return [entry[1] for entry in groups.values()]

def assemble(output):
    if output.exists():raise ValueError('New candidate directory required')
    output.mkdir(parents=True);traces=json.loads((HERE/'traces.json').read_text());factions=json.loads((HERE/'native-factions.json').read_text());town=factions['demacia']['town']
    def effective_faction(faction):
        result=json.loads(json.dumps(faction));defaults=json.loads((HERE/'native-building-library.json').read_text())
        result['town']['buildings']={k:{**defaults.get(k,{}),**value} for k,value in faction['town']['buildings'].items()}
        return result
    states={};site_for={};provenance={};reference=load(WORKSPACE/traces['source']);background=load(GEOMETRY/'background.png')
    for name,site in traces['sites'].items():
        final=site['states'][-1]
        states[final]=(load(GEOMETRY/f'{name}-full.png'),Image.open(GEOMETRY/f'{name}-architecture-mask.png').convert('L'))
        site_for.update({key:name for key in site['states']});provenance[final]={'kind':'approved-visible-pixels-and-painted-hidden-underbody','geometry_frame_sha256':sha(GEOMETRY/f'{name}-full.png'),'site':name}
    early=json.loads((EARLIER/'receipt.json').read_text())
    for row in early['states']:
        key=row['state'];frame=load(EARLIER/key/'frame.png');mask=Image.open(EARLIER/key/'architecture-mask.png').convert('L')
        if sha(EARLIER/key/'frame.png')!=row['frame_sha256'] or sha(EARLIER/key/'architecture-mask.png')!=row['mask_sha256']:raise ValueError('Earlier state changed')
        states[key]=(frame,mask);provenance[key]={'kind':'painted-earlier-building-state','source':row}
    revision=WATCHTOWER
    special=json.loads((revision/'native-v1/receipt.json').read_text())
    if sha(revision/'native-v1/frame.png')!=special['frame_sha256'] or sha(revision/'native-v1/architecture-mask.png')!=special['mask_sha256']:raise ValueError('Refined watchtower changed')
    states['special1']=(load(revision/'native-v1/frame.png'),Image.open(revision/'native-v1/architecture-mask.png').convert('L'))
    provenance['special1']={'kind':'refined-painted-slender-watchtower','source':special}
    # Ship is the native upgrade of shipyard; it contains the complete quay+boat.
    coast=traces['sites']['coast'];dock_mask=poly(coast['polygons']).filter(ImageFilter.MaxFilter(7));boat_mask=poly(coast['ship_polygons']).filter(ImageFilter.MaxFilter(7))
    dock=load(HERE/'art/underpaint-dock-native.png');dock.putalpha(dock_mask)
    states['shipyard']=(dock,poly(coast['architecture_polygons']));provenance['shipyard']={'kind':'painted-ship-absent-coast-state','underpaint_sha256':sha(HERE/'art/underpaint-dock-native.png')}
    site_for['grail']='civic';z_for={n:s['z'] for n,s in traces['sites'].items()}
    if set(states)!=set(town['buildings']):raise ValueError('DMC1 native state closure differs: '+str(set(states)^set(town['buildings'])))
    records=[]
    for key,(raw_frame,mask) in list(states.items()):
        # Canonical invisible RGB is zero, matching the actual raster converter's
        # transparent-canvas alpha composition. This changes no visible pixel.
        frame=Image.new('RGBA',SIZE);frame.alpha_composite(raw_frame);states[key]=(frame,mask)
        if frame.size!=SIZE or mask.size!=SIZE or any(mask.histogram()[1:255]):raise ValueError('Invalid native state geometry')
        if ImageChops.subtract(mask,binary(frame.getchannel('A'))).getbbox():raise ValueError('Architecture outside body: '+key)
        folder=output/'states'/key;folder.mkdir(parents=True)
        frame.save(folder/'frame.png');mask.save(folder/'architecture-mask.png')
        area=Image.new('RGBA',SIZE,(255,255,255,0));area.putalpha(mask);area.save(folder/'area.png');border(mask).save(folder/'border.png')
        box=frame.getchannel('A').getbbox();crop=(max(0,box[0]-1),max(0,box[1]-1),min(800,box[2]+1),min(374,box[3]+1))
        frame.crop(crop).save(folder/'prepared-master.png')
        site=site_for[key];depth=12 if key=='grail' else z_for[site];town['structures'][key]['z']=depth
        records.append({'state':key,'site':site,'z':depth,'crop_box_xyxy':list(crop),'composition_box_xywh':[crop[0],crop[1],crop[2]-crop[0],crop[3]-crop[1]],'frame_sha256':sha(folder/'frame.png'),'architecture_mask_sha256':sha(folder/'architecture-mask.png'),'area_sha256':sha(folder/'area.png'),'border_sha256':sha(folder/'border.png'),'prepared_master_sha256':sha(folder/'prepared-master.png'),'provenance':provenance[key]})
    background.save(output/'background.png');dump(output/'factions-candidate.json',factions)
    all_built=set(states)-{'grail'};standard={'tavern','blacksmith','marketplace','resourceSilo','special2','special3'}
    cases={'empty':set(),'early':{'villageHall','tavern','blacksmith','marketplace','resourceSilo','dwellingLvl1','dwellingLvl2'},'developed':standard|{'townHall','citadel','mageGuild2','special1','special4'}|{f'dwellingLvl{i}' for i in range(1,8)},'fully-built-coastal':all_built,'fully-built-inland':all_built-{'ship','shipyard'},'grail-coastal':set(states)}
    views={}
    for label,built in cases.items():
        scene=background.copy();effective=effective_faction(factions['demacia'])['town'];selected=visible(effective,built)
        for key in sorted(selected,key=lambda k:town['structures'][k]['z']):scene.alpha_composite(states[key][0])
        scene.save(output/(label+'.png'));views[label]={'visible_states':selected,'sha256':sha(output/(label+'.png'))}
        if label=='fully-built-coastal' and ImageChops.difference(scene.convert('RGB'),reference.convert('RGB')).getbbox():raise ValueError('Actual native visibility differs from approved fully built scene')
    for key,(frame,mask) in states.items():
        alone=background.copy();alone.alpha_composite(frame);alone.save(output/'states'/key/'alone.png')
    sheet=Image.new('RGB',(1600,((len(records)+3)//4)*190),(29,31,34));d=ImageDraw.Draw(sheet)
    for i,row in enumerate(sorted(records,key=lambda q:(q['site'],q['state']))):
        frame=load(output/'states'/row['state']/'frame.png');box=frame.getchannel('A').getbbox();tile=frame.crop(box);tile.thumbnail((390,160),Image.Resampling.NEAREST)
        x=i%4*400;y=i//4*190;sheet.paste(tile,(x,y+25),tile);d.text((x+4,y+4),row['state'],fill='white')
    sheet.save(output/'all-35-states.png')
    receipt={'status':'authored configuration candidate','runtime_verified':False,'selected':False,'native_canvas':list(SIZE),'ordinary_land_sites':16,'optional_coast':1,'states':records,'views':views,'approved_full_coastal_pixels_exact':True,'geometry_receipt_sha256':sha(GEOMETRY/'receipt.json'),'earlier_receipt_sha256':sha(EARLIER/'receipt.json')}
    dump(output/'receipt.json',receipt);return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=assemble(a.output.resolve());print(json.dumps({'states':len(r['states']),'approved_full_coastal_pixels_exact':r['approved_full_coastal_pixels_exact']},indent=2))
