"""Protect V1 scenery/buildings outside the genuinely painted Fleet Hall edit."""
from pathlib import Path
from PIL import Image, ImageDraw,ImageChops
import hashlib,json
HERE=Path(__file__).resolve().parent
POLY=[(547,49),(553,49),(554,55),(566,57),(581,66),(583,73),(575,77),
      (566,75),(566,84),(574,87),(586,94),(596,104),(600,116),(599,132),
      (596,145),(583,151),(571,153),(558,155),(555,161),(545,166),(526,165),
      (526,156),(533,150),(534,145),(525,143),(520,134),(520,121),(519,113),
      (523,109),(523,100),(531,96),(535,94),(536,85),(539,80),(544,79)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=Image.open(HERE/'complete-town-native-v1.png').convert('RGB')
    raw=Image.open(HERE/'complete-town-native-raw-v2.png').convert('RGB')
    mask=Image.new('L',old.size);ImageDraw.Draw(mask).polygon(POLY,fill=255)
    mask.save(HERE/'fleet-hall-edit-mask-v2.png')
    selected=Image.composite(raw,old,mask);selected.save(HERE/'complete-town-native-v2.png')
    diff=ImageChops.difference(selected,old)
    changed=diff.convert('L').point(lambda x:255 if x else 0)
    outside=ImageChops.subtract(changed,mask)
    assert outside.getbbox() is None
    record={'status':'authored configuration','tool':'OpenAI built-in image_gen',
       'prompt':'assets/source/town/complete-town-20261028-v1/whole-town-prompt-v2.txt',
       'prompt_sha256':sha(HERE/'whole-town-prompt-v2.txt'),
       'raw_master':'assets/source/town/complete-town-20261028-v1/complete-town-master-v2.png',
       'raw_master_sha256':sha(HERE/'complete-town-master-v2.png'),
       'raw_native':'assets/source/town/complete-town-20261028-v1/complete-town-native-raw-v2.png',
       'raw_native_sha256':sha(HERE/'complete-town-native-raw-v2.png'),
       'selected_native':'assets/source/town/complete-town-20261028-v1/complete-town-native-v2.png',
       'selected_native_sha256':sha(HERE/'complete-town-native-v2.png'),
       'protected_base_sha256':sha(HERE/'complete-town-native-v1.png'),
       'mask':'assets/source/town/complete-town-20261028-v1/fleet-hall-edit-mask-v2.png',
       'mask_sha256':sha(HERE/'fleet-hall-edit-mask-v2.png'),
       'mask_polygon':POLY,'outside_allowed_pixels_changed':0,
       'method':'One whole-scene genuine2D Fleet Hall addition, one global nativefit; technical protected compositing selects its actual bounded silhouette/support context and preserves every other V1 pixel.',
       'native_verified':False,'release_accepted':False}
    (HERE/'generation-v2.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
