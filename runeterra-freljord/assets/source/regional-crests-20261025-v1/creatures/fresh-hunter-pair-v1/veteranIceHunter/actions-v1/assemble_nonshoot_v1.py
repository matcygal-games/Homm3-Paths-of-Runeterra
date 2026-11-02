"""Portable nonshoot painted key conversion. Raw alpha/body pixels never edited."""
from pathlib import Path
import argparse,json,hashlib
from PIL import Image,ImageDraw,ImageOps
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
MOD=ROOT/'runeterra-freljord'
REPORT=ROOT/'build/reports/regional-crests-20261025-v1/freljord-unit-art/fresh-hunter-pair-v1/upgrade-actions-v1'
NAMES=['fidget-look','equipment-check','hit-recoil','defend-brace','death-kneel','death-fall','death-prone','turn-nearfront','turn-front','knife-anticipation','knife-up-contact','knife-front-contact','knife-down-contact']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def convert(p):
    im=Image.open(p).convert('RGBA');assert im.size==(1024,1536)
    native=Image.new('RGBA',(450,400));native.alpha_composite(im.resize((61,92),Image.Resampling.LANCZOS),(166,177));return native
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--first-three',action='store_true');args=parser.parse_args()
    names=NAMES[:3] if args.first_three else NAMES;suffix='first-three-v1' if args.first_three else 'thirteen-v1'
    rows=[];deps={Path(__file__)};outdir=HERE/'native-nonshoot-v1';outdir.mkdir(exist_ok=True)
    cols=3;board=Image.new('RGBA',(cols*350,((len(names)+2)//3)*350),(60,60,60,255));draw=ImageDraw.Draw(board)
    for i,name in enumerate(names):
        stem='nonshoot-'+name;meta=HERE/f'{stem}-generation-v1.json';record=json.loads(meta.read_text());deps.add(meta)
        for field in ['raw','prompt','identity_ancestry']:
            path=MOD/record[field]['path'];assert sha(path)==record[field]['sha256'];deps.add(path)
        for ref in record['input_references']:
            if ref['included_in_source_package']:
                path=MOD/ref['path'];assert sha(path)==ref['sha256'];deps.add(path)
        raw=HERE/f'{stem}-raw-v1.png';native=convert(raw);assert native.tobytes()==convert(raw).tobytes();opposite=ImageOps.mirror(native);assert ImageOps.mirror(opposite).tobytes()==native.tobytes()
        target=outdir/f'{name}-right.png';left=outdir/f'{name}-left.png';native.save(target);opposite.save(left)
        solid=native.getchannel('A').point(lambda a:255 if a>=128 else 0)
        rows.append({'action_key':name,'raw':pin(raw),'generation':pin(meta),'right':pin(target),'left':pin(left),'alpha128_bbox':solid.getbbox(),'raw_body_alpha_edited':False,'repeat_decoded_exact':True,'mirror_roundtrip_exact':True})
        x=i%cols*350;y=i//cols*350;draw.text((x+8,y+8),name,fill='white');tight=native.crop((120,165,280,285));board.alpha_composite(tight,(x+4,y+27));draw.line((x+4,y+128,x+164,y+128),fill=(100,80,80,255));draw.ellipse((x+79,y+126,x+83,y+130),fill='red');board.alpha_composite(tight.resize((320,240),Image.Resampling.NEAREST),(x+20,y+105))
    proof=REPORT/f'upgrade-nonshoot-native1x-and-2x-{suffix}.png';board.save(proof)
    ledger={'status':'design proposal','selected':False,'scope':'Genuine painted action keys, not complete animation interpolation or native acceptance.','canvas':[450,400],'scale':.06,'source_camera_root':[520,1485],'native_root':[197,266],'left_mirrored_root':[252,266],'method':'Once uniform LANCZOS1024x1536 to61x92 at166,177; no perpose fitting, bodywarps, alpha edits or glyphdrawing. Left mirrors wholecanvas.','pose_count':len(rows),'frames':rows,'direct_inputs':[pin(p) for p in sorted(deps)],'proof':pin(proof),'repeat_decoded_checks':len(rows),'mirror_roundtrip_checks':len(rows),'native_execution':False,'release_accepted':False}
    path=REPORT/f'nonshoot-assembly-{suffix}.json';path.write_text(json.dumps(ledger,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps({'proof':pin(proof),'ledger':pin(path)},indent=2))
if __name__=='__main__':main()
