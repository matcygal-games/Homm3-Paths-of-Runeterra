"""One coherent empty painting plus one genuinely painted Fleet support repair."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps,ImageChops
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent
FLEET=[(522,119),(597,119),(603,131),(605,146),(600,163),(584,174),
       (561,174),(543,171),(525,169),(515,154),(517,136)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    crop=ImageOps.fit(Image.open(HERE/'fleet-empty-crop-master-v4.png').convert('RGB'),(120,80),method=Image.Resampling.LANCZOS)
    crop.save(HERE/'fleet-empty-crop-native-v4.png')
    old=Image.open(HERE/'empty-terrain-native-raw-v2.png').convert('RGB')
    canvas=old.copy();canvas.paste(crop,(500,110))
    mask=Image.new('L',old.size);ImageDraw.Draw(mask).polygon(FLEET,fill=255)
    mask.save(HERE/'fleet-empty-repair-mask-v4.png')
    selected=Image.composite(canvas,old,mask)
    selected.save(HERE/'empty-terrain-selected-v4.png')
    assert not ImageChops.multiply(ImageChops.difference(old,selected).convert('L'),ImageChops.invert(mask)).getbbox()
    record={'status':'authored configuration','empty_background':'assets/source/town/complete-town-20261028-v1/empty-terrain-selected-v4.png',
       'empty_background_sha256':sha(HERE/'empty-terrain-selected-v4.png'),
       'whole_empty_master':'assets/source/town/complete-town-20261028-v1/empty-terrain-master-v2.png',
       'whole_empty_master_sha256':sha(HERE/'empty-terrain-master-v2.png'),
       'whole_empty_native_sha256':sha(HERE/'empty-terrain-native-raw-v2.png'),
       'repair_master':'assets/source/town/complete-town-20261028-v1/fleet-empty-crop-master-v4.png','repair_master_sha256':sha(HERE/'fleet-empty-crop-master-v4.png'),
       'repair_prompt':'assets/source/town/complete-town-20261028-v1/fleet-empty-crop-prompt-v4.txt','repair_prompt_sha256':sha(HERE/'fleet-empty-crop-prompt-v4.txt'),
       'repair_mask':'assets/source/town/complete-town-20261028-v1/fleet-empty-repair-mask-v4.png','repair_mask_sha256':sha(HERE/'fleet-empty-repair-mask-v4.png'),
       'repair_context_origin':[500,110],'repair_context_size':[120,80],'repair_polygon':FLEET,
       'outside_repair_mask_changed_pixels':0,'method':'Genuine whole-scene empty terrain inpainting, genuine removal of optional coast/Grail, then one source-context Fleet Hall supported landing repair. One fixed uniform conversion per source, technical protected compositing only.',
       'native_verified':False,'release_accepted':False}
    (HERE/'empty-terrain-selection-v4.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
