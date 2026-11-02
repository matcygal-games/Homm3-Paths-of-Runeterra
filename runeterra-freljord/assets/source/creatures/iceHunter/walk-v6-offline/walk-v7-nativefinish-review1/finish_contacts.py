"""ONE localized own-paint/UV/equipment finish, opposite contacts only.

Old authors, selected masters, joints and all non-equipment vertices are inputs.
No phase-dependent UV or sprite/cutout compositing. No new body animation.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / 'equipment-sculpt-pass'))
sys.path.insert(0, str(HERE.parent))
import author_pass as prior
import raster_finish

original, fit, previous = prior.original, prior.fit, prior.previous
PROJECT = original.PROJECT
REPORT = original.REPORT / 'independent-finishing-pass'
NAME = HERE.name
UNITS = original.UNITS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True) + '\n'


def root_for(unit):
    return original.candidate_root(unit) / NAME


def contract(unit):
    veteran = unit == 'veteranIceHunter'
    landmarks = prior.landmarks_for(unit)
    # Native contour traces: lower nock -> unchanged wrist grip -> upper nock.
    # Half-widths deliberately vary along the wood; Veteran hooks are geometry,
    # not short pale cylinders laid over the end of the old bow.
    controls = ([[215,242],[218,241],[221,236],[222,231],[228,227],[232,222],
                 [234,216],[233,210],[234,207],[236,204]] if veteran else
                [[207,241],[211,238],[215,230],[220,228],[224,223],
                 [226,218],[227,212],[229,208]])
    widths = ([.28,.58,.78,.88,.90,.85,.73,.68,.45,.18] if veteran else
              [.25,.48,.72,.82,.86,.75,.55,.20])
    return {'unit': unit, 'one_painting_pass': True, 'selected': False,
            'canvas': [450,400], 'pivot': [197,266], 'phases': [0,3],
            'camera': {'scale': fit.SCALE, 'right': fit.RIGHT.tolist(), 'up': fit.UP.tolist(), 'view': fit.VIEW.tolist()},
            'bow_native_center_trace': controls, 'bow_halfwidth_native': widths,
            'bow_grip_control_index': 3 if veteran else 2,
            'contour_reference': 'Own selected holding-cell master through saved source camera; deliberate local native contour trace, not an automated match score',
            'string_radius_world': .0147, 'string_nominal_diameter_native_px': .79968,
            'feather_axial_length_world': .24, 'feather_vane_width_world': .074,
            'feather_tip_native': landmarks['arrow_tips'],
            'shoulder_arm_rects': {'near': [185,210,196,238] if veteran else [180,208,194,237],
                                   'far': [205,212,226,236] if veteran else [202,211,219,235]},
            'waist_shadow_rect': [191,239,203,244] if veteran else [188,238,200,243],
            'geometry_change_allowlist': ['continuous_wood_bow','continuous_taut_string','leather_bow_grip',
                'lower_pale_recurve','upper_pale_recurve','measured_arrow_shaft_*','measured_feather_*'],
            'uv_paint_change_allowlist': ['*_continuous_arm_island','fitted_*_pauldron','*_sculpt_*',
                                         'closed_leather_quiver','quiver_mouth_binding'],
            'paint_definition': {'shoulder': 'Separate near/far own projected padded islands, shared pauldron/arm UV; soft two-sided shoulder boundary bridge sampled from own paint',
                 'thigh': 'Own upper-leg paint; upper hem shadow feathered into top 16 percent of longitudinal island',
                 'calf': 'Own boot upper 68 percent, continuous long axis, painted light not re-lit',
                 'foot': 'Own boot lower 38 percent; cuff-to-vamp longitudinal mapping, no repeated calf highlight',
                 'feather': 'Own painted feather sample with deliberate central rachis, alternating diagonal gold/dark barbs and darker outside edge; opaque material on actual three-vane mesh',
                 'bow': 'Own warm wood longitudinal gradient/ridge and grip bindings; Veteran pale recurve edge painted into tapered hooked surface, not added cap'},
            'limits': ['One view own painted reference does not supply every unseen surface',
                       'Contact candidate only, no identity gate or human approval', 'No cycle expansion or selection']}


def holding_inputs(unit):
    base = PROJECT / 'assets/source/creatures' / unit
    evidencepath = base / 'registered-v3/production-evidence-v2.json'
    holding = next(row for row in json.loads(evidencepath.read_text())['source_cells'] if row['group'] == 2 and row['frame'] == 0)
    masterpath = PROJECT / holding['master']
    assert sha(masterpath) == holding['master_sha256']
    return Image.open(masterpath).convert('RGBA'), holding, evidencepath, masterpath


def patch_rgb(master, holding, rect, size=None):
    result = Image.fromarray(fit.fill_texture(previous.master_patch(master, holding, rect, 8)).astype(np.uint8))
    return result.resize(size, Image.Resampling.BICUBIC) if size else result


def warm_palette(image):
    pixels = np.asarray(image, float).reshape(-1,3)
    warm = pixels[(pixels[:,0] > pixels[:,2]*1.22) & (pixels[:,0] > 40)]
    if not len(warm):
        raise ValueError('own warm paint missing')
    return [np.percentile(warm, percentile, axis=0) for percentile in (20,55,92)]


def shoulder_paint(master, holding, rect, point):
    image = patch_rgb(master, holding, rect)
    rgb = np.asarray(image, float).copy()
    x0, y0, x1, y1 = rect
    # Two-sided local colour bridge across the selected shoulder/upper arm.
    # Painted in the rest island once, not image-space pose blending.
    sx = (point[0]-x0)*8
    sy = (point[1]+.7-y0)*8
    yy, xx = np.mgrid[:rgb.shape[0], :rgb.shape[1]]
    top_y = int(np.clip(sy-10, 0, rgb.shape[0]-1))
    bot_y = int(np.clip(sy+16, 0, rgb.shape[0]-1))
    x = int(np.clip(sx, 2, rgb.shape[1]-3))
    top = np.median(rgb[top_y, x-2:x+3], axis=0)
    bottom = np.median(rgb[bot_y, x-2:x+3], axis=0)
    amount = np.clip((yy-(sy-10))/26, 0, 1)
    bridge = top[None,None,:]*(1-amount[:,:,None])+bottom[None,None,:]*amount[:,:,None]
    mask = np.clip(1-((xx-sx)/16)**2-((yy-sy)/21)**2, 0, 1)*.67
    rgb = rgb*(1-mask[:,:,None])+bridge*mask[:,:,None]
    return Image.fromarray(np.clip(rgb,0,255).astype(np.uint8))


def make_materials(unit, output):
    output.mkdir(parents=True, exist_ok=False)
    folder = output / 'materials'
    folder.mkdir()
    spec = contract(unit)
    landmarks = prior.landmarks_for(unit)
    master, holding, evidencepath, masterpath = holding_inputs(unit)
    material = {}
    provenance = {'master': masterpath.relative_to(PROJECT).as_posix(), 'master_sha256': sha(masterpath),
                  'holding_camera': holding, 'evidence_sha256': sha(evidencepath), 'materials': {}}
    def save(name, image, region, method):
        path = folder / (name+'.png')
        image.convert('RGB').save(path)
        material[name] = {'pixels': np.asarray(image.convert('RGB'),float), 'baked': True}
        provenance['materials'][name] = {'source_native_region': region, 'method': method, 'sha256': sha(path), 'baked': True}
    original_upper = patch_rgb(master, holding, fit.TEXTURE_CROP, (300,228))
    # Reuse exact original material array for unedited head/face/torso/mantle.
    original_upper = Image.open(prior.root_for(unit)/'contacts-finish/source-upperbody-rgb.png').convert('RGB')
    save('source_upperbody', original_upper, list(fit.TEXTURE_CROP), 'Exact preserved original upper-body material; sampler unchanged')
    for side in ('near','far'):
        save('finish_'+side+'_shoulder_arm', shoulder_paint(master,holding,spec['shoulder_arm_rects'][side],landmarks[side+'_arm'][0]),
             spec['shoulder_arm_rects'][side], 'Own paint local projected UV bridge shared by shoulder and continuous arm, padded opaque RGB')
    boot = landmarks['boot_texture_patch']
    thigh = landmarks['upper_leg_texture_patch']
    shadow = np.asarray(patch_rgb(master,holding,spec['waist_shadow_rect']),float)
    shadow_color = np.percentile(shadow.reshape(-1,3),35,axis=0)
    upper = np.asarray(patch_rgb(master,holding,thigh,(128,256)),float)
    y = np.arange(256)[:,None,None]/255
    weight = np.clip(1-y/.16,0,1)*.78
    upper = upper*(1-weight)+shadow_color[None,None,:]*weight
    save('finish_thigh',Image.fromarray(upper.astype(np.uint8)),thigh,'Single longitudinal own trouser island with painted upper hem shadow transition')
    h = boot[3]-boot[1]
    calfrect = [boot[0],boot[1],boot[2],boot[1]+h*.68]
    footrect = [boot[0],boot[1]+h*.62,boot[2],boot[3]]
    kneerect = [thigh[0],thigh[3]-3,thigh[2],thigh[3]]
    save('finish_calf',patch_rgb(master,holding,calfrect,(128,256)),calfrect,'Own upper boot longitudinal RGB, no repeated vamp highlight, no analytic relighting')
    save('finish_foot',patch_rgb(master,holding,footrect,(128,128)),footrect,'Own lower boot vamp/sole island; material follows real foot ring height')
    save('finish_knee',patch_rgb(master,holding,kneerect,(96,96)),kneerect,'Own knee junction source paint; no duplicated calf stripe')
    for index,amount in enumerate((.28,.57,.86)):
        # Calf v=0 at ankle and1 at knee in the final material coordinate.
        native_y = calfrect[3]-(calfrect[3]-calfrect[1])*amount
        rect = [boot[0],native_y-.55,boot[2],native_y+.55]
        save('finish_binding_'+str(index),patch_rgb(master,holding,rect,(128,24)),rect,'Separate binding island sampled at corresponding physical calf height')
    quiver = [184,200,194,214] if unit=='veteranIceHunter' else [181,202,191,215]
    save('finish_quiver',patch_rgb(master,holding,quiver,(96,160)),quiver,'Own painted leather quiver, clamped longitudinal UV')
    featherrect = [183,196,193,208] if unit=='veteranIceHunter' else [180,198,190,209]
    featherpatch = patch_rgb(master,holding,featherrect,(64,128))
    dark, middle, gold = warm_palette(featherpatch)
    # Deliberate editable feather painting: axial rachis and staggered barbs.
    yy,xx = np.mgrid[:128,:64]
    ridge = np.exp(-((xx-30)/9)**2)
    edge = np.clip(np.minimum(xx,63-xx)/9,0,1)
    feather = middle[None,None,:]*.65 + np.asarray(featherpatch,float)*.35
    feather = feather*(.73+.27*edge[:,:,None])
    feather = feather*(1-ridge[:,:,None]*.50)+gold[None,None,:]*ridge[:,:,None]*.50
    fim = Image.fromarray(np.clip(feather,0,255).astype(np.uint8))
    draw = ImageDraw.Draw(fim)
    color = lambda v: tuple(np.clip(v,0,255).astype(int))
    draw.line([(30,2),(31,125)], fill=color(gold), width=3)
    for j in range(11,125,12):
        draw.line([(31,j+5),(5,j-7)],fill=color(gold*.93),width=2)
        draw.line([(33,j+7),(58,j-4)],fill=color(middle*.70),width=2)
        draw.line([(31,j+8),(7,j-1)],fill=color(dark),width=1)
    save('finish_feather',fim,featherrect,'Painted golden rachis, diagonal barbs, dark edge; opaque three-dimensional vane UV, not palette noise')
    # Wood paint follows length; ridge follows side, rather than projected background.
    bowrect = [215,212,230,237] if unit=='iceHunter' else [222,205,237,237]
    woodpatch = patch_rgb(master,holding,bowrect,(64,256))
    wd, wm, wh = warm_palette(woodpatch)
    yy,xx = np.mgrid[:256,:64]
    cross = np.exp(-((xx-22)/14)**2)
    wood = wm[None,None,:]*(.64+.36*cross[:,:,None])+np.asarray(woodpatch,float)*.16
    wood *= (1+.025*np.cos(yy[:,:,None]*.21))
    if unit=='veteranIceHunter':
        ownpale = np.asarray(patch_rgb(master,holding,[232,203,237,211]),float)
        pale = np.percentile(ownpale.reshape(-1,3),91,axis=0)
        ends = np.maximum(np.clip((.16-yy/255)/.12,0,1),np.clip((yy/255-.82)/.15,0,1))
        edge = (.35+.65*np.exp(-((xx-17)/16)**2))*ends
        wood = wood*(1-edge[:,:,None])+pale[None,None,:]*edge[:,:,None]
    save('finish_bow',Image.fromarray(np.clip(wood,0,255).astype(np.uint8)),bowrect,'Longitudinal warm wood ridge; Veteran own pale inlaid recurve edge on integrated tapered hook')
    string = np.zeros((128,16,3),float)
    string[:] = gold*.82+wh*.18
    string *= (.86+.14*np.sin(np.linspace(0,math.pi,16))[None,:,None])
    save('finish_string',Image.fromarray(np.clip(string,0,255).astype(np.uint8)),featherrect,'Own warm light fibre paint, non-repeating along actual string; explicit0.8px nominal geometry')
    lines=[]
    for name in material:
        lines += ['newmtl '+name,'Kd 1 1 1','map_Kd materials/'+name+'.png','']
    (output/'materials.mtl').write_text('\n'.join(lines),encoding='ascii')
    (output/'material-provenance.json').write_text(encoded(provenance),encoding='utf-8')
    return material, provenance


def part_ids(mesh, name):
    return sorted({i for face,part in zip(mesh.faces,mesh.parts) if part==name for i in face})


def change_material(mesh, part, name):
    for i, label in enumerate(mesh.parts):
        if label == part:
            mesh.materials[i] = name


def tube_uv(surface, points, halfwidths, material, name, depth_ratio=.55, sides=12):
    points=np.asarray(points,float)
    lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    start=len(surface.vertices)
    for i,p in enumerate(points):
        tangent=original.normalize(points[min(i+1,len(points)-1)]-points[max(0,i-1)])
        cross=original.normalize(np.cross(tangent,fit.VIEW))
        depth=original.normalize(np.cross(tangent,cross))
        for j in range(sides+1):
            angle=math.tau*j/sides
            surface.vertices.append(p+halfwidths[i]*(math.cos(angle)*cross+depth_ratio*math.sin(angle)*depth))
            surface.uv.append((j/sides,1-lengths[i]/lengths[-1]))
    for i in range(len(points)-1):
        for j in range(sides):
            a=start+i*(sides+1)+j
            for face in ((a,a+1,a+sides+2),(a,a+sides+2,a+sides+1)):
                surface.faces.append(face);surface.materials.append(material);surface.parts.append(name)
    for row,reverse in ((0,True),(len(points)-1,False)):
        center=len(surface.vertices)
        surface.vertices.append(points[row]);surface.uv.append((.5,1-lengths[row]/lengths[-1]))
        for j in range(sides):
            face=(center,start+row*(sides+1)+j,start+row*(sides+1)+j+1)
            surface.faces.append(face[::-1] if reverse else face);surface.materials.append(material);surface.parts.append(name)


def author(t,unit):
    landmarks=prior.landmarks_for(unit)
    old,joints=prior.author(t,unit,landmarks)
    removed=lambda part: part in {'continuous_wood_bow','continuous_taut_string','leather_bow_grip','lower_pale_recurve','upper_pale_recurve'} or part.startswith(('measured_arrow_shaft_','measured_feather_'))
    mesh=fit.subset(old,lambda part:not removed(part))
    spec=contract(unit)
    for side in ('near','far'):
        rect=spec['shoulder_arm_rects'][side]
        for part in (side+'_continuous_arm_island','fitted_'+side+'_pauldron'):
            for index in part_ids(mesh,part):
                u,v=mesh.uv[index]
                x,y=165+u*75,245-v*57
                mesh.uv[index]=((x-rect[0])/(rect[2]-rect[0]),1-(y-rect[1])/(rect[3]-rect[1]))
            change_material(mesh,part,'finish_'+side+'_shoulder_arm')
        for part,mat,cols,rows,reverse in ((side+'_sculpt_thigh','finish_thigh',12,6,True),
                (side+'_sculpt_calf_boot','finish_calf',12,6,True),
                (side+'_sculpt_foot','finish_foot',20,6,False),
                (side+'_sculpt_knee','finish_knee',14,8,False)):
            ids=part_ids(mesh,part)
            for slot,index in enumerate(ids):
                if slot<cols*rows:
                    # Same physical surface, separately padded longitudinal UV island.
                    row,col=divmod(slot,cols)
                    v=row/(rows-1)
                    mesh.uv[index]=(col/cols,1-v if reverse else v)
                else:
                    mesh.uv[index]=(.5,0 if slot==cols*rows else 1)
            change_material(mesh,part,mat)
        for index in range(3):
            part=side+'_sculpt_binding_'+str(index)
            for slot,vertex in enumerate(part_ids(mesh,part)):
                row,col=divmod(slot,16)
                mesh.uv[vertex]=(col/16,1-row)
            change_material(mesh,part,'finish_binding_'+str(index))
    for part in ('closed_leather_quiver','quiver_mouth_binding'):
        for index in part_ids(mesh,part):
            u,v=mesh.uv[index]
            mesh.uv[index]=(u/.49999,v/.49999)
        change_material(mesh,part,'finish_quiver')
    equipment=original.Surface()
    controls=np.array([fit.unproject(*point,-.015) for point in spec['bow_native_center_trace']])
    grip_idx=spec['bow_grip_control_index']
    wrist=np.array(joints['arms']['far']['wrist'])
    rest_wrist=fit.unproject(*landmarks['far_arm'][2],-.015)
    controls+=wrist-rest_wrist
    curve=prior.smooth_curve(controls)
    # Same Catmull-Rom node correspondence, tapered elliptical cross sections.
    widths=np.interp(np.linspace(0,len(controls)-1,len(curve)),np.arange(len(controls)),spec['bow_halfwidth_native'])/fit.SCALE
    tube_uv(equipment,curve,widths,'finish_bow','finished_tapered_bow')
    tube_uv(equipment,[controls[0],controls[-1]],[spec['string_radius_world']]*2,'finish_string','finished_taut_string',1,sides=8)
    grip=curve[grip_idx*6]
    tube_uv(equipment,[grip-(0,0,.043),grip+(0,0,.043)],[.033,.033],'finish_quiver','finished_bound_grip',1)
    joints['bow']={'handle':grip.tolist(),'hand_side':'far','attachment_error':float(np.linalg.norm(grip-wrist)),
                   'nocks':[controls[0].tolist(),controls[-1].tolist()], 'string_nominal_native_diameter':.79968}
    move=fit.body_transform(t)
    qbottom,qtop=(move(fit.unproject(*p,-.12)) for p in landmarks['quiver'])
    for index,tip in enumerate(landmarks['arrow_tips']):
        top=move(fit.unproject(*tip,-.10))
        bottom=qbottom*.78+qtop*.22
        tube_uv(equipment,[bottom,top],[.009,.009],'finish_bow','finished_arrow_shaft_'+str(index),1,sides=8)
        direction=original.normalize(top-bottom)
        radial=original.normalize(np.cross(direction,fit.VIEW))
        radial2=original.normalize(np.cross(direction,radial))
        length=spec['feather_axial_length_world']
        width=spec['feather_vane_width_world']
        for vane_index,angle in enumerate((0,math.tau/3,2*math.tau/3)):
            across=math.cos(angle)*radial+math.sin(angle)*radial2
            start=len(equipment.vertices)
            # Real convex vane with longitudinal UV; no alpha-defined silhouette.
            for along,lateral,uv in ((0,0,(.5,0)),(.17,width*.63,(1,.17)),
                                      (.69,width,(1,.69)),(.94,width*.34,(.68,.94)),(1,0,(.5,1))):
                equipment.vertices.append(top-direction*length*(1-along)+across*lateral)
                equipment.uv.append(uv)
            for face in ((0,1,2),(0,2,3),(0,3,4)):
                equipment.faces.append(tuple(start+i for i in face));equipment.materials.append('finish_feather')
                equipment.parts.append('finished_feather_'+str(index)+'_'+str(vane_index))
    prior.add_mesh(mesh,equipment)
    return mesh,joints


def render(mesh,materials):
    return raster_finish.render(mesh,materials,fit,original)


def source_pins(unit):
    _,_,evidence,master=holding_inputs(unit)
    paths=[Path(__file__),HERE/'raster_finish.py',Path(prior.__file__),Path(fit.__file__),
           Path(previous.__file__),Path(original.__file__),evidence,master]
    filename='identity-fit-second-reachfix-landmarks.json' if unit=='veteranIceHunter' else 'identity-fit-second-landmarks.json'
    paths.append(HERE.parent/filename)
    return {p.relative_to(PROJECT).as_posix():sha(p) for p in paths}


def assemble(unit,label):
    root=root_for(unit)
    root.mkdir(parents=True,exist_ok=True)
    definition=contract(unit)
    dependencies=source_pins(unit)
    if label=='contacts-a':
        for path,value in ((root/'finish-contract.json',definition),(root/'source-pins.json',dependencies)):
            if path.exists():raise ValueError('Preserve existing source contract')
            path.write_text(encoded(value),encoding='utf-8')
    else:
        assert json.loads((root/'finish-contract.json').read_text())==definition
        assert json.loads((root/'source-pins.json').read_text())==dependencies
    output=root/label
    materials,provenance=make_materials(unit,output)
    records=[]
    for phase in (0,3):
        mesh,joints=author(phase/6,unit)
        image=render(mesh,materials)
        png=output/f'g00-f{phase:03}.png'
        obj=output/f'phase{phase}.obj'
        image.save(png);mesh.export_obj(obj)
        uv={part:{'materials':sorted({m for p,m in zip(mesh.parts,mesh.materials) if p==part}),
                 'uv':[list(mesh.uv[i]) for i in part_ids(mesh,part)]} for part in sorted(set(mesh.parts))}
        (output/f'phase{phase}-uv-islands.json').write_text(encoded(uv),encoding='utf-8')
        records.append({'phase':phase,'png_sha256':sha(png),'obj_sha256':sha(obj),'joints':joints,
                        'vertices':len(mesh.vertices),'triangles':len(mesh.faces)})
    files={p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()}
    receipt={'unit':unit,'status':'built-unreviewed','selected':False,'human_visual_approval':False,
             'identity_gate_pass':False,'production_ready':False,'phase_records':records,
             'canvas':[450,400],'pivot':[197,266],'source_pins':dependencies,'files':files,
             'contract_sha256':sha(root/'finish-contract.json'),'material_provenance':provenance}
    (output/'receipt.json').write_text(encoded(receipt),encoding='utf-8')
    print(encoded({'unit':unit,'assembly':label,'receipt_sha256':sha(output/'receipt.json'),
                   'frames':[{k:v for k,v in row.items() if k in ('phase','png_sha256','obj_sha256')} for row in records]}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('unit',choices=UNITS)
    parser.add_argument('label',choices=('contacts-a','contacts-b'))
    args=parser.parse_args()
    assemble(args.unit,args.label)
