"""Native Castle reference composition from read-only extracted original pixels."""
import json,re,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/painted-town-community-20261024-v1'
REF=ROOT.parent/'runeterra-demacia/references'
CONFIG=ROOT.parent/'vcmi-develop/vcmi-develop/config/factions/castle.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    # VCMI JSON contains comments, so parse the simple one-line structure records only.
    records=[]
    pattern=r'"(\w+)"\s*:\s*\{\s*"animation"\s*:\s*"([^"]+)"\s*,\s*"x"\s*:\s*(-?\d+)\s*,\s*"y"\s*:\s*(-?\d+)(?:\s*,\s*"z"\s*:\s*(-?\d+))?'
    wanted=['extraAnimation','castle','capitol','mageGuild4','special3','marketplace','resourceSilo','blacksmith','special1','special2','horde1Upgr','shipyard','ship','grail']+['dwellingUpLvl'+str(t) for t in range(1,8)]
    for name,animation,x,y,z in re.findall(pattern,CONFIG.read_text()):
        if name in wanted:records.append({'name':name,'animation':animation,'x':int(x),'y':int(y),'z':int(z or 0)})
    canvas=Image.open(REF/'images/tbcsback.pcx.png').convert('RGBA');missing=[]
    for row in sorted(records,key=lambda r:r['z']):
        source=REF/'frames'/Path(row['animation']).stem.lower()/'g00-f000.png'
        if not source.is_file():missing.append(str(source));continue
        canvas.alpha_composite(Image.open(source).convert('RGBA'),(row['x'],row['y']))
        row.update({'source':str(source),'sha256':sha(source)})
    canvas.save(REPORT/'original-castle-assembled-native.png')
    comparison=Image.new('RGBA',(800,782),(35,32,27,255));comparison.alpha_composite(canvas,(0,14))
    comparison.alpha_composite(Image.open(REPORT/'grail-native.png').convert('RGBA'),(0,408))
    d=ImageDraw.Draw(comparison);d.text((2,0),'Original Castle native pixels / source-config placement; static reference, not a screenshot',fill='white')
    d.text((2,394),'Bandle candidate native800x374; independent painted2D layers; no visual acceptance granted',fill='white')
    comparison.save(REPORT/'original-castle-fulltown-native-comparison.png')
    receipt={'ok':not missing,'purpose':'Read-only original native pixel/material/scale context, not licensed deliverable or screenshot',
        'background':str(REF/'images/tbcsback.pcx.png'),'background_sha256':sha(REF/'images/tbcsback.pcx.png'),
        'config':str(CONFIG),'config_sha256':sha(CONFIG),'records':records,'missing':missing,
        'initial_attempt':'Strict json.loads on commented original config failed at line158; no files changed. Replaced by bounded one-line structure parser.',
        'output_sha256':sha(REPORT/'original-castle-fulltown-native-comparison.png'),'visual_approval_granted':False}
    (REPORT/'original-reference-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'ok':not missing,'records':len(records),'missing':missing}))
if __name__=='__main__':main()
