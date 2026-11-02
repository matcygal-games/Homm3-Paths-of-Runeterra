"""Explicit native visible gate/stair/frontage spans, rather than point guards.

Polygons protect actual entrance architecture through its stair-foot/apron.
They remain review candidates bound to each genuine selected source frame.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OUT=HERE/'entry-spans-v2';REPORT=ROOT/'build/reports/complete-town-20261027-v2/entry-spans-v2'
POLYGONS={
 'villageHall':[(146,134),(161,134),(166,140),(179,162),(157,162),(151,145)],
 'townHall':[(150,129),(165,129),(171,140),(186,162),(166,162),(157,147)],
 'cityHall':[(144,122),(160,122),(168,133),(169,145),(183,162),(153,162),(148,145)],
 'capitol':[(151,103),(168,103),(174,112),(175,132),(199,161),(157,162),(154,139)],
 'fort':[(415,78),(438,78),(447,109),(447,120),(460,148),(420,148),(421,122),(413,110)],
 'citadel':[(415,75),(436,75),(445,110),(445,121),(454,148),(417,148),(420,121),(412,110)],
 'castle':[(441,73),(462,73),(470,96),(468,111),(477,148),(431,148),(436,123),(442,109)],
 'mageGuild1':[(315,127),(329,127),(334,136),(333,145),(343,158),(321,158)],
 'mageGuild2':[(324,121),(336,121),(342,131),(340,142),(351,158),(327,158)],
 'mageGuild3':[(326,122),(339,122),(345,133),(344,144),(355,158),(329,158)],
 'mageGuild4':[(328,117),(341,117),(348,128),(347,141),(359,158),(332,158)],
 'dwellingLvl1':[(628,145),(642,145),(656,175),(632,175)],
 'dwellingUpLvl1':[(619,135),(635,135),(651,172),(626,172)],
 'dwellingLvl2':[(144,207),(156,207),(162,233),(142,233)],
 'dwellingUpLvl2':[(162,204),(177,204),(187,232),(157,232)],
 'dwellingLvl3':[(49,177),(62,177),(76,201),(58,201)],
 'dwellingUpLvl3':[(45,168),(61,168),(71,201),(50,201)],
 'dwellingLvl4':[(540,168),(553,168),(558,190),(550,194),(539,193),(540,184)],
 'dwellingUpLvl4':[(501,167),(514,167),(519,188),(512,192),(502,190)],
 'dwellingLvl5':[(303,289),(318,289),(324,300),(323,312),(332,329),(309,329)],
 'dwellingUpLvl5':[(302,278),(318,278),(324,291),(322,307),(334,329),(306,329),(306,307)],
 'dwellingLvl6':[(512,315),(528,315),(533,327),(532,339),(534,348),(508,348),(513,336)],
 'dwellingUpLvl6':[(490,327),(506,327),(512,347),(485,347)],
 'special4':[(467,244),(487,244),(494,280),(462,280)],
 'dwellingLvl7':[(466,236),(482,236),(488,247),(486,263),(493,280),(461,280),(461,263),(463,247)],
 'dwellingUpLvl7':[(466,232),(482,232),(489,243),(488,260),(496,280),(460,280),(461,261),(463,243)],
 'tavern':[(161,307),(177,307),(181,319),(195,330),(208,345),(183,348),(175,337),(164,331)],
 'marketplace':[(591,235),(606,235),(614,249),(587,249)],
 'blacksmith':[(651,302),(690,302),(701,314),(703,337),(711,352),(664,355),(654,338),(649,317)],
 'resourceSilo':[(677,225),(690,225),(697,256),(680,258),(676,246)],
 'special1':[(51,98),(62,98),(76,129),(62,129)],
 'special2':[(731,131),(744,131),(753,157),(726,157)],
 'special3':[(240,197),(254,197),(259,208),(259,221),(252,237),(228,231),(238,221)],
 'shipyard':[(748,169),(756,169),(759,178),(748,179)],
 'ship':[(748,169),(756,169),(759,178),(748,179)],
 'grail':[(224,140),(232,140),(233,145),(222,145)],
}
ANCHORS={'villageHall':[164,162],'townHall':[175,162],'cityHall':[168,162],'capitol':[174,161],'fort':[440,148],'citadel':[432,148],'castle':[451,148],'mageGuild1':[328,158],'mageGuild2':[335,158],'mageGuild3':[338,158],'mageGuild4':[341,158],'dwellingLvl1':[645,173],'dwellingUpLvl1':[637,171],'dwellingLvl2':[151,231],'dwellingUpLvl2':[172,231],'dwellingLvl3':[66,200],'dwellingUpLvl3':[60,199],'dwellingLvl4':[548,192],'dwellingUpLvl4':[509,190],'dwellingLvl5':[321,328],'dwellingUpLvl5':[319,328],'dwellingLvl6':[523,347],'dwellingUpLvl6':[498,347],'special4':[479,278],'dwellingLvl7':[475,279],'dwellingUpLvl7':[475,279],'tavern':[191,346],'marketplace':[601,245],'blacksmith':[682,353],'resourceSilo':[686,256],'special1':[68,128],'special2':[737,156],'special3':[245,235],'shipyard':[750,174],'ship':[750,174],'grail':[228,144]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def main():
 s=load(HERE/'candidate-final-v5/selection.json');rows=[]
 if set(POLYGONS)!={r['state']for r in s['states']}:raise ValueError('Entry span state coverage differs')
 for r in s['states']:
  state=r['state'];source=ROOT/r['native_layer'];im=Image.open(source).convert('RGBA');bb=im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox();m=Image.new('L',(800,374));ImageDraw.Draw(m).polygon(POLYGONS[state],fill=255);bounds=Image.new('L',(800,374));ImageDraw.Draw(bounds).rectangle((bb[0],bb[1],bb[2]-1,bb[3]-1),fill=255);m=ImageChops.multiply(m,bounds);anchor=ANCHORS[state]
  if not m.getpixel(tuple(anchor)):raise ValueError('Actual anchor outside selected entry span '+state+str(anchor))
  
  if state in ('shipyard','ship'):m=ImageChops.multiply(m,im.getchannel('A').point(lambda a:255 if a>=8 else 0))
  p=OUT/(state+'.png');save(p,m);save(REPORT/(state+'-entire-source-4x.png'),im.crop(bb).resize(((bb[2]-bb[0])*4,(bb[3]-bb[1])*4),Image.Resampling.NEAREST));view=im.copy();color=Image.new('RGBA',(800,374),(25,210,255,0));color.putalpha(m.point(lambda a:110 if a else 0));view.alpha_composite(color);ImageDraw.Draw(view).ellipse((anchor[0]-1,anchor[1]-1,anchor[0]+1,anchor[1]+1),fill=(255,255,255,255));save(REPORT/(state+'-entire-source-and-entry-4x.png'),view.crop(bb).resize(((bb[2]-bb[0])*4,(bb[3]-bb[1])*4),Image.Resampling.NEAREST));crop=(max(bb[0],min(p[0]for p in POLYGONS[state])-4),max(bb[1],min(p[1]for p in POLYGONS[state])-4),min(bb[2],max(p[0]for p in POLYGONS[state])+5),min(bb[3],max(p[1]for p in POLYGONS[state])+5));save(REPORT/(state+'-full-entry-6x.png'),view.crop(crop).resize(((crop[2]-crop[0])*6,(crop[3]-crop[1])*6),Image.Resampling.NEAREST));rows.append({'state':state,'source':r['native_layer'],'source_sha256':sha(source),'actual_native_gate_stair_frontage_polygon':POLYGONS[state],'entrance':anchor,'mask':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)},'mask_pixels':m.histogram()[255],'status':'authored configuration','review':'Complete visible entry span proposal, not a tiny point exemption; source-pixel review required.'})
 write(OUT/'entries.json',{'status':'authored configuration','script_sha256':sha(Path(__file__)),'states':rows});print(json.dumps({'entry_spans':len(rows),'index_sha256':sha(OUT/'entries.json')}))
if __name__=='__main__':main()
