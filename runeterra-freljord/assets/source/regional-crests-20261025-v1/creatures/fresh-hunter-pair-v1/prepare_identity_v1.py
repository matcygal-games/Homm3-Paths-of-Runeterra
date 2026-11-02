"""Fresh painted identity pilot; only generated cloth patch is assembled over clean body."""
from pathlib import Path
import hashlib, io, json
from PIL import Image, ImageDraw
S=Path(__file__).resolve().parent
P=S.parents[4]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def png(p, im):
    b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False)
    if p.exists() and p.read_bytes()!=b.getvalue():raise ValueError('Frozen output differs')
    p.write_bytes(b.getvalue())
def main():
    d=S/'iceHunter';original=Image.open(d/'identity-raw-v1.png').convert('RGBA');edited=Image.open(d/'identity-crest-edit-raw-v2.png').convert('RGBA')
    # Technical extraction of genuinely painted cloth only; never synthesize a glyph.
    crop=(550,325,665,475)
    mask=Image.new('L',edited.size)
    ImageDraw.Draw(mask).polygon([(558,340),(638,329),(651,421),(633,463),(582,443)],fill=255)
    material=edited.copy();material.putalpha(mask);material=material.crop(crop)
    png(d/'painted-cloth-material-v1.png',material)
    # Same material tilt/shape, no body resampling. Broader cloth remains on original chest.
    material=material.resize((140,182),Image.Resampling.LANCZOS)
    layer=Image.new('RGBA',original.size);layer.alpha_composite(material,(548,386))
    allowed=Image.new('L',original.size);out=original.copy()
    for y in range(386,568):
        for x in range(548,688):
            ink=layer.getpixel((x,y));old=original.getpixel((x,y))
            if ink[3] and old[3]>=248:
                a=ink[3]/255
                out.putpixel((x,y),tuple(round(ink[c]*a+old[c]*(1-a)) for c in range(3))+(old[3],))
                allowed.putpixel((x,y),255)
    assert out.getchannel('A').tobytes()==original.getchannel('A').tobytes()
    before,after,maskbytes=original.tobytes(),out.tobytes(),allowed.tobytes()
    assert all(before[4*i:4*i+4]==after[4*i:4*i+4] for i,m in enumerate(maskbytes) if not m)
    png(d/'identity-painted-v1.png',out);png(d/'identity-cloth-mask-v1.png',allowed)
    # Uniform whole-body conversion. Native nearest sampling applies solely to painted cloth.
    scale=.06;size=tuple(round(n*scale) for n in original.size);position=(197-round(520*scale),266-round(1425*scale))
    body=original.resize(size,Image.Resampling.LANCZOS);body_native=Image.new('RGBA',(450,400));body_native.alpha_composite(body,position)
    patch=out.resize(size,Image.Resampling.NEAREST);patchmask=allowed.resize(size,Image.Resampling.NEAREST)
    native=Image.new('RGBA',(450,400));native.alpha_composite(body,position)
    for y in range(size[1]):
        for x in range(size[0]):
            if patchmask.getpixel((x,y)):
                px=x+position[0];py=y+position[1];a=native.getpixel((px,py))[3]
                native.putpixel((px,py),patch.getpixel((x,y))[:3]+(a,))
    png(d/'holding-native-pilot-v1.png',native)
    png(d/'holding-native-body-only-v1.png',body_native)
    names=['identity-raw-v1.png','identity-crest-edit-raw-v2.png','identity-prompt-v1.txt','identity-crest-prompt-v2.txt','identity-generation-v1.json','painted-cloth-material-v1.png','identity-painted-v1.png','identity-cloth-mask-v1.png','holding-native-pilot-v1.png','holding-native-body-only-v1.png']
    receipt={'status':'design proposal','scope':'Single fresh identity pilot only, no action family/recipes selected','root':[197,266],'source_floor_root':[520,1425],'uniform_scale':scale,'native_size':[450,400],'material_crop':list(crop),'material_target_top_left':[548,386],'material_target_size':[140,182],'body_alpha_exact':True,'outside_cloth_mask_RGBA_exact':True,'crest_only_native_nearest':True,'native_execution':False,'release_accepted':False,'producer':{'path':Path(__file__).relative_to(P).as_posix(),'sha256':sha(Path(__file__))},'source_files':[{ 'path':(d/name).relative_to(P).as_posix(),'sha256':sha(d/name)} for name in names]}
    path=d/'identity-assembly-v1.json';data=(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()
    if path.exists() and path.read_bytes()!=data:raise ValueError('Frozen receipt differs')
    path.write_bytes(data)
if __name__=='__main__':main()
