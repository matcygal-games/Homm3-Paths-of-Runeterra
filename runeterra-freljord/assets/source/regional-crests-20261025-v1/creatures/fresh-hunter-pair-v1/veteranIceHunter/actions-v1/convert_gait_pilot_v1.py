"""Uniform native-camera pilot only; no body edits, limb warps or glyph drawing."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
REPORT=ROOT/'build/reports/regional-crests-20261025-v1/freljord-unit-art/fresh-hunter-pair-v1/upgrade-actions-v1'
SCALE=.06
SOURCE_ROOT=(520,1485)
NATIVE_ROOT=(197,266)
CANVAS=(450,400)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def convert(p):
    im=Image.open(p).convert('RGBA')
    size=tuple(round(x*SCALE) for x in im.size)
    reduced=im.resize(size,Image.Resampling.LANCZOS)
    native=Image.new('RGBA',CANVAS)
    offset=tuple(NATIVE_ROOT[i]-round(SOURCE_ROOT[i]*SCALE) for i in (0,1))
    native.alpha_composite(reduced,offset)
    return native

def main():
    rows=[]
    items=[('standing clean identity',HERE.parent/'identity-raw-v1.png'),('contact request near V1',HERE/'walk-near-contact-raw-v1.png'),('contact far V1',HERE/'walk-far-contact-raw-v1.png'),('crossover near V2',HERE/'walk-near-crossover-raw-v2.png')]
    board=Image.new('RGBA',(800,700),(61,61,61,255));d=ImageDraw.Draw(board)
    for i,(label,p) in enumerate(items):
        native=convert(p);out=HERE/(p.stem+'-native-pilot.png')
        if p.parent==HERE:native.save(out)
        else:out=REPORT/'identity-native-comparison.png';native.save(out)
        x=(i%2)*400;y=(i//2)*350
        d.text((x+8,y+8),label,fill='white')
        tight=native.crop((120,170,270,300))
        board.alpha_composite(tight,(x+8,y+28))
        board.alpha_composite(tight.resize((300,260),Image.Resampling.NEAREST),(x+95,y+82))
        rows.append({'label':label,'raw':pin(p),'native':pin(out),'source_size':list(Image.open(p).size),'native_alpha_bbox':native.getchannel('A').getbbox(),'repeat_decoded_rgba_exact':convert(p).tobytes()==native.tobytes()})
    proof=REPORT/'upgrade-gait-pilot-native1x-and-2x-v1.png';board.save(proof)
    report={'status':'design proposal','method':'Each raw source resized once uniformly .06 LANCZOS and alpha-composited at fixed camera offset; no alpha edits, per-pose fitting, body filters, glyph synthesis or limb/body deformation. Labels do not establish anatomical support.','canvas':list(CANVAS),'scale':SCALE,'source_camera_root':list(SOURCE_ROOT),'native_root':list(NATIVE_ROOT),'producer':pin(Path(__file__)),'frames':rows,'proof':pin(proof),'native_execution':False,'selected':False,'release_accepted':False}
    (REPORT/'pilot-conversion-v1.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'proof':pin(proof),'conversion':pin(REPORT/'pilot-conversion-v1.json')},indent=2))

if __name__=='__main__':main()
