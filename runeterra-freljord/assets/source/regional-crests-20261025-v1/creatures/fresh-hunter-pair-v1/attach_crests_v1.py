"""Genuine painted regional cloth planes on new clean natives. Never alter body geometry."""
from pathlib import Path
import hashlib,importlib.util,io,json,sys
from PIL import Image,ImageDraw
S=Path(__file__).resolve().parent;P=S.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(item):
    name=item['path']
    if ':' in name or '\\' in name or any(x in ('','.','..') for x in name.split('/')):raise ValueError('Unsafe local path')
    p=(P/name).resolve()
    if not p.is_relative_to(P) or not p.is_file() or sha(p)!=item['sha256']:raise ValueError('Missing/stale attachment input '+name)
    return p
def png(path,im):
    path.parent.mkdir(parents=True,exist_ok=True);b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False)
    if path.exists() and path.read_bytes()!=b.getvalue():raise ValueError('Frozen source output differs '+str(path))
    path.write_bytes(b.getvalue())
def assemble(plan):
    data=json.loads(plan.read_text());helper=local(data['painted_material_helper'])
    spec=importlib.util.spec_from_file_location('native_painted_cloth_helper',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    tile=Image.open(local(data['painted_material'])).convert('RGBA');records=[]
    for e in data['contexts']:
        body=Image.open(local(e['body'])).convert('RGBA');paint=m.warp_material(tile,e['cloth_quad'],body.size,'nearest')
        polygon=Image.new('L',body.size);draw=ImageDraw.Draw(polygon);draw.polygon([tuple(x) for x in e['cloth_quad']],fill=255)
        for occluder in e.get('occluders',[]):draw.polygon([tuple(x) for x in occluder],fill=0)
        after=body.copy();mask=Image.new('L',body.size)
        for y in range(body.height):
            for x in range(body.width):
                before=body.getpixel((x,y));ink=paint.getpixel((x,y))
                if polygon.getpixel((x,y)) and ink[3] and before[3]>=248:
                    a=ink[3]/255;after.putpixel((x,y),tuple(round(ink[c]*a+before[c]*(1-a)) for c in range(3))+(before[3],));mask.putpixel((x,y),255)
        assert after.getchannel('A').tobytes()==body.getchannel('A').tobytes()
        beforebytes,afterbytes=body.tobytes(),after.tobytes()
        assert all(beforebytes[i*4:i*4+4]==afterbytes[i*4:i*4+4] for i,v in enumerate(mask.tobytes()) if not v)
        output=P/e['output'];maskpath=P/e['mask'];png(output,after);png(maskpath,mask)
        records.append({**e,'output_sha256':sha(output),'mask_sha256':sha(maskpath),'original_body_alpha_exact':True,'outside_physical_cloth_mask_RGBA_exact':True,'changed_pixels':sum(beforebytes[i*4:i*4+4]!=afterbytes[i*4:i*4+4] for i in range(body.width*body.height))})
    return {'status':'design proposal','plan':{'path':plan.relative_to(P).as_posix(),'sha256':sha(plan)},'producer':{'path':Path(__file__).relative_to(P).as_posix(),'sha256':sha(Path(__file__))},'records':records,'native_execution':False,'release_accepted':False}
if __name__=='__main__':
    path=Path(sys.argv[1]).resolve()
    if not path.is_relative_to(P):raise ValueError('Plan outside project')
    receipt=assemble(path);target=path.with_name(path.stem+'-assembly.json');b=(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()
    if target.exists() and target.read_bytes()!=b:raise ValueError('Frozen receipt differs')
    target.write_bytes(b)
