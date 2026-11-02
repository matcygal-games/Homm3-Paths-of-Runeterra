"""New genuine painted base gait, fixed camera; raw and conservative matte comparison."""
from pathlib import Path
from collections import deque
import hashlib,io,json
from PIL import Image
S=Path(__file__).resolve().parent;P=S.parents[5];R=S.parent
NAMES=['walk-contact-a-v2','walk-far-down-base-raw-v1','walk-near-passing-base-raw-v1','walk-contact-b-v4','walk-near-down-base-raw-v1','walk-far-passing-base-raw-v1']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def png(p,im):
    b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False)
    if p.exists() and p.read_bytes()!=b.getvalue():raise ValueError('Frozen output differs')
    p.write_bytes(b.getvalue())
def clean_matte(im):
    """Technical alpha only. Never raise opacity, fit bounds or modify material RGB."""
    out=im.copy();px=out.load();remaining=set()
    for y in range(im.height):
        for x in range(im.width):
            c=px[x,y]
            if 0<c[3]<=8:px[x,y]=c[:3]+(0,)
            elif c[3]>8:remaining.add((x,y))
    removed_components=0
    while remaining:
        seed=remaining.pop();component=[seed];q=deque([seed]);maximum=px[seed][3]
        while q:
            x,y=q.popleft()
            for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
                n=(x+dx,y+dy)
                if n in remaining:remaining.remove(n);component.append(n);q.append(n);maximum=max(maximum,px[n][3])
        if maximum<128:
            removed_components+=1
            for point in component:px[point]=px[point][:3]+(0,)
    return out,removed_components
def main():
    records=[]
    for i,name in enumerate(NAMES):
        raw=R/'iceHunter'/(name+'.png');im=Image.open(raw).convert('RGBA')
        if im.size!=(1024,1536):raise ValueError('Source camera changed')
        body=Image.new('RGBA',(450,400));body.alpha_composite(im.resize((61,92),Image.Resampling.LANCZOS),(166,177))
        cleaned,removed=clean_matte(body)
        png(S/f'g00-f{i:03d}-raw.png',body);png(S/f'g00-f{i:03d}-matte.png',cleaned)
        changed=[(a,b) for a,b in zip(body.getdata(),cleaned.getdata()) if a!=b]
        assert all(a[:3]==b[:3] and a[3]<128 and b[3]==0 for a,b in changed)
        records.append({'frame':i,'pose':name,'raw_master':{'path':raw.relative_to(P).as_posix(),'sha256':sha(raw)},'raw_native_sha256':sha(S/f'g00-f{i:03d}-raw.png'),'matte_comparison_sha256':sha(S/f'g00-f{i:03d}-matte.png'),'matte_alpha_changed_pixels':len(changed),'removed_low_opacity_exterior_components':removed,'all_material_RGB_exact':True,'all_alpha128plus_exact':True})
    data={'status':'design proposal','scope':'Six clean base gait source pilots, no active selection. Matte cleanup is unselected comparison only.','fixed_source_root':[520,1485],'fixed_native_root':[197,266],'fixed_scale':.06,'raw_source_alpha_preserved_in_first_outputs':True,'matte_comparison_rule':'Clear only alpha1..8 and disconnected8-connected components whose maximumalpha is below128. Preserve every materialRGB and every alpha>=128 pixel; rawmaster unchanged. No bodycolour/style/pose filtering.','records':records,'native_execution':False,'release_accepted':False}
    path=S/'assembly-v1.json';b=(json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
    if path.exists() and path.read_bytes()!=b:raise ValueError('Frozen receipt differs')
    path.write_bytes(b)
if __name__=='__main__':main()
