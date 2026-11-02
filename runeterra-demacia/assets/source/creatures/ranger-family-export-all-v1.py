"""Measured fixed-camera source exports of the remaining Ranger actions."""
from pathlib import Path
import json
import sys

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'scripts'))
from creature_family_motion_art import calibrate_generation, export_generation, proof, write
from creature_padding import crop_padding

# Actually inspected upright/ready landmark frames. Coordinates on the512px
# review grid, except the explicitly recovered576px g05/upgradeg16 sheets.
# One scale applies to an ENTIRE action atlas, never fitted to each body pose.
CAMERAS = {
    'demacianRanger': {
        1:(3,41,470,265),3:(3,33,473,253),4:(3,60,475,256),5:(0,97,564,288),
        7:(0,46,502,280),8:(0,26,495,285),11:(0,71,504,260),12:(0,67,509,256),
        13:(0,71,501,275),14:(0,48,503,239),16:(0,59,503,241)},
    'veteranRanger': {
        1:(3,39,456,275),3:(3,38,459,268),4:(3,26,483,256),5:(0,86,561,288),
        7:(0,33,498,284),8:(0,65,504,270),11:(0,51,499,260),12:(0,35,486,265),
        13:(0,30,499,280),14:(0,46,506,246),16:(0,45,476,246)},
}
REPACKED = {('demacianRanger',5),('veteranRanger',5),('veteranRanger',16)}


def reviews(folder, group, result, version=3):
    count = len(result['frames']);board = Image.new('RGB',(count*140,300),'#303b35');draw=ImageDraw.Draw(board)
    draw.text((3,4),f'{result["unit"]} g{group:02} actual painted source; measured fixed camera/ground translation',fill='white')
    gif=[]
    for index,frame in enumerate(result['frames']):
        with Image.open(PROJECT/frame['output']) as native:
            crop=native.crop((135,165,275,295))
            for row,color in ((0,'#d6d6c6'),(1,'#283b31')):
                tile=Image.new('RGBA',crop.size,color);tile.alpha_composite(crop);board.paste(tile.convert('RGB'),(index*140,row*140+20))
                draw.line((index*140,row*140+122,(index+1)*140-1,row*140+122),fill='#718b71')
            draw.text((index*140+4,283),f'source f{index}',fill='white')
            tile=Image.new('RGBA',(170,150),'#c6c7b5');tile.alpha_composite(native.crop((130,160,300,310)));gif.append(tile.convert('RGB'))
    board.save(folder/f'paint-action-g{group:02}-native-light-dark-review-v{version}.png')
    gif[0].save(folder/f'paint-action-g{group:02}-native-motion-review-v{version}.gif',save_all=True,append_images=gif[1:],duration=150,loop=0,disposal=2)


for unit,groups in CAMERAS.items():
    folder=PROJECT/'assets/source/creatures'/unit/'ranger-rig-v4'
    for group,(reference,top,ground,root) in groups.items():
        repacked=(unit,group) in REPACKED
        generation=folder/f'paint-action-g{group:02}-atlas-v{2 if repacked else 1}-generation.json'
        source=json.loads(generation.read_text());factor=1 if repacked else source['returned_cell'][0]/512
        camera=calibrate_generation(PROJECT,generation,reference_index=reference,head_top_y=top*factor,
            ground_y=ground*factor,root_x=root*factor,target_height=78 if unit=='demacianRanger' else 80,
            basis=f'Actual reviewed upright/ready pose{reference}: hood/open-helmet plume topY{top}, front support soleY{ground}, pelvis projectionX{root}, measured on{576 if repacked else 512}px review coordinates. One whole-atlas camera only; body dimensions never fitted per frame. Repacked sheets retain exact original pose pixels with a common32px shift and fractional-grid phase, absorbed by this camera.')
        camera_path=folder/f'paint-action-g{group:02}-camera-v1.json'
        initial=export_generation(PROJECT,generation,camera_path)
        placements=[]
        for frame in initial['frames']:
            # The contact point is explicitly the lowest visible supporting sole
            # (or grounded knee/body in the actual collapse/prone pose), observed
            # in the complete source. This moves the full frame without resizing.
            dy=267-frame['alpha8_bbox'][3]
            placements.append({'index':frame['index'],'native_translation':[0,dy],'reviewed':True,
                'basis':f'Observed actual supporting sole/knee/prone-body lower contact is nativeY{frame["alpha8_bbox"][3]} before correction. Translate the complete pose by{dy}px to the shared ground contact267. Fixed atlas scale and all actual limb/equipment geometry remain unchanged; no raw-to-painted pixel/geometry equivalence claimed.',
                'evidence':[proof(PROJECT,generation),proof(PROJECT,PROJECT/frame['output'])]})
        result=export_generation(PROJECT,generation,camera_path,version=2,placements=placements,placement_version=1)
        reviews(folder,group,result)
        print(unit,group,'source exports',len(result['frames']),'scale',round(camera['scale'],5),'whole-frameY',[item['native_translation'][1] for item in placements])

# Normalize only distant near-transparent gutter speckles on the SAME native
# canvas, after measured placement. This never paints/cuts body alpha>=8.
for unit in CAMERAS:
    folder=PROJECT/'assets/source/creatures'/unit/'ranger-rig-v4';padding=[];export_records=[]
    for group in (0,1,2,3,4,5,7,8,11,12,13,14,15,16):
        record_path=folder/f'paint-action-g{group:02}-native-export-v2-placement-v1.json'
        result=json.loads(record_path.read_text());export_records.append(proof(PROJECT,record_path));frames=[]
        for frame in result['frames']:
            target=folder/f'native-actions-final-v1/g{group:02}/g{group:02}-f{frame["index"]:03}.png'
            converted=crop_padding(PROJECT/frame['output'],target,PROJECT);padding.append(converted)
            frames.append({'index':frame['index'],'output':converted['output'],'sha256':converted['sha256']})
        reviews(folder,group,{**result,'frames':frames},version=4)
    write(folder/'painted-native-padding-v1.json',{'unit':unit,'source_export_records':export_records,
        'conversions':padding,'status':'actual same-canvas padding conversions; native/art approval absent',
        'visual_approval_granted':False,'active_assets_modified':False})
print('All28painted action groups exported as source-only candidates; active assets unchanged.')
