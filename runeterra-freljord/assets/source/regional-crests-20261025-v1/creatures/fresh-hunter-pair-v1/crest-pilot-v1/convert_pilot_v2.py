"""Fixed new pair camera; genuine painted material only on authored native cloth planes."""
from pathlib import Path
import hashlib, importlib.util, io, json
from PIL import Image, ImageDraw
S=Path(__file__).resolve().parent;P=S.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def png(path,im):
    b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False)
    if path.exists() and path.read_bytes()!=b.getvalue():raise ValueError('Frozen output differs')
    path.write_bytes(b.getvalue())
def main():
    config=json.loads((S/'planes-v2.json').read_text())
    helper=P/config['painted_material_helper']['path']
    if sha(helper)!=config['painted_material_helper']['sha256']:raise ValueError('Stale helper before import')
    spec=importlib.util.spec_from_file_location('frozen_painted_material',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    tile=P/config['painted_material']['path']
    if sha(tile)!=config['painted_material']['sha256']:raise ValueError('Stale painted material')
    records=[]
    for entry in config['units']:
        raw=P/entry['raw']['path']
        if sha(raw)!=entry['raw']['sha256']:raise ValueError('Stale clean body')
        im=Image.open(raw).convert('RGBA');size=tuple(round(x*.06) for x in im.size)
        body=Image.new('RGBA',(450,400));body.alpha_composite(im.resize(size,Image.Resampling.LANCZOS),(166,177))
        field=m.warp_material(Image.open(tile).convert('RGBA'),entry['cloth_quad'],body.size,'nearest')
        polygon=Image.new('L',body.size);draw=ImageDraw.Draw(polygon);draw.polygon([tuple(x) for x in entry['cloth_quad']],fill=255)
        for poly in entry.get('occluders',[]):draw.polygon([tuple(x) for x in poly],fill=0)
        mask=Image.new('L',body.size);after=body.copy()
        for y in range(190,225):
            for x in range(190,225):
                before=body.getpixel((x,y));paint=field.getpixel((x,y))
                if polygon.getpixel((x,y)) and paint[3] and before[3]>=248:
                    a=paint[3]/255
                    after.putpixel((x,y),tuple(round(paint[c]*a+before[c]*(1-a)) for c in range(3))+(before[3],));mask.putpixel((x,y),255)
        assert after.getchannel('A').tobytes()==body.getchannel('A').tobytes()
        bb,aa=body.tobytes(),after.tobytes()
        assert all(bb[4*i:4*i+4]==aa[4*i:4*i+4] for i,v in enumerate(mask.tobytes()) if not v)
        unit=entry['unit'];png(S/(unit+'-body-v2.png'),body);png(S/(unit+'-crest-v2.png'),after);png(S/(unit+'-mask-v2.png'),mask)
        records.append({**entry,'native_body_sha256':sha(S/(unit+'-body-v2.png')),'native_crest_sha256':sha(S/(unit+'-crest-v2.png')),'mask_sha256':sha(S/(unit+'-mask-v2.png')),'alpha_exact':True,'exterior_RGBA_exact':True,'mask_area':sum(v>0 for v in mask.tobytes())})
    receipt={'status':'design proposal','scope':'Two newcleanpainted standing pilots only; no action/recipe selection','source_root':[520,1485],'native_root':[197,266],'fixed_scale':.06,'records':records,'native_execution':False,'release_accepted':False}
    path=S/'assembly-v2.json';data=(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()
    if path.exists() and path.read_bytes()!=data:raise ValueError('Frozen receipt differs')
    path.write_bytes(data)
if __name__=='__main__':main()
