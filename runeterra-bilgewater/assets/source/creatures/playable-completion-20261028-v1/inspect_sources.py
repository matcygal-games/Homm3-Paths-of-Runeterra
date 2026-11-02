"""Read-only pixel inventory for candidate masters and native controls."""
from pathlib import Path
import hashlib, json
from PIL import Image

ROOT = Path(__file__).resolve().parent
def inspect(path, cols=1, rows=1):
    im = Image.open(path).convert('RGBA')
    cells = []
    for row in range(rows):
        for col in range(cols):
            box = (im.width*col//cols, im.height*row//rows, im.width*(col+1)//cols, im.height*(row+1)//rows)
            crop = im.crop(box)
            alpha = crop.getchannel('A')
            bound = alpha.getbbox()
            edges = [bool(alpha.crop(edge).getbbox()) for edge in [(0,0,crop.width,1),(0,crop.height-1,crop.width,crop.height),(0,0,1,crop.height),(crop.width-1,0,crop.width,crop.height)]]
            cells.append({'row':row, 'column':col, 'crop':box, 'alpha_bounds':bound, 'edge_opaque':edges})
    return {'path':path.as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'dimensions':im.size,'alpha_extrema':im.getchannel('A').getextrema(),'cells':cells}

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('path',type=Path);p.add_argument('--cols',type=int,default=1);p.add_argument('--rows',type=int,default=1)
    a=p.parse_args();print(json.dumps(inspect(a.path,a.cols,a.rows),indent=2))
