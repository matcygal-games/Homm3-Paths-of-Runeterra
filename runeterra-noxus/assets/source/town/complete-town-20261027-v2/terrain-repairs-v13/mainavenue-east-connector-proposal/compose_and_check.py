"""Crop/fit genuine public stair paintings, assemble isolated V12 proposal previews."""
from pathlib import Path
import hashlib,json,argparse
from PIL import Image,ImageOps,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent;TOWN=HERE.parents[1];ROOT=TOWN.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2/mainavenue-east-connector-proposal'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',type=int,choices=(1,2),default=1);v=ap.parse_args().version
    REPORT.mkdir(parents=True,exist_ok=True)
    base=TOWN/'terrain/final-native-v12-proposal.png';assert sha(base)=='d594523cc2d00e0fc4f372e8de5e349496bf675f831d6bc9fd47ef7ee2cfee3f'
    bg=Image.open(base).convert('RGBA');merged=bg.copy();records=[];union=Image.new('L',bg.size)
    guide=TOWN/'geometry-final-v2/connector-source-guide-v12-v2';body=Image.open(guide/'all36-actual-body.png').convert('L');roots=Image.open(guide/'all36-actual-structural-contact.png').convert('L')
    for side,box in [('east',(414,168,445,186)),('west',(0,130,10,155 if v==2 else 148))]:
        source=HERE/f'{side}-master-v1.png';im=Image.open(source).convert('RGBA');source_crop=(0,0,im.width,im.height)
        if side=='west':
            source_crop=(0,0,826,im.height);im=im.crop(source_crop)
        native=ImageOps.fit(im,(box[2]-box[0],18),method=Image.Resampling.LANCZOS);extension=None
        if side=='west' and v==2:
            canvas=Image.new('RGBA',(10,25));canvas.alpha_composite(native)
            landing_crop=(0,1160,826,1422);landing=ImageOps.fit(Image.open(source).convert('RGBA').crop(landing_crop),(10,7),method=Image.Resampling.LANCZOS)
            alpha=Image.new('L',(10,7));draw=ImageDraw.Draw(alpha)
            for row,last in enumerate([9,9,9,7,5,3,3]):draw.line((0,row,last,row),fill=255)
            landing.putalpha(alpha);canvas.alpha_composite(landing,(0,18));native=canvas
            extension={'genuine_existing_source_crop':landing_crop,'native_rectangle':[0,148,10,155],'last_painted_x_per_row148_to154':[9,9,9,7,5,3,3],'purpose':'Actual painted bottom landing across independently confirmed vegetation/wall gap to real Civic pavingx0..3,y153..154; exact UpKnife body excluded.'}
        assert ImageChops.multiply(body.crop(box),native.getchannel('A')).getbbox() is None;assert ImageChops.multiply(roots.crop(box),native.getchannel('A')).getbbox() is None
        native.save(HERE/f'{side}-native-v{v}.png');merged.alpha_composite(native,box[:2]);union.paste(native.getchannel('A'),box[:2])
        records.append({'side':side,'master':ref(source),'source_crop':source_crop,'native_patch':ref(HERE/f'{side}-native-v{v}.png'),'native_box':box,'body_overlap_pixels':0,'structural_contact_overlap_pixels':0,'alpha_extrema':native.getchannel('A').getextrema(),'bottom_landing_extension':extension,'conversion':'Exact genuine painted source crop; uniform coverfit LANCZOS; no artistic raster edits.'})
    merged.save(HERE/f'terrain-two-connectors-v{v}.png')
    diff=ImageChops.difference(bg.convert('RGB'),merged.convert('RGB'));outside=diff.copy();outside.paste((0,0,0),(0,0),union);assert outside.getbbox() is None
    selection=json.loads((TOWN/'candidate-final-v5/selection.json').read_text());index=TOWN/'native-transforms-v13/states.json';states=json.loads(index.read_text())['states'];rows={r['state']:r for r in states};pins=[]
    for row in states:
        for key in ('frame','painted_master'):
            p=ROOT/row[key]['path'];assert sha(p)==row[key]['sha256'];pins.append(ref(p))
        for role in ('body_mask','foundation_mask'):
            p=ROOT/row[role]['path'];assert sha(p)==row[role]['sha256']
            actual=Image.open(p).convert('L')
            assert ImageChops.multiply(actual,union).getbbox() is None,(row['state'],role)
    for mode in ('empty','full','base','early','east-early','west-early'):
        chosen=[] if mode=='empty' else [site['states'][0] if mode=='base' else site['top'] for site in selection['sites'] if site['id'] not in ('coast','grail')]
        if mode in ('early','east-early','west-early'):chosen=['villageHall','fort','dwellingLvl1','tavern']
        if mode=='east-early':chosen+=['dwellingLvl4','dwellingLvl7']
        if mode=='west-early':chosen+=['special1','dwellingLvl3']
        im=merged.copy()
        for state in sorted(chosen,key=lambda k:rows[k]['native_z']):im.alpha_composite(Image.open(ROOT/rows[state]['frame']['path']).convert('RGBA'))
        im.save(REPORT/f'{mode}-native-v{v}.png')
        for side,box in [('east',(400,155,460,201)),('west',(0,112,45,160))]:im.crop(box).resize(((box[2]-box[0])*12,(box[3]-box[1])*12),Image.Resampling.NEAREST).save(REPORT/f'{mode}-{side}-detail12x-v{v}.png')
    original=ROOT/'build/reports/complete-town-20261027-v2/final-v3/extracted-original-castle-source-assembly.png';board=Image.new('RGB',(1600,394),(16,16,16));board.paste(Image.open(original).convert('RGB'),(0,20));board.paste(Image.open(REPORT/f'full-native-v{v}.png').convert('RGB'),(800,20));d=ImageDraw.Draw(board);d.text((3,3),'Actual original HoMM3 Castle source assembly; native800x374',fill='white');d.text((803,3),'Noxus isolated public stairs proposal, V13 architecture on V12 terrain; no runtime claim',fill='white');board.save(REPORT/f'actual-original-native-comparison-v{v}.png')
    receipt={'status':'design proposal','base':ref(base),'source_index':ref(index),'geometry_guide':ref(guide/'index.json'),'script':ref(Path(__file__)),'patches':records,'proposal':ref(HERE/f'terrain-two-connectors-v{v}.png'),'outside_union_difference_bbox':outside.getbbox(),'all36_selected_frames_and36_raw_masters_match_pins':len(pins)==72,'preserved_frame_master_pins':pins,'independent_actualflight_review_pending':True,'source_owner_integration_pending':True,'native_verified':False,'release_accepted':False}
    (HERE/f'recipe-and-checks-v{v}.json').write_text(json.dumps(receipt,indent=2)+'\n');(REPORT/f'recipe-and-checks-v{v}.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'proposal':receipt['proposal'],'patches':records,'outside_exact':True,'all72_building_pins_match':len(pins)==72}))
if __name__=='__main__':main()
