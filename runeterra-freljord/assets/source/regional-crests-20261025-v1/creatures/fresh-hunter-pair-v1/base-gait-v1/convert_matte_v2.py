"""Technical background cutout successor, before crest assembly; raw paint preserved."""
from pathlib import Path
from collections import deque
import hashlib,importlib.util,io,json
from PIL import Image
S=Path(__file__).resolve().parent;P=S.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clear_border_matte(im):
    """Clear border-connected transparent/near-black matte, not body material colour."""
    out=im.copy();px=out.load();w,h=im.size
    todo=deque([(x,y) for x in range(w) for y in (0,h-1)]+[(x,y) for y in range(h) for x in (0,w-1)])
    seen=set();changed=0;opaque_changes=0
    while todo:
        x,y=todo.popleft()
        if (x,y) in seen or not(0<=x<w and 0<=y<h):continue
        seen.add((x,y));c=px[x,y]
        if c[3]>8 and max(c[:3])>12:continue
        if c[3]:changed+=1;opaque_changes+=c[3]>=128;px[x,y]=c[:3]+(0,)
        todo.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
    assert all(a[:3]==b[:3] for a,b in zip(im.getdata(),out.getdata()))
    assert all(a==b for a,b in zip(im.getdata(),out.getdata()) if a[3]>8 and max(a[:3])>12)
    return out,changed,opaque_changes
def main():
    helper=S/'convert.py'
    if sha(helper)!='a0cd5b1a699e1ad0cdbb7d741fbb6104c3914e94a9800da6d29b4a667b5cf3f9':raise ValueError('Old converter changed before import')
    spec=importlib.util.spec_from_file_location('base_gait_v1',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    records=[]
    for i,name in enumerate(m.NAMES):
        source=S/f'g00-f{i:03d}-raw.png';im=Image.open(source).convert('RGBA');cleaned,changed,opaque=clear_border_matte(im)
        path=S/f'g00-f{i:03d}-matte-v2.png';m.png(path,cleaned)
        records.append({'frame':i,'pose':name,'source':{'path':source.relative_to(P).as_posix(),'sha256':sha(source)},'output':{'path':path.relative_to(P).as_posix(),'sha256':sha(path)},'changed_alpha_pixels':changed,'changed_opaque_nearblack_background_pixels':opaque,'material_RGB_exact':True,'all_non_matte_material_alpha_exact':True})
    receipt={'status':'design proposal','scope':'Unselected background-only comparison successor, no body palette/pose/filter/scale change','method':'Borderflood through alpha<=8 or RGBmax<=12 only. Clear alpha of reached background pixels; preserve every RGB and every alpha of material with RGBmax>12 andalpha>8. Raw generated paint and sourcealphas retained.','producer_sha256':sha(Path(__file__)),'records':records,'native_execution':False,'release_accepted':False}
    path=S/'matte-comparison-v2.json';data=(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()
    if path.exists() and path.read_bytes()!=data:raise ValueError('Frozen receipt differs')
    path.write_bytes(data)
if __name__=='__main__':main()
