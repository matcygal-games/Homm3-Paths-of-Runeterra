"""Technical source-RGB mattes for two roost and two coastal states.

No painting, recolouring or frame-owner writes. Every retained or recovered
pixel is read from the held state's declared genuinely painted source and its
recorded whole-image registration. Output alpha proposals require review.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
TOWN = HERE.parents[1]
REPORT = PROJECT / 'build/reports/complete-town-20261028-v1/physical-contract-v1/technical-mattes-four-v1/proposals-v1'
INDEX_PIN = 'c5eb6af7e638b86a879b51fda03236f0c86eb7f6763724bd4ec6b329139ac0e3'

# These explicit polygons trace architectural/cloth/bird components; thin
# structural members are separately traced so their surrounding sky remains
# transparent. They are image-space annotations, never newly painted pixels.
PARTS = {
    'dwellingUpLvl5': {
        'polygons': [
            [[637,45],[642,46],[646,48],[652,49],[658,49],[664,50],[670,51],[675,53],[681,55],[688,56],[689,58],[682,59],[681,73],[676,77],[665,78],[651,75],[643,73],[640,68],[639,57]],
            [[591,80],[594,80],[598,82],[604,84],[610,83],[610,94],[608,98],[604,96],[601,95],[600,97],[597,95],[595,97],[593,95],[591,92]],
            [[609,80],[614,82],[619,83],[625,84],[631,83],[636,83],[641,87],[645,92],[639,95],[628,95],[618,94],[611,91]],
            [[608,91],[618,94],[628,96],[638,94],[643,96],[643,115],[634,115],[626,113],[618,113],[612,111],[608,108]],
            [[638,93],[646,94],[657,94],[663,92],[667,94],[671,95],[671,98],[667,99],[656,99],[646,98],[640,99],[636,97]],
            [[643,98],[665,100],[666,114],[670,115],[669,119],[644,118]],
            [[668,98],[678,99],[685,97],[688,101],[687,119],[679,120],[668,116]],
            [[672,88],[680,85],[686,81],[690,80],[688,88],[686,97],[681,101],[674,103],[669,101],[669,94]],
            [[642,124],[647,126],[652,126],[657,127],[665,126],[673,125],[674,133],[670,139],[663,142],[651,141],[644,136]],
            [[641,39],[643,38],[644,40],[646,41],[646,43],[643,43]],
            [[649,41],[651,41],[653,43],[653,46],[650,46]],
            [[660,41],[662,41],[663,44],[665,45],[665,47],[661,46]],
            [[665,45],[667,45],[669,47],[671,48],[672,49],[668,49]],
            [[678,31],[681,32],[684,35],[684,38],[680,37],[677,36]],
            [[627,66],[630,65],[632,68],[632,70],[629,70]],
            [[633,68],[635,67],[637,70],[637,72],[634,71]],
            [[688,75],[691,74],[693,76],[694,78],[690,78]],
            [[607,75],[609,74],[611,77],[610,79],[607,78]],
            [[616,76],[619,75],[621,77],[621,79],[618,79]]
        ],
        'lines': [
            {'points': [[591,59],[592,111]], 'width': 1},
            {'points': [[592,63],[593,110]], 'width': 1},
            {'points': [[606,63],[608,113]], 'width': 2},
            {'points': [[631,68],[633,116]], 'width': 2},
            {'points': [[640,46],[643,139]], 'width': 2},
            {'points': [[656,30],[657,51]], 'width': 2},
            {'points': [[677,29],[678,119]], 'width': 2},
            {'points': [[649,78],[650,140]], 'width': 2},
            {'points': [[660,78],[660,139]], 'width': 2},
            {'points': [[670,79],[669,139]], 'width': 2},
            {'points': [[689,78],[689,128]], 'width': 1},
            {'points': [[597,77],[645,81]], 'width': 2},
            {'points': [[632,73],[687,81]], 'width': 2},
            {'points': [[606,99],[689,103]], 'width': 2},
            {'points': [[641,119],[685,122]], 'width': 2},
            {'points': [[644,79],[660,95]], 'width': 2},
            {'points': [[660,79],[646,95]], 'width': 1},
            {'points': [[663,80],[675,96]], 'width': 2},
            {'points': [[675,80],[666,96]], 'width': 1},
            {'points': [[646,119],[662,138]], 'width': 1},
            {'points': [[668,119],[651,139]], 'width': 1},
            {'points': [[592,62],[604,81]], 'width': 1},
            {'points': [[607,66],[631,82]], 'width': 1},
            {'points': [[678,34],[687,78]], 'width': 1},
            {'points': [[690,78],[698,121]], 'width': 1}
        ]
    },
    'dwellingLvl5': {
        'polygons': [
            [[630,49],[635,50],[641,51],[646,53],[651,56],[655,60],[658,64],[659,67],[657,67],[654,64],[650,61],[645,59],[640,57],[636,55],[632,52]],
            [[659,65],[661,65],[663,67],[665,68],[664,73],[658,74],[657,71]],
            [[664,66],[666,62],[670,61],[676,62],[682,64],[687,66],[691,69],[694,71],[690,72],[685,70],[679,69],[672,69],[667,70],[664,73]],
            [[649,71],[655,72],[660,72],[664,75],[661,80],[653,81],[649,78]],
            [[625,88],[632,86],[638,84],[644,83],[650,84],[654,84],[662,87],[669,89],[675,92],[685,95],[693,97],[697,99],[696,102],[685,101],[673,99],[664,96],[655,94],[646,92],[636,92],[628,93],[620,94]],
            [[621,94],[639,94],[654,96],[670,98],[689,102],[691,118],[687,129],[669,132],[650,132],[629,128],[620,123]],
            [[615,92],[623,90],[627,95],[628,125],[619,126],[612,121],[612,101]],
            [[700,91],[705,90],[710,88],[709,100],[708,109],[705,114],[702,115],[701,112],[699,113],[698,109],[698,100]],
            [[626,125],[640,129],[655,130],[668,129],[685,127],[688,132],[676,137],[659,138],[645,135],[633,132],[626,130]]
        ],
        'lines': [
            {'points': [[619,88],[620,128]], 'width': 2},
            {'points': [[630,87],[632,130]], 'width': 2},
            {'points': [[641,73],[642,131]], 'width': 2},
            {'points': [[650,72],[650,132]], 'width': 2},
            {'points': [[661,77],[660,134]], 'width': 2},
            {'points': [[676,96],[676,131]], 'width': 2},
            {'points': [[690,102],[690,130]], 'width': 1},
            {'points': [[699,90],[698,134]], 'width': 2},
            {'points': [[619,90],[699,99]], 'width': 2},
            {'points': [[619,123],[690,129]], 'width': 2},
            {'points': [[620,90],[649,80]], 'width': 1},
            {'points': [[650,80],[707,89]], 'width': 1},
            {'points': [[709,89],[706,123]], 'width': 1}
        ]
    },
    'shipyard': {
        'polygons': [
            [[634,300],[640,300],[646,302],[651,304],[656,304],[661,306],[676,306],[694,307],[714,307],[730,307],[741,305],[755,304],[769,305],[776,310],[777,313],[764,314],[748,314],[733,315],[718,315],[701,315],[684,315],[669,313],[654,311],[641,309],[634,307]],
            [[638,308],[641,310],[641,324],[639,327],[637,325],[636,314]],
            [[649,311],[652,311],[652,325],[651,327],[649,325]],
            [[664,313],[667,314],[667,327],[665,330],[663,327]],
            [[681,314],[684,314],[684,329],[682,332],[680,328]],
            [[700,314],[703,314],[703,328],[701,330],[699,326]],
            [[720,314],[723,314],[723,330],[721,332],[718,328]],
            [[739,314],[742,314],[742,328],[739,330],[737,327]],
            [[759,313],[763,312],[763,326],[760,329],[757,325]],
            [[772,312],[775,312],[775,322],[773,324],[771,320]]
        ],
        'lines': [
            {'points': [[640,313],[649,325]], 'width': 1},
            {'points': [[653,313],[665,327]], 'width': 1},
            {'points': [[668,315],[681,329]], 'width': 1},
            {'points': [[685,315],[700,327]], 'width': 1},
            {'points': [[704,315],[720,329]], 'width': 1},
            {'points': [[724,315],[739,328]], 'width': 1},
            {'points': [[744,314],[759,326]], 'width': 1},
            {'points': [[763,314],[773,323]], 'width': 1}
        ]
    },
    'ship': {
        'polygons': [
            [[667,291],[676,283],[686,272],[697,260],[708,250],[712,247],[712,253],[702,265],[692,276],[680,288],[672,294]],
            [[672,287],[682,281],[693,277],[704,266],[704,286],[700,293],[694,297],[685,297],[677,294],[672,293]],
            [[632,304],[637,303],[644,306],[652,308],[661,308],[669,313],[678,315],[691,319],[708,323],[719,323],[719,330],[704,334],[687,334],[670,331],[654,329],[638,323],[632,316]],
            [[621,325],[629,321],[641,319],[654,322],[673,325],[691,328],[708,328],[719,327],[725,319],[727,319],[726,331],[722,334],[721,351],[716,355],[703,359],[688,360],[672,359],[656,356],[641,349],[630,342],[624,335]],
            [[634,301],[640,301],[646,303],[654,306],[665,307],[683,308],[702,308],[721,308],[740,307],[758,305],[770,305],[776,309],[778,313],[765,314],[747,314],[731,315],[713,315],[698,315],[683,314],[665,313],[650,310],[638,309],[634,307]],
            [[729,314],[732,314],[732,330],[730,333],[727,329]],
            [[745,314],[748,313],[748,327],[746,330],[743,327]],
            [[760,313],[763,312],[764,325],[761,329],[758,326]],
            [[773,312],[776,312],[776,321],[774,324],[772,320]]
        ],
        'lines': [
            {'points': [[664,299],[710,248]], 'width': 2},
            {'points': [[668,291],[669,347]], 'width': 2},
            {'points': [[680,286],[678,339]], 'width': 1},
            {'points': [[705,265],[702,322]], 'width': 1},
            {'points': [[637,302],[667,316]], 'width': 1},
            {'points': [[640,306],[664,330]], 'width': 1},
            {'points': [[672,290],[646,317]], 'width': 1},
            {'points': [[678,288],[715,325]], 'width': 1},
            {'points': [[704,273],[724,325]], 'width': 1},
            {'points': [[733,315],[746,328]], 'width': 1},
            {'points': [[749,315],[761,327]], 'width': 1},
            {'points': [[764,314],[774,322]], 'width': 1}
        ]
    }
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    index = TOWN / 'derived-v1/states.json'
    if sha(index) != INDEX_PIN:
        raise ValueError('Held source index changed')
    data = json.loads(index.read_text())
    REPORT.mkdir(parents=True, exist_ok=True)
    rows = {}
    for state, definition in PARTS.items():
        record = data['states'][state]
        path = PROJECT / record['frame']
        if sha(path) != record['frame_sha256']:
            raise ValueError('Held frame changed: ' + state)
        source_path = TOWN / record['source']
        if sha(source_path) != record['source_sha256']:
            raise ValueError('Genuine painted source changed: ' + state)
        original = Image.open(path).convert('RGBA')
        raw = Image.open(source_path).convert('RGBA')
        registered = Image.new('RGBA', raw.size)
        registered.paste(raw, tuple(record.get('delta', [0, 0])))
        mask = Image.new('L', raw.size)
        draw = ImageDraw.Draw(mask)
        for polygon in definition['polygons']:
            draw.polygon([tuple(point) for point in polygon], fill=255)
        for line in definition['lines']:
            draw.line([tuple(point) for point in line['points']], fill=255, width=line['width'])
        mask = ImageChops.multiply(mask, registered.getchannel('A'))
        destination = HERE / state
        destination.mkdir(exist_ok=True)
        mask.save(destination / 'proposed-alpha.png')
        # RGB presentation evidence only; no new RGBA frame is written.
        proposed = registered.copy()
        proposed.putalpha(mask)
        bounds = mask.getbbox()
        box = [max(0, bounds[0]-4), max(0, bounds[1]-4), min(800, bounds[2]+4), min(374, bounds[3]+4)]
        plain = Image.new('RGBA', proposed.size, (35,39,43,255))
        plain.alpha_composite(proposed)
        plain.crop(tuple(box)).convert('RGB').resize(((box[2]-box[0])*4,(box[3]-box[1])*4), Image.Resampling.NEAREST).save(REPORT / (state+'-plain-4x.png'))
        checker = Image.new('RGBA', proposed.size)
        cd = ImageDraw.Draw(checker)
        for y in range(0,374,8):
            for x in range(0,800,8):
                value = 184 if (x//8+y//8)%2 else 222
                cd.rectangle((x,y,x+7,y+7), fill=(value,value,value,255))
        checker.alpha_composite(proposed)
        checker.crop(tuple(box)).convert('RGB').resize(((box[2]-box[0])*4,(box[3]-box[1])*4), Image.Resampling.NEAREST).save(REPORT / (state+'-checker-4x.png'))
        old_alpha = original.getchannel('A')
        recovered = ImageChops.subtract(mask, old_alpha)
        removed = ImageChops.subtract(old_alpha, mask)
        difference = ImageChops.difference(original.convert('RGB'), registered.convert('RGB')).convert('L')
        overlap = ImageChops.multiply(old_alpha, mask)
        if ImageChops.multiply(difference, overlap).getbbox():
            raise ValueError('Existing visible genuine RGB was altered')
        rows[state] = {'held_frame': record['frame'], 'held_frame_sha256': sha(path),
                       'genuine_source': source_path.relative_to(PROJECT).as_posix(), 'genuine_source_sha256': sha(source_path),
                       'whole_registration_delta': record.get('delta',[0,0]),
                       'alpha_mask': (destination/'proposed-alpha.png').relative_to(PROJECT).as_posix(),
                       'alpha_mask_sha256': sha(destination/'proposed-alpha.png'),
                       'bounds': list(bounds), 'retained_pixels': mask.histogram()[255],
                       'removed_background_pixels': removed.point(lambda x:255 if x else 0).histogram()[255],
                       'recovered_genuine_pixels_outside_old_clipped_alpha': recovered.point(lambda x:255 if x else 0).histogram()[255],
                       'retained_visible_rgb_changed_pixels': 0,
                       'apply_to_declared_painted_source_not_old_clipped_frame': True,
                       'source_owner_frames_modified': False, 'status': 'design proposal'}
    receipt = {'status':'design proposal', 'index_sha256':INDEX_PIN,
               'method':'Explicit technical component/rigging matte; source RGB and whole registration are unchanged. No painting or recolouring.',
               'states':rows, 'native_executed':False, 'release_accepted':False}
    (HERE/'proposal-index.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (REPORT/'proposal-index.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({state:{key:row[key] for key in ('bounds','retained_pixels','removed_background_pixels','recovered_genuine_pixels_outside_old_clipped_alpha')} for state,row in rows.items()},indent=2))


if __name__ == '__main__':
    main()
