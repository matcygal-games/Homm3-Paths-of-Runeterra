"""Check actually rendered family prototype before related full cohorts."""
from pathlib import Path
from PIL import Image
import argparse
import hashlib
import json

parser=argparse.ArgumentParser()
parser.add_argument('--unit',required=True)
parser.add_argument('--revision',required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[4]
folder=root/'assets/source/creatures/animals'/args.unit/args.revision
receipt=json.loads((folder/'pilot-render-receipt.json').read_text())
audit=json.loads((folder/(args.unit+'-portable-reopened-audit.json')).read_text())
for key in ('integrity_matches',):assert audit[key]
for key in ('transition_endpoint_geometry_check','turn_consumer_endpoint_check','resting_wing_ground_clearance','opposing_facing_geometry_check'):
    assert audit[key]['passed'],key
maps=[]
for item in receipt['frames']:
    if item.get('context')!='map' or item['facing']!='right':continue
    path=root/item['source']
    right=Image.open(path).convert('RGBA')
    left=Image.open(path.parent.parent/'left'/path.name).convert('RGBA')
    assert right.tobytes()!=left.tobytes()
    bounds=[]
    for image in (right,left):
        bound=image.getchannel('A').point(lambda a:255 if a>=200 else 0).getbbox()
        assert 0<bound[0]<bound[2]<64 and 0<bound[1]<bound[3]<64,(path,bound)
        bounds.append(bound)
    maps.append({'group':item['group'],'frame':item['frame'],'body_bounds_right_left':bounds,
                 'opposing_rgba_differs':True,'projected_root':item['projected_ground_root']})
result={'status':'authored configuration','passed':True,'unit':args.unit,'revision':args.revision,
        'visual_approval_granted':False,'receipt_sha256':hashlib.sha256((folder/'pilot-render-receipt.json').read_bytes()).hexdigest(),
        'audit':audit,'maps':maps,'limits':'Actual saved-scene/PNG checks. Native playback, final visual quality, map legibility and rights remain pending.'}
Path(__file__).with_name(args.unit+'-'+args.revision+'-prototype-checks.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(args.unit+' prototype checks passed')
