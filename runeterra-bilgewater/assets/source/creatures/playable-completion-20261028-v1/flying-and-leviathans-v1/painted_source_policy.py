"""Shared painted creature provenance gate, preserved from inspected Targon implementation. This never produces or approves artwork.

Recipe provenance is project metadata, not a VCMI field. Existing native-size,
all-frame art review and release/rights consumers remain mandatory afterwards.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path,PurePosixPath

WORKFLOW='image-based-painted-2d'
OPERATIONS={'fixed-canvas','root-placement','alpha-cleanup','shadow-treatment','frame-assembly','png-conversion'}
FORBIDDEN_FIELDS={'geometry_source','geometry_sha256','editable_scene','renderer_source','renderer_sha256','parent_renderer_sha256','parent_full_source_pose_sha256'}
SHA=re.compile(r'[0-9a-f]{64}')

def read(path):
 def unique(pairs):
  result={}
  for key,value in pairs:
   if key in result:raise ValueError('Duplicate JSON key: '+key)
   result[key]=value
  return result
 return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique)

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(65536),b''):h.update(block)
 return h.hexdigest()

def own(root,name):
 if not isinstance(name,str):raise ValueError('Missing own provenance path')
 relative=PurePosixPath(name)
 if '\\' in name or ':' in name or relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0]!='assets':raise ValueError('Provenance must stay under own assets')
 path=Path(root).resolve()/name
 if not path.resolve().is_relative_to(Path(root).resolve()/'assets'):raise ValueError('Provenance escapes own assets')
 for item in (path,*path.parents):
  if item==Path(root).resolve():break
  if item.is_symlink() or item.exists() and getattr(item.stat(),'st_file_attributes',0)&0x400:raise ValueError('Redirected provenance path')
 return path

def walk(value):
 if isinstance(value,dict):
  for key,item in value.items():
   yield key,item
   yield from walk(item)
 elif isinstance(value,list):
  for item in value:yield from walk(item)

def blender_lineage(value):
 for key,item in walk(value):
  if key in FORBIDDEN_FIELDS and item not in (None,'',False):return True
  if isinstance(item,str) and re.search(r'(?i)\.blend(?:\d+|~)?(?:$|[\s?#])',item):return True
  if key in ('provider','method','producer','assembly_method') and isinstance(item,str) and re.search(r'(?i)\bblender\b|\bbpy\b',item):return True
 return False

def recipe_errors(root,recipe,rejected_hashes):
 errors=[]
 if blender_lineage(recipe):errors.append('Blender geometry/render lineage is forbidden for replacement creature art')
 generation=recipe.get('generation',{})
 if not isinstance(generation,dict) or generation.get('workflow')!=WORKFLOW:
  return errors+['Missing painted-2D replacement provenance; image_generation_used alone is insufficient']
 try:
  ledger_path=own(root,generation.get('source_generation_ledger'))
  if not ledger_path.is_file() or generation.get('source_generation_ledger_sha256')!=sha(ledger_path):raise ValueError('Missing/changed source generation ledger')
  ledger=read(ledger_path)
  if ledger.get('workflow')!=WORKFLOW or ledger.get('derived_from_blender') is not False or ledger.get('user_rejected') is not False or blender_lineage(ledger):raise ValueError('Ledger is not an unrejected painted-2D origin')
  operations=ledger.get('assembly_operations')
  if not isinstance(operations,list) or any(operation not in OPERATIONS for operation in operations):raise ValueError('Unknown/creative-code assembly operation')
  pins=ledger.get('files_sha256');origins=ledger.get('origins')
  if not isinstance(pins,dict) or not pins or not isinstance(origins,list) or not origins:raise ValueError('Missing concrete painted/image origin or file closure')
  for origin in origins:
   if not isinstance(origin,dict) or origin.get('kind') not in ('painted-2d-master','image-generation'):raise ValueError('Origin is not painted/image-based')
   if pins.get(origin.get('path'))!=origin.get('sha256'):raise ValueError('Origin absent from hash-bound closure')
  sources={item for key,item in walk(recipe) if key in ('source','painted_master','producer_source') and isinstance(item,str) and item.startswith('assets/')}
  if not sources or not sources.issubset(pins):raise ValueError('Actual selected source/producer omitted from provenance closure')
  for name,pin in pins.items():
   path=own(root,name)
   if not SHA.fullmatch(str(pin)) or not path.is_file() or sha(path)!=pin:raise ValueError('Provenance input missing/changed: '+str(name))
   if pin in rejected_hashes:raise ValueError('User-rejected old creature bytes reused: '+str(name))
   if re.fullmatch(r'(?i)\.blend(?:\d+|~)?',path.suffix):raise ValueError('Blender scene in input closure')
   if path.suffix.casefold()=='.py' and re.search(r'\b(?:import\s+bpy|from\s+bpy\b)',path.read_text(encoding='utf-8')):raise ValueError('Blender producer in input closure')
 except (OSError,ValueError,TypeError) as error:errors.append(str(error))
 return errors
