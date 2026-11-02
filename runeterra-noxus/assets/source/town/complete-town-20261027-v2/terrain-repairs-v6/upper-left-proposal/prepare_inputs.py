"""Prepare technical review guides; no artwork is created by this script."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent
TOWN=HERE.parents[1]
ROOT=TOWN.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2/terrain-repairs-v6/upper-left-proposal'
STATES=['villageHall','townHall','cityHall','capitol','mageGuild1','mageGuild2','mageGuild3','mageGuild4','special1']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    bg=Image.open(TOWN/'terrain/final-native-v5.png').convert('RGBA')
    guide=bg.copy()
    union=Image.new('L',bg.size)
    for state in STATES:
        mask=Image.open(TOWN/f'physical-v10/{state}/foundation.png').convert('L')
        union=ImageChops.lighter(union,mask)
    guide.paste((255,0,210,255),(0,0),union)
    d=ImageDraw.Draw(guide)
    d.rectangle((0,104,397,177),outline=(0,255,255),width=1)
    d.text((5,105),'Repair region only; magenta = actual roots',fill=(255,255,255))
    guide.save(HERE/'terrain-root-guide.png')
    bg.crop((0,90,400,178)).save(HERE/'terrain-target-crop.png')
    Image.open(ROOT/'build/reports/complete-town-20261027-v2/final-v5/full-native.png').crop((0,90,400,178)).save(HERE/'full-context-crop.png')
    (HERE/'input-pins.json').write_text(json.dumps({'status':'design proposal','base':{'path':str((TOWN/'terrain/final-native-v5.png').relative_to(ROOT)).replace('\\','/'),'sha256':sha(TOWN/'terrain/final-native-v5.png')},'root_union_bbox':union.getbbox(),'states':STATES,'native_patch_limit':[0,104,398,178],'no_geometry_admission':True},indent=2)+'\n')
    print(json.dumps({'guide':str(HERE/'terrain-root-guide.png'),'root_union_bbox':union.getbbox()}))
if __name__=='__main__':main()
