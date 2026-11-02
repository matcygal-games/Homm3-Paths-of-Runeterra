"""Replay the two genuine painted support edits used as the terrace base."""
from pathlib import Path
import hashlib
import io
from PIL import Image

HERE=Path(__file__).resolve().parent


def main():
    background=Image.open(HERE/'background-master-v1-native.png').convert('RGBA')
    for name,size,origin in [('aerie',(180,124),(0,0)),('fort',(204,161),(596,10))]:
        raw=Image.open(HERE/'ancillary'/(name+'-support')/'master-v1-raw.png').convert('RGBA')
        source=raw.resize(size,Image.Resampling.LANCZOS)
        mask=Image.open(HERE/(name+'-support-selection-mask.png')).convert('L')
        background.paste(source,origin,mask)
    buffer=io.BytesIO();background.save(buffer,format='PNG')
    target=HERE/'background-selected-native-v3.png'
    if target.is_file() and target.read_bytes()!=buffer.getvalue():
        raise ValueError('Background replay differs from the preserved selected base')
    target.write_bytes(buffer.getvalue())
    print('Selected terrain base replay: '+hashlib.sha256(buffer.getvalue()).hexdigest())


if __name__=='__main__':main()
