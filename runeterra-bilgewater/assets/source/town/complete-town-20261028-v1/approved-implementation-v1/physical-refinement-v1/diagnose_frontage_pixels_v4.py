from pathlib import Path
import importlib.util
import json
from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('binder', HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
annotation = json.loads((HERE / 'semantic-candidate-v4/annotations.json').read_text())
index = json.loads((HERE / 'lower-roost-registration-v1/states.json').read_text())
out = {}
for key in ('castle','citadel','dwellingLvl3','dwellingUpLvl1','dwellingUpLvl3','dwellingUpLvl4','fort','ship','shipyard','special1'):
    frame = Image.open(binder.PROJECT / index['states'][key]['frame']).convert('RGBA')
    alpha = frame.getchannel('A')
    body = alpha.point(lambda p: 255 if p >= 128 else 0)
    full = alpha.point(lambda p: 255 if p >= 8 else 0)
    row = annotation['states'][key]
    door = binder.trace(row['door'])
    approach = binder.trace(row['approach'])
    cross = ImageChops.multiply(approach, ImageChops.subtract(body, door))
    bbox = approach.getbbox()
    out[key] = {'bbox': full.getbbox(), 'crossing': [
        [x,y] for y in range(bbox[1],bbox[3]) for x in range(bbox[0],bbox[2]) if cross.getpixel((x,y))]}
print(json.dumps(out, indent=2))
