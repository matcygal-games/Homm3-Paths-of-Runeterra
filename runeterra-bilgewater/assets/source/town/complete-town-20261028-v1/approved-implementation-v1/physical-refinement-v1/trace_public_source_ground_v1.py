"""Native permanent-ground observations after architecture/scenery separation.

This writer reads the approved public-ground source and earlier source studies,
not a building contact mask, negative control, desired support result or error.
Terrace tops, retaining faces, individual stair flights and water stay distinct.
The polygons are manually observed source boundaries, not plot rectangles.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
BASE=HERE.parent
OUT=HERE/'public-source-ground-v1'
OUT.mkdir(exist_ok=False)
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def poly(ps):
 out=Image.new('L',(800,374));ImageDraw.Draw(out).polygon(list(map(tuple,ps)),fill=255);return out
def union(ms):
 out=Image.new('L',(800,374))
 for m in ms:out=ImageChops.lighter(out,m)
 return out
prior=BASE/'physical-tools-v1/manual-inputs-v3/terrain-annotations.json'
plan=json.loads(prior.read_text())
ground=HERE/'ownership-separation-v3/background-public-source.png'
plan.update(status='design proposal',background=ref(ground),ancestry=ref(prior),
 scope='Actual permanent public paving, recovered selected horizontal beds, timber deck tops and separately traced stair flights. No structural contact or terrain-fitting inputs are loaded by this writer.')
replace={
 'archive-upper-landing':[[458,110],[478,110],[504,111],[522,114],[531,120],[532,126],[522,130],[507,132],[486,130],[470,127],[458,121]],
 'fleet-level-stone-pad':[[525,121],[548,119],[574,119],[594,121],[600,130],[600,138],[595,146],[585,151],[567,154],[545,154],[531,150],[526,143],[523,135],[522,128]],
 'genuine-recovered-sailors-lower-deck-top':[[65,249],[82,248],[118,248],[143,248],[150,251],[147,254],[138,256],[100,255],[71,254],[65,252]],
 'genuine-recovered-captains-stone-apron-top':[[529,141],[550,141],[589,140],[598,144],[597,148],[587,152],[568,154],[543,154],[531,151]],
 'genuine-recovered-buhru-lower-apron-top':[[599,212],[620,212],[643,214],[662,214],[685,211],[703,211],[710,215],[708,219],[698,222],[674,222],[648,221],[626,220],[605,220]],
 # Real upper end of the civic stair is wider than the old narrow brush.
 'actual-central-inter-flight-rest':[[393,176],[407,175],[413,181],[410,184],[394,184],[391,180]],
 'actual-west-mid-flight-turn-landing':[[144,244],[156,245],[172,247],[173,251],[169,255],[158,255],[145,252]],
}
for row in plan['support_regions']:
 if row['id'] in replace:row['polygon']=replace[row['id']]
plan['support_regions'] += [
 {'id':'permanent-keeps-garden-cap','polygon':[[103,80],[148,85],[189,89],[231,94],[276,102],[280,111],[233,109],[190,104],[147,99],[102,91]],'observation':'Existing genuine hidden garden source plus permanent approved rock-garden top; lower ivy face is excluded.'},
 {'id':'permanent-basin-poolside-top','polygon':[[94,173],[111,173],[127,174],[147,176],[164,176],[187,176],[200,178],[201,183],[193,186],[180,187],[164,185],[146,184],[126,185],[111,182],[95,179]],'observation':'Native poolside paved cap ends above the ivy retaining face; wet spray is not a road.'},
 {'id':'permanent-treasury-top','polygon':[[444,181],[460,183],[479,186],[499,186],[517,184],[521,188],[519,192],[502,195],[482,197],[464,193],[446,189]],'observation':'Native actual sloping-in-projection horizontal paved forecourt; the darker vertical face below is excluded.'},
 {'id':'main-stair-lower-landing','polygon':[[382,275],[400,273],[443,274],[460,276],[468,281],[465,286],[439,288],[410,287],[383,284]],'observation':'Actual pale paved foot landing visible immediately below broad main stair.'},
 {'id':'eastern-buhru-street-turn','polygon':[[704,188],[716,190],[727,194],[729,199],[720,206],[706,216],[699,218],[697,214],[709,202],[716,197],[706,195]],'observation':'Actual east public street turns around the terrace edge; only cap/treads, never the exposed coastal cliff.'},
]
# Actual painted treads reclaimed from the former broad construction alpha.
stairs_replace={
 'civic-first-descent':[[371,130],[390,132],[400,149],[382,153],[374,144]],
 'civic-middle-descent':[[382,154],[401,152],[410,171],[406,175],[394,176],[387,165]],
 'fleet-eastern-switchback':[[546,154],[562,154],[579,164],[597,173],[595,177],[589,177],[572,172],[550,162]],
 'actual-west-upper-public-flight':[[173,187],[185,189],[183,204],[174,219],[162,232],[147,232],[151,220],[162,207]],
 'east-middle-downturn':[[608,222],[620,222],[613,226],[592,237],[578,241],[577,237],[579,231],[591,224]],
 'east-lower-return-flight':[[576,242],[590,241],[612,261],[610,266],[606,270],[594,262],[579,252]],
}
for row in plan['stairs_regions']:
 if row['id'] in stairs_replace:row['polygon']=stairs_replace[row['id']]
plan['stairs_regions'] += [
 {'id':'actual-archive-west-small-entry-treads','polygon':[[467,128],[478,130],[479,133],[471,132],[467,131]],'observation':'Short real small source steps at the west court edge, not vertical face below.'},
 {'id':'actual-tavern-public-southwest-stair','polygon':[[530,264],[544,263],[559,266],[580,276],[595,281],[613,286],[624,290],[620,294],[608,290],[589,285],[572,280],[551,270],[533,269]],'observation':'Continuous permanent source masonry treads along the public diagonal retaining frontage; no enclosed tavern room is opened.'},
 {'id':'actual-front-quay-east-timber-descent','polygon':[[548,293],[554,293],[560,300],[569,307],[581,313],[580,317],[574,316],[564,310],[554,302],[549,299]],'observation':'Native brown timber diagonal descent into east public quay; selected source coordinates independently preserved for review.'},
]
support=union(poly(r['polygon']) for r in plan['support_regions'])
stairs_raw=union(poly(r['polygon']) for r in plan['stairs_regions'])
# Shared source junction pixels are cap landings; no double level is authored.
stairs=ImageChops.subtract(stairs_raw,support)
water=union(poly(r['polygon']) for r in plan['water_regions'])
dry_plan=json.loads((HERE/'terrain-planes-v1/terrain-plan.json').read_text())
land=ImageChops.subtract(poly(dry_plan['dry_ownership_polygon']),water)
land=union([land,support,stairs])
plan['dry_ownership_polygon']=dry_plan['dry_ownership_polygon']
plan['junction_interpretation']='Observed horizontal terrace cap takes ownership of shared boundary pixels; tread pixels start immediately below it. No contact masks are an input.'
plan['shared_cap_tread_boundary_pixels']=sum(bool(v) for v in ImageChops.multiply(support,stairs_raw).get_flattened_data())
plan['source_observation_atlas']=[ref(p) for p in sorted((HERE/'ownership-ground-atlas-v1').glob('*.png'))]
for role,im in [('support',support),('stairs',stairs),('water',water),('land',land)]:im.save(OUT/(role+'.png'))
plan['masks']={role:ref(OUT/(role+'.png')) for role in ('land','support','stairs','water')}
(OUT/'terrain-plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
overlay=Image.open(ground).convert('RGBA')
for im,c in [(support,(20,220,90)),(stairs,(240,160,20)),(water,(20,80,240))]:
 layer=Image.new('RGBA',(800,374),c+(0,));layer.putalpha(im.point(lambda v:75 if v else 0));overlay=Image.alpha_composite(overlay,layer)
overlay.save(OUT/'native-source-planes-overlay.png')
print(json.dumps({'support_regions':len(plan['support_regions']),'stairs_regions':len(plan['stairs_regions']),'junction_pixels':plan['shared_cap_tread_boundary_pixels'],'terrain_plan':ref(OUT/'terrain-plan.json')}))
