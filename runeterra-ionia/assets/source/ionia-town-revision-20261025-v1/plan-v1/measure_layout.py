"""Diagnostic planning only: reuse exact selected painted masters, no terrain artwork."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw,ImageFont
import numpy as np
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent;R=W/'build/reports/ionia-town-revision-20261025-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(p):return p.relative_to(P).as_posix()
def crop(master):
    im=Image.open(master).convert('RGBA');box=im.getchannel('A').point(lambda v:255 if v>16 else 0).getbbox()
    return im.crop(box),box
def transform(key,site,record):
    im,box=crop(P/record['master']['path']);x,y,w,h=site['box'];scale=min(w/im.width,h/im.height);size=[max(1,round(im.width*scale)),max(1,round(im.height*scale))];origin=[x+(w-size[0])//2,y+h-size[1]];piece=im.resize(size,Image.Resampling.LANCZOS);layer=Image.new('RGBA',(800,374));layer.alpha_composite(piece,tuple(origin));return layer,{'master_crop':box,'uniform_scale':scale,'native_size':size,'native_origin':origin}
def main():
    version=sys.argv[1] if len(sys.argv)>1 else 'v1';plan_path=S/('site-plan-'+version+'.json');layout=json.loads(plan_path.read_text());inventory=json.loads((R/'selected-inventory-v1.json').read_text());records={e['key']:e for e in inventory['structures']};states={};layers={}
    for name,site in layout['sites'].items():
        for key in site['keys']:
            record=records[key]
            if key in layout.get('master_overrides',{}):
                master=P/layout['master_overrides'][key];record={**record,'master':{'path':relative(master),'sha256':sha(master)}}
            layer,t=transform(key,site,record);a=np.asarray(layer)[:,:,3];ys,xs=np.where(a>=128);bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
            states[key]={'site':name,'master':record['master'],**t,'bbox_alpha128':bbox,'alpha128_area':int((a>=128).sum()),'alpha17_area':int((a>=17).sum()),'full_alpha_area':int((a>0).sum())};layers[key]=layer
    # All permutations of construction states on different sites, not just final masks.
    overlaps=[];sites=list(layout['sites'].items())
    for index,(one,a) in enumerate(sites):
        for two,b in sites[index+1:]:
            worst=(0,None,None);soft=0
            for ka in a['keys']:
                aa=np.asarray(layers[ka])[:,:,3]
                for kb in b['keys']:
                    ab=np.asarray(layers[kb])[:,:,3];n=int(((aa>=128)&(ab>=128)).sum())
                    soft=max(soft,int(((aa>=17)&(ab>=17)).sum()))
                    if n>worst[0]:worst=(n,ka,kb)
            if worst[0] or soft:overlaps.append({'sites':[one,two],'opaque_pixels':worst[0],'worst_states':list(worst[1:]),'alpha17_pixels':soft})
    background=Image.new('RGBA',(800,374),(122,129,125,255))
    draw=ImageDraw.Draw(background)
    for name,site in layout['sites'].items():
        x,y,w,h=site['box'];draw.rectangle((x,y,x+w-1,y+h-1),outline=(235,210,160,255));draw.text((x+2,y+2),name,fill='white')
    background.convert('RGB').save(R/('measured-site-reservations-'+version+'.png'))
    composition=Image.new('RGBA',(800,374),(114,123,119,255));d=ImageDraw.Draw(composition)
    for name,site in sorted(layout['sites'].items(),key=lambda item:item[1]['z']):
        if name in ('coast','grail'):continue
        composition.alpha_composite(layers[site['keys'][-1]])
    composition.convert('RGB').save(R/('measured-existing-buildings-plan-'+version+'.png'))
    report={'status':'design proposal','scope':'Measured geometry diagnostic; flatbackground/grid are planning tools, never final terrain art or generationguide buildings','site_plan_sha256':sha(plan_path),'states':states,'cross_site_opaque_intersections':overlaps,'ordinary_site_count':sum(k not in ('coast','grail') for k in layout['sites']),'state_count':len(states)}
    (R/('measured-layout-'+version+'.json')).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'states':len(states),'intersections':overlaps}))
if __name__=='__main__':main()
