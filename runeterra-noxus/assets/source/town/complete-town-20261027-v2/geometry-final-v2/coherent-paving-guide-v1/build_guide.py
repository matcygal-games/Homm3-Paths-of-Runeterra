"""Freeze source-bound structural controls for a whole-scene2Dsurface repaint.
This produces engineering guides only. The reference materials are user-rejected.
"""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageChops,ImageDraw,ImageFilter
G=Path(__file__).resolve().parent;R=G.parents[5];T=G.parents[1]
SOURCE=T/'coherent-paving-repaint-v1/reference-empty-native.png';INDEX=T/'native-transforms-v14/states.json';BASE=G.parent/'final-v14-trace-v1';OUT=G/'structural-contract/terrain-trace'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def mask(polys):
 im=Image.new('L',(800,374));d=ImageDraw.Draw(im)
 for poly in polys:d.polygon(poly,fill=255)
 return im
def main():
 if(G/'guide-index.json').exists():raise ValueError('Preserve the frozen guide; use a new guide version')
 assert sha(SOURCE)=='a6734272452581492165564f67a59b8785f862e66ce421e918e2503bc15b6ed2'
 assert sha(INDEX)=='e5101798a4336583495f9fbcb04ad780e54cca81275677b94e191ac69f233023'
 rows=json.loads(INDEX.read_text())['states'];assert len(rows)==36
 trace=json.loads((BASE/'background-plane-trace-v6.json').read_text());floors=trace['level_floor_polygons'];stairs=trace['public_stair_polygons']
 links=[
 {'id':'academy_west','material':'stone','stairs':[[1,132],[7,132],[7,144],[1,144]],'landings':[[[0,130],[9,130],[9,131],[0,131]],[[0,145],[9,145],[9,150],[7,151],[5,152],[3,153],[3,154],[0,154]]],'endpoints':[[3,131],[3,154]],'relative_height':'Academy west landing above Civic court','field':[0,130,10,155]},
 {'id':'avenue_east','material':'stone','stairs':[[423,177],[430,170],[432,170],[438,173],[436,175],[431,180],[428,181],[424,179]],'landings':[],'endpoints':[[416,183],[440,174]],'relative_height':'Main avenue to raised Menagerie court, preserve native diagonal flight and side-face contour','field':[414,168,445,186]},
 {'id':'east_descent','material':'stone','stairs':[[665,166],[670,166],[673,179],[683,186],[691,197],[696,210],[690,210],[686,200],[679,193],[673,186],[668,180],[666,174]],'landings':[],'endpoints':[[666,166],[693,210]],'relative_height':'Barracks/Hall upper quay above lower Market court','field':[654,166,711,215]},
 {'id':'market_rift','material':'stone','stairs':[[561,232],[572,232],[575,233],[573,235],[562,235],[560,234]],'landings':[[[554,235],[562,235],[563,236],[554,236]],[[573,231],[579,231],[579,233],[575,233],[572,232]]],'endpoints':[[579,233],[559,235]],'relative_height':'Market upper side of the diagonal retaining wall to lower Rift frontage','field':[554,231,580,237]},
 {'id':'coast_gangway','material':'wood with existing support pilings','stairs':[[745,158],[748,158],[748,169],[745,169]],'landings':[[[745,170],[750,170],[750,172],[745,172]]],'endpoints':[[746,157],[748,172]],'actual_selected_deck_join':[749,172],'relative_height':'Dry upper quay to selected lower coast deck','field':[742,158,753,176]}
 ]
 support=Image.open(BASE/'support.png').convert('L');step=Image.open(BASE/'stairs.png').convert('L');walk=Image.open(BASE/'walkable-plane.png').convert('L');water=Image.open(BASE/'water.png').convert('L');added_floor=Image.new('L',(800,374));added_steps=added_floor.copy()
 for link in links:
  lm=mask(link['landings']);sm=mask([link['stairs']]);folder=G/'links'/link['id'];save(folder/'actual-step-footprint.png',sm);save(folder/'actual-landing-footprint.png',lm);link['step_mask']=ref(folder/'actual-step-footprint.png');link['landing_mask']=ref(folder/'actual-landing-footprint.png')
  if link['id']in('east_descent','market_rift','coast_gangway'):added_floor=ImageChops.lighter(added_floor,lm);added_steps=ImageChops.lighter(added_steps,sm);stairs[link['id']+'_actual_new_flight']=link['stairs']
  for i,poly in enumerate(link['landings']):floors[link['id']+'_actual_landing_'+str(i)]=poly
 coast=ImageChops.lighter(mask([links[-1]['stairs']]),mask(links[-1]['landings']));water=ImageChops.subtract(water,coast);land=ImageChops.invert(water);step=ImageChops.lighter(step,added_steps);support=ImageChops.subtract(ImageChops.lighter(support,added_floor),step);walk=ImageChops.multiply(ImageChops.lighter(walk,ImageChops.lighter(added_floor,added_steps)),land)
 for name,im in [('support',support),('stairs',step),('walkable-plane',walk),('water',water),('land',land)]:save(OUT/(name+'.png'),im)
 trace.update(source=ref(SOURCE),scope='AUTHORING STRUCTURE ONLY. Exact current rejected reference, independent background planes and all five real public links. No visual acceptance, final admission, negatives or stage.',level_floor_polygons=floors,public_stair_polygons=stairs,historical_background_trace=ref(BASE/'background-plane-trace-v6.json'),coast_constructed_horizontal_surface=ref(G/'links/coast_gangway/actual-landing-footprint.png'),coast_visible_water_change='Only actual opaque constructed wood step/landing footprint removed from visible external water; ordinary shoreline and all other water retained.',structural_source_index=ref(INDEX),producer=ref(Path(__file__)))
 write(OUT/'background-plane-trace-v6.json',trace)
 bg=Image.open(SOURCE).convert('RGBA');save(G/'reference/reference-empty-native.png',bg);shutil.copyfile(INDEX,G/'reference/states-index-v14.json');write(G/'five-required-links.json',{'status':'design proposal','reference':ref(SOURCE),'links':links,'retained_existing_public_stair_polygons':{k:v for k,v in stairs.items()if not any(k.startswith(link['id'])for link in links)},'heights':'Preserve native projected contours and listed relative order. Native structure z is draw order, never a fabricated physical elevation.'})
 unions={k:Image.new('L',(800,374))for k in('body','silhouette','foundation','complete-contact','full-entry','own-horizontal-treads')};state_records=[]
 for row in rows:
  s=row['state'];folder=G/'immutable-building-layers'/s;record={k:row[k]for k in('state','site','native_z','entrance','transform')};folder.mkdir(parents=True,exist_ok=True)
  mapping={'frame':'frame','body_mask':'body','silhouette_mask':'silhouette','foundation_mask':'foundation','door_mask':'full-entry','own_treads_mask':'own-horizontal-treads','semantic_zone_mask':'semantic-ground-zone'}
  for source_key,name in mapping.items():
   rr=row[source_key];p=R/rr['path'];assert sha(p)==rr['sha256'];q=folder/(name+'.png');shutil.copyfile(p,q);record[name]=ref(q)
   if name in unions:unions[name]=ImageChops.lighter(unions[name],Image.open(q).convert('L'))
  full_contact=row.get('complete_structural_and_entry_contact_mask',row['foundation_mask']);p=R/full_contact['path'];assert sha(p)==full_contact['sha256'];q=folder/'complete-contact.png';shutil.copyfile(p,q);record['complete-contact']=ref(q);unions['complete-contact']=ImageChops.lighter(unions['complete-contact'],Image.open(q).convert('L'))
  if 'entry_contact_role_mask'in row:
   p=R/row['entry_contact_role_mask']['path'];q=folder/'verified-entry-contact-role.png';shutil.copyfile(p,q);record['verified-entry-contact-role']=ref(q)
  state_records.append(record)
 for name,im in unions.items():save(G/'geometry-reference'/('all36-'+name+'.png'),im)
 write(G/'immutable-building-layers/index.json',{'status':'authored configuration','source_index':ref(INDEX),'states':state_records,'rules':['All36 raw selected RGBA layers, native positions, draw order, full source parts, contacts, arches and own treads are immutable.','Building silhouettes are REFERENCE ONLY, never an exclusion from repainting EMPTY-background paving underneath them.','Foundation masks classify actual source contact only; they never generate background floor/support or art.']})
 # The initial paint control includes the complete independently traced
 # horizontal/step surfaces, without subtracting any building footprint.
 # Retaining masonry and transition refinements are kept separate from the
 # immutable functional support/walking plan.
 save(G/'paint-controls/horizontal-and-step-surface-interiors.png',ImageChops.lighter(support,walk));save(G/'paint-controls/constructed-coast-horizontal-footprint.png',coast)
 faces={
 'rift_left_front_face':[[420,285],[440,285],[440,297],[420,297]],
 'rift_right_retaining_front':[[417,232],[439,237],[475,241],[515,243],[551,239],[563,238],[562,247],[539,251],[503,251],[466,247],[438,241],[417,236]],
 'silo_right_projected_front_face':[[746,261],[778,261],[778,264],[746,264]],
 'market_rift_upper_diagonal_face':[[538,218],[547,221],[559,225],[571,228],[573,230],[569,230],[557,227],[545,224],[538,221]]}
 write(G/'retaining-geometry.json',{'status':'design proposal','reference':ref(SOURCE),'locked_relative_levels':[['Bastion','Civic'],['Bastion','College'],['Bastion','Barracks'],['Bastion','Rose'],['Civic','Axe'],['Civic','Hound'],['Axe','Hound'],['Rose','Market'],['Silo','Foundry'],['Arena','Crimson']],'confirmed_native_contours':{'silo':'Horizontal top must contain all411 translated contact pixels; projected front edge approximatelyy260; vertical support below.','rift_left':'Horizontal court through282; cap283/284; vertical masonry below.','rift_right':'Horizontal brown top band through237/238; dark vertical front face240+; upper diagonal gray face is never floor.'},'face_witness_polygons':faces,'caution':'Witness polygons identify known vertical masonry, not a complete physical-height map. Preserve the actual reference contours; no numerical heights invented and no oldV3 geometry imported.'})
 write(G/'horizontal-plane-fields.json',{'status':'authored configuration','source':ref(SOURCE),'fields':floors,'masks':'Independent background-source polygons, not roots. Overlapping descriptive fields are not numerical physical heights.','current_functional_masks':{n:ref(OUT/(n+'.png'))for n in('support','stairs','walkable-plane','water','land')}})
 write(G/'guide-index.json',{'status':'design proposal','user_rejected_materials':True,'visual_approval':False,'final_admission_on_hold':True,'native_or_stage_operation':False,'reference':ref(SOURCE),'reference_merge_proof':ref(T/'coherent-paving-repaint-v1/REFERENCE-v1.json'),'source_state_index':ref(INDEX),'architecture':ref(G/'immutable-building-layers/index.json'),'five_links':ref(G/'five-required-links.json'),'planes':ref(G/'horizontal-plane-fields.json'),'retaining_geometry':ref(G/'retaining-geometry.json'),'paint_constraint':'Whole-scene2Dsurface repaint. Include paving below future building silhouettes, retaining masonry TOP/CAP/FACE and bounded transition fringes. Protect actual sky, trees, props, cliffs and externalwater outside the existing constructed coast link. Raw building layers remain exact.','structural_check_scope':'One actual public geometry-only authoring replay is authorized separately. Even a positive result does not approve rejected materials or permit final admission/negative/stage work.'})
 print(json.dumps({'guide':str(G),'guide_index_sha256':sha(G/'guide-index.json'),'states':len(rows),'five_new_public_links':len(links),'structural_stair_fields':len(stairs),'source_reference_sha256':sha(SOURCE),'bytes':sum(p.stat().st_size for p in G.rglob('*')if p.is_file())}))
if __name__=='__main__':main()
