"""Six genuine raw painted gait phases; uniform conversion, diagnostic proofs only."""
from pathlib import Path
import hashlib,json,importlib.util
from PIL import Image,ImageDraw,ImageOps

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
MOD=ROOT/'runeterra-freljord'
REPORT=ROOT/'build/reports/regional-crests-20261025-v1/freljord-unit-art/fresh-hunter-pair-v1/upgrade-actions-v1'
PHASES=[('far-contact','walk-far-contact','v1'),('far-down','walk-far-down','v1'),('near-passing','walk-near-passing','v1'),('near-contact','walk-near-crossover','v2'),('near-down','walk-near-down','v1'),('far-passing','walk-far-passing','v1')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    spec=importlib.util.spec_from_file_location('gait_camera',HERE/'convert_gait_pilot_v1.py');camera=importlib.util.module_from_spec(spec);spec.loader.exec_module(camera)
    direct={HERE/'convert_gait_pilot_v1.py',Path(__file__)}
    frames=[];rows=[];outdir=HERE/'native-gait-v1';outdir.mkdir(exist_ok=True)
    board=Image.new('RGBA',(1050,700),(62,62,62,255));d=ImageDraw.Draw(board)
    for i,(phase,stem,v) in enumerate(PHASES):
        metadata=HERE/f'{stem}-generation-{v}.json';record=json.loads(metadata.read_text());direct.add(metadata)
        for key in ['raw','prompt','identity_ancestry']:
            q=MOD/record[key]['path'];assert sha(q)==record[key]['sha256'];direct.add(q)
        for ref in record['input_references']:
            if ref['included_in_source_package']:
                q=MOD/ref['path'];assert sha(q)==ref['sha256'];direct.add(q)
        raw=HERE/f'{stem}-raw-{v}.png';native=camera.convert(raw);repeat=camera.convert(raw);assert repeat.tobytes()==native.tobytes()
        target=outdir/f'g00-f{i:03d}.png';native.save(target)
        opposite=ImageOps.mirror(native);left=outdir/f'g00-f{i:03d}-left.png';opposite.save(left)
        assert ImageOps.mirror(opposite).tobytes()==native.tobytes()
        a=native.getchannel('A');solid=a.point(lambda x:255 if x>=128 else 0)
        rows.append({'index':i,'phase':phase,'raw':pin(raw),'generation':pin(metadata),'right':pin(target),'left':pin(left),'alpha128_bbox':solid.getbbox(),'source_camera_root':[520,1485],'native_root':[197,266],'uniform_scale':.06,'repeat_decoded_exact':True,'left_mirror_roundtrip_exact':True})
        frames.append(native)
        x=i*175;d.text((x+6,8),f'{i} {phase}',fill='white')
        tight=native.crop((120,170,270,300));board.alpha_composite(tight,(x+8,30))
        d.line((x+8,126,x+158,126),fill=(100,85,85,255));d.ellipse((x+83,124,x+87,128),fill='red')
        board.alpha_composite(tight.resize((150,130),Image.Resampling.NEAREST),(x+8,185))
        legs=native.crop((155,218,235,278)).resize((160,120),Image.Resampling.NEAREST);board.alpha_composite(legs,(x+5,350))
        lefttight=opposite.crop((180,170,330,300));board.alpha_composite(lefttight,(x+8,530));d.text((x+6,505),'derived left 1x',fill='white')
    proof=REPORT/'upgrade-walk-six-native-rootproof-v1.png';board.save(proof)
    gifs=[]
    for name,scale in [('native1x',1),('nearest3x',3)]:
        gifframes=[]
        for i,native in enumerate(frames):
            tile=Image.new('RGBA',(170,160),(62,62,62,255));tile.alpha_composite(native.crop((120,160,270,300)),(10,10));draw=ImageDraw.Draw(tile);draw.line((10,116,160,116),fill=(95,80,80,255));draw.ellipse((85,114,89,118),fill='red');draw.text((5,145),f'{i}: {PHASES[i][0]}',fill='white')
            if scale>1:tile=tile.resize((170*scale,160*scale),Image.Resampling.NEAREST)
            gifframes.append(tile.convert('RGB'))
        gif=REPORT/f'upgrade-walk-six-{name}-diagnostic-v1.gif';gifframes[0].save(gif,save_all=True,append_images=gifframes[1:],duration=160,loop=0,disposal=2);gifs.append(pin(gif))
    # Closure records the exact public inputs this assembler actually reads.
    report={'status':'design proposal','selected':False,'scope':'Six real gait action sources only; no shooting/reaction/death/turn/melee/portrait/map completion claimed.','method':'Uniform .06 LANCZOS body conversion at camera520,1485 to root197,266. Left is wholecanvas mirror; no limb warps, per-pose fitting, body filtering, alpha edits or code glyph.','frame_count':6,'canvas':[450,400],'source_camera_root':[520,1485],'native_root':[197,266],'left_mirrored_root':[252,266],'frames':rows,'direct_inputs':[pin(q) for q in sorted(direct)],'proof':pin(proof),'gifs':gifs,'gif_duration_ms_per_frame':160,'gif_timing':'Diagnostic only, not native VCMI timing; unchanged content scalars attack1/walk1/idle10.','repeated_conversion_checks_executed':6,'mirror_roundtrip_checks_executed':6,'native_execution':False,'human_art_accepted':False,'release_accepted':False}
    (REPORT/'walk-six-assembly-v1.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'proof':pin(proof),'ledger':pin(REPORT/'walk-six-assembly-v1.json'),'gifs':gifs},indent=2))
if __name__=='__main__':main()
