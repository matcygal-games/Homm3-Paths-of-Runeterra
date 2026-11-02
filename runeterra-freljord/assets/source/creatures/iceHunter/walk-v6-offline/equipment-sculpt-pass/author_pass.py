"""One concentrated private equipment/material/surface pass, no shared edits.

Actual new calf/boot/sole geometry follows unchanged fixed IK chains. Equipment
uses dedicated opaque materials, never background-projected body texels.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import author_cohort as original
import identity_fit as fit
import identity_fit_second as previous

PROJECT = original.PROJECT
REPORT = original.REPORT / "equipment-sculpt-pass"
PASS_NAME = "equipment-sculpt-pass"


def root_for(unit):
    return original.candidate_root(unit) / PASS_NAME


def landmarks_for(unit):
    filename = "identity-fit-second-reachfix-landmarks.json" if unit == "veteranIceHunter" else "identity-fit-second-landmarks.json"
    return json.loads((HERE.parent / filename).read_text())[unit]


def add_mesh(target, source):
    start = len(target.vertices)
    target.vertices.extend(source.vertices)
    target.uv.extend(source.uv)
    target.faces.extend(tuple(start+i for i in face) for face in source.faces)
    target.materials.extend(source.materials)
    target.parts.extend(source.parts)


def cap_rings(surface, rings, material, name):
    start = len(surface.vertices)
    surface.patch(rings, material, name)
    count = len(rings[0])
    for row, reverse in ((0,True),(len(rings)-1,False)):
        center = len(surface.vertices)
        surface.vertices.append(np.mean(rings[row],axis=0))
        surface.uv.append((.5,row/max(1,len(rings)-1)))
        for i in range(count):
            face = (center,start+row*count+i,start+row*count+(i+1)%count)
            surface.faces.append(face[::-1] if reverse else face)
            surface.materials.append(material)
            surface.parts.append(name)


def tube(surface, points, radius, material, name, sides=12):
    points = np.asarray(points,float)
    rings=[]
    for i,point in enumerate(points):
        tangent = original.normalize(points[min(i+1,len(points)-1)]-points[max(0,i-1)])
        cross = original.normalize(np.cross(tangent,fit.VIEW))
        if np.linalg.norm(cross)<.1:
            cross=original.normalize(np.cross(tangent,fit.RIGHT))
        depth=original.normalize(np.cross(tangent,cross))
        r=radius(i/max(1,len(points)-1)) if callable(radius) else radius
        rings.append([point+r*(math.cos(a)*cross+math.sin(a)*depth)
                      for a in np.arange(sides)*math.tau/sides])
    cap_rings(surface,rings,material,name)


def smooth_curve(controls, subdivisions=6):
    controls=np.asarray(controls,float)
    points=[]
    for i in range(len(controls)-1):
        a=controls[max(0,i-1)];b=controls[i];c=controls[i+1];d=controls[min(len(controls)-1,i+2)]
        for j in range(subdivisions):
            t=j/subdivisions
            points.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    points.append(controls[-1])
    return np.array(points)


def sculpt_legs(t,joints):
    surface=original.Surface()
    contact_records={}
    for side in ("far","near"):
        leg=joints["legs"][side]
        hip,knee,ankle=(np.array(leg[key]) for key in ("hip","knee","ankle"))
        factor=1 if side=="near" else .95
        surface.limb(hip,knee,.140*factor,.102*factor,"trouser_leather",side+"_sculpt_thigh",.91)
        surface.oval(knee,(.105*factor,.095*factor,.088),"boot_leather",side+"_sculpt_knee")
        surface.limb(knee,ankle,.135*factor,.087*factor,"boot_leather",side+"_sculpt_calf_boot",.92)
        for index,amount in enumerate((.28,.57,.86)):
            center=ankle*(1-amount)+knee*amount
            axis=original.normalize(knee-ankle)
            cross=original.normalize(np.cross(axis,(0,1,0)))
            depth=original.normalize(np.cross(axis,cross))
            radius=(.087*(1-amount)+.135*amount)*factor*1.025
            rings=[]
            for offset in (-.012,.012):
                rings.append([center+axis*offset+radius*(math.cos(a)*cross+.92*math.sin(a)*depth)
                              for a in np.arange(16)*math.tau/16])
            surface.patch(rings,"boot_binding",side+"_sculpt_binding_"+str(index))
        foot,foot_record=original.foot_pose(t,side)
        profiles=((0,.170,.088,.010),(.025,.171,.092,.009),(.065,.154,.087,.008),
                  (.120,.108,.077,-.004),(.175,.073,.067,-.010),(.205,.062,.062,-.013))
        rings=[]
        for z,rx,ry,cx in profiles:
            rings.append([foot((cx+rx*math.cos(a),ry*math.sin(a),z))
                          for a in np.arange(20)*math.tau/20])
        cap_rings(surface,rings,"boot_leather",side+"_sculpt_foot")
        contact_records[side]={"actual_sole_toe_vertex":np.asarray(rings[0][0]).tolist(),
                               "planned_toe":foot_record["contact_toe"],
                               "sole_width_world":.176,"maximum_pitch":.52}
    joints["sculpt_surface_contacts"]=contact_records
    return surface


def arm_surface(s,e,w,name):
    surface=original.Surface()
    rings=[]
    positions=[(s*(1-t)+e*t,.076*(1-t)+.063*t) for t in (0,.20,.45,.70,.88)]
    positions.append((e,.064))
    positions.extend((e*(1-t)+w*t,.063*(1-t)+.047*t) for t in (.12,.30,.55,.80,1))
    for i,(point,radius) in enumerate(positions):
        tangent=original.normalize(positions[min(i+1,len(positions)-1)][0]-positions[max(0,i-1)][0])
        cross=original.normalize(np.cross(tangent,fit.VIEW))
        depth=original.normalize(np.cross(tangent,cross))
        rings.append([point+radius*(math.cos(a)*cross+.90*math.sin(a)*depth)
                      for a in np.arange(16)*math.tau/16])
    cap_rings(surface,rings,"source_upperbody",name)
    return surface


def author(t,unit,landmarks):
    old,joints=previous.author(t,unit,landmarks)
    joints.pop("old_leg_vertices_unchanged",None)
    joints["leg_surface_sculpt_changed"]=True
    # Retain the matched hood/hair/face/torso/mantle, actual hands and pauldrons.
    retained={"fitted_head_closed_surface","fitted_torso_closed_surface","source_matched_folded_mantle",
              "near_actual_hand","far_actual_hand","fitted_near_pauldron","fitted_far_pauldron"}
    mesh=fit.subset(old,lambda name:name in retained)
    add_mesh(mesh,sculpt_legs(t,joints))
    for side in ("far","near"):
        depth=.25 if side=="near" else -.015
        s,e,w=(fit.unproject(*point,depth) for point in landmarks[side+"_arm"])
        arm=joints["arms"][side]
        ps,pe,pw=(np.array(arm[key]) for key in ("shoulder","elbow","wrist"))
        rest=arm_surface(s,e,w,side+"_continuous_arm_island")
        posed=arm_surface(ps,pe,pw,side+"_continuous_arm_island")
        fit.append_reference(mesh,rest,posed)
    # One connected, smoothly curved opaque bow material, including the real grip node.
    rest_controls=np.array([fit.unproject(*point,-.015) for point in landmarks["bow"]])
    rest_hand=fit.unproject(*landmarks["far_arm"][2],-.015)
    actual_hand=np.array(joints["arms"]["far"]["wrist"])
    delta=actual_hand-rest_hand
    controls=rest_controls+delta
    curve=smooth_curve(controls)
    equipment=original.Surface()
    tube(equipment,curve,lambda x:.026*(.72+.28*math.sin(math.pi*x)),"bow_wood","continuous_wood_bow")
    tube(equipment,[controls[0],controls[-1]],.0055,"bow_string","continuous_taut_string",sides=8)
    grip_index=landmarks["bow_grip_index"]*6
    grip=curve[grip_index]
    tube(equipment,[grip-(0,0,.045),grip+(0,0,.045)],.032,"quiver_leather","leather_bow_grip")
    if unit=="veteranIceHunter":
        for name,points in (("lower_pale_recurve",curve[:5]),("upper_pale_recurve",curve[-5:])):
            tube(equipment,points,.021,"bow_tip",name)
    joints["bow"]={"handle":grip.tolist(),"hand_side":"far",
                   "attachment_error":float(np.linalg.norm(grip-actual_hand)),
                   "curve_node_count":len(curve),"continuous_material":"bow_wood",
                   "nocks":[controls[0].tolist(),controls[-1].tolist()]}
    move=fit.body_transform(t)
    qbottom,qtop=(move(fit.unproject(*point,-.12)) for point in landmarks["quiver"])
    tube(equipment,[qbottom,qtop],lambda x:.078+.008*x,"quiver_leather","closed_leather_quiver")
    axis=original.normalize(qtop-qbottom)
    across=original.normalize(np.cross(axis,fit.VIEW))
    around=original.normalize(np.cross(axis,across))
    rim=[qtop+.089*(math.cos(a)*across+math.sin(a)*around) for a in np.linspace(0,math.tau,17)]
    tube(equipment,rim,.010,"quiver_binding","quiver_mouth_binding",sides=8)
    feather_records=[]
    for index,tip in enumerate(landmarks["arrow_tips"]):
        top=move(fit.unproject(*tip,-.10))
        shaft_start=qbottom*.78+qtop*.22
        tube(equipment,[shaft_start,top],.009,"arrow_wood","measured_arrow_shaft_"+str(index),sides=8)
        direction=original.normalize(top-shaft_start)
        radial=original.normalize(np.cross(direction,fit.VIEW))
        radial2=original.normalize(np.cross(direction,radial))
        base=top-direction*.13
        vanes=[math.cos(angle)*radial+math.sin(angle)*radial2 for angle in (0,math.tau/3,2*math.tau/3)]
        for vane_index,vane in enumerate(vanes):
            vertices=[base,base+direction*.045+vane*.060,
                      base+direction*.095+vane*.043,top]
            start=len(equipment.vertices)
            equipment.vertices.extend(vertices)
            equipment.uv.extend(((0,0),(1,.3),(1,.7),(0,1)))
            for face in ((start,start+1,start+2),(start,start+2,start+3)):
                equipment.faces.append(face)
                equipment.materials.append("arrow_fletching")
                equipment.parts.append("measured_feather_"+str(index)+"_"+str(vane_index))
        feather_records.append({"reference_tip_native":tip,"posed_tip_world":top.tolist()})
    joints["quiver"]={"arrow_count":len(feather_records),"measured_fletching":feather_records,
                      "body_endpoints":[qbottom.tolist(),qtop.tolist()]}
    add_mesh(mesh,equipment)
    # Private renderer tiles regular materials twice; each surface island uses
    # half-domain UVs so the source leather reads once along a physical segment.
    regular={index for face,material in zip(mesh.faces,mesh.materials) if material!="source_upperbody" for index in face}
    for index in regular:
        u,v=mesh.uv[index]
        mesh.uv[index]=(u*.49999,v*.49999)
    return mesh,joints


def palette_texture(patch,kind):
    rgba=np.asarray(patch.convert("RGBA"),float)
    rgb=rgba[:,:,:3]
    valid=rgba[:,:,3]>=128
    brown=valid & (rgb[:,:,0]>rgb[:,:,2]*1.20) & (rgb[:,:,0]>25)
    samples=rgb[brown] if brown.sum()>4 else rgb[valid]
    if not len(samples):
        raise ValueError("own material sample is empty")
    color=np.percentile(samples,60,axis=0)
    if kind=="bow_tip":
        color=np.percentile(samples,92,axis=0)*np.array((1.12,1.20,1.28))
    if kind=="bow_string":
        color=np.percentile(samples,72,axis=0)*np.array((.83,.87,.91))
    if kind=="boot_binding":
        color=np.percentile(samples,74,axis=0)
    if kind=="arrow_fletching":
        color=np.percentile(samples,80,axis=0)
    y,x=np.mgrid[:64,:64]
    if "wood" in kind or kind=="bow_tip":
        detail=.045*np.sin(x*.60+np.sin(y*.20))+.025*np.cos(x*1.7+y*.08)
    else:
        detail=.05*np.sin(x*1.2+y*.5)*np.cos(y*.91)+.025*np.cos(y*.33)
    return np.clip(color[None,None,:]*(1+detail[:,:,None]),0,255),color.tolist()


def prepare_materials(unit,landmarks,output):
    reference=PROJECT/"assets/source/creatures"/unit/"registered-v3/native/g02-f000.png"
    evidencepath=reference.parents[1]/"production-evidence-v2.json"
    holding=next(cell for cell in json.loads(evidencepath.read_text())["source_cells"] if cell["group"]==2 and cell["frame"]==0)
    masterpath=PROJECT/holding["master"]
    if original.digest(masterpath)!=holding["master_sha256"]:
        raise ValueError("painted master hash changed")
    master=Image.open(masterpath).convert("RGBA")
    color=fit.fill_texture(previous.master_patch(master,holding,fit.TEXTURE_CROP,4))
    Image.fromarray(color.astype(np.uint8)).save(output/"source-upperbody-rgb.png")
    materials={"source_upperbody":{"pixels":color}}
    folder=output/"materials"
    folder.mkdir()
    specs={"bow_wood":(landmarks["bow"][3][0]-2,landmarks["bow"][3][1]-3,landmarks["bow"][-2][0]+2,landmarks["bow"][-2][1]+15),
           "bow_tip":(landmarks["bow"][-1][0]-3,landmarks["bow"][-1][1]-3,landmarks["bow"][-1][0]+2,landmarks["bow"][-1][1]+5),
           "bow_string":(landmarks["bow"][3][0]-2,landmarks["bow"][3][1]-4,landmarks["bow"][3][0]+3,landmarks["bow"][3][1]+4),
           "quiver_leather":(181,202,191,215) if unit=="iceHunter" else (184,200,194,214),
           "quiver_binding":(181,202,191,215) if unit=="iceHunter" else (184,200,194,214),
           "arrow_wood":(180,198,190,209) if unit=="iceHunter" else (183,196,193,208),
           "arrow_fletching":(180,198,190,209) if unit=="iceHunter" else (183,196,193,208),
           "trouser_leather":landmarks["upper_leg_texture_patch"],
           "boot_leather":landmarks["boot_texture_patch"],"boot_binding":landmarks["boot_texture_patch"]}
    record={}
    lines=["newmtl source_upperbody","Kd 1 1 1","map_Kd source-upperbody-rgb.png",""]
    for name,rect in specs.items():
        # Rectangles are RGB material samples only, never silhouette masks.
        rect=(min(rect[0],rect[2]),min(rect[1],rect[3]),max(rect[0],rect[2]),max(rect[1],rect[3]))
        patch=previous.master_patch(master,holding,rect,4)
        pixels,palette=palette_texture(patch,name)
        transfer="dedicated opaque palette/material island from own painted sample"
        if name in ("trouser_leather","boot_leather"):
            rgb=fit.fill_texture(patch)
            image=Image.fromarray(rgb.astype(np.uint8)).resize((64,64),Image.Resampling.BICUBIC)
            transfer="own painted leather RGB transferred as one non-alpha surface island; no silhouette or contact mask"
        else:
            image=Image.fromarray(pixels.astype(np.uint8))
        image.save(folder/(name+".png"))
        materials[name]={"pixels":np.asarray(image,float)}
        record[name]={"own_source_native_sample":list(rect),"palette_rgb":palette,"transfer":transfer,"sha256":original.digest(folder/(name+".png"))}
        lines.extend(("newmtl "+name,"Kd 1 1 1","map_Kd materials/"+name+".png",""))
    (output/"materials.mtl").write_text("\n".join(lines)+"\n",encoding="ascii")
    return materials,{"reference":str(reference.relative_to(PROJECT)),"reference_sha256":original.digest(reference),
                      "master":str(masterpath.relative_to(PROJECT)),"master_sha256":original.digest(masterpath),
                      "holding_camera":holding,"materials":record}


def run(unit,mode,label=None):
    start=time.perf_counter()
    root=root_for(unit)
    root.mkdir(exist_ok=True)
    if label and (not label.replace("-","").isalnum()):
        raise ValueError("invalid private output label")
    output=root/(label or mode)
    output.mkdir(exist_ok=False)
    report=REPORT/unit/(label or mode)
    report.mkdir(parents=True,exist_ok=False)
    landmarks=landmarks_for(unit)
    materials,provenance=prepare_materials(unit,landmarks,output)
    frames,records=[],[]
    for phase in ((0,3) if mode=="contacts" else range(6)):
        mesh,joints=author(phase/6,unit,landmarks)
        path=output/f"g00-f{phase:03d}.png"
        fit.raster(mesh,materials).save(path)
        mesh.export_obj(output/f"phase{phase}.obj")
        records.append({"phase":phase,"png":path.relative_to(PROJECT).as_posix(),"sha256":original.digest(path),
                        "mesh_sha256":original.digest(output/f"phase{phase}.obj"),"triangles":len(mesh.faces),"joints":joints})
        frames.append(path)
    original.contact_sheet(unit,frames,report/"selected-idle-versus-sculpt-native.png",PASS_NAME)
    receipt={"unit":unit,"mode":mode,"status":"built-unreviewed","selected":False,"production_ready":False,
             "human_visual_approval":False,"independent_art_approval":False,"canvas":[450,400],"pivot":[197,266],
             "camera_unchanged_from_identity_fit":True,"method":"One concentrated equipment/material/surface pass; continuous dedicated-material equipment, joined arm UV islands, thicker shaped real leg/boot surfaces on unchanged fixed IK chains.",
             "source_sha256":original.digest(Path(__file__)),"landmarks":landmarks,"provenance":provenance,
             "phases":records,"seconds":time.perf_counter()-start,
             "limits":["Art contract requires actual native comparisons, not geometry alone","No human or independent acceptance implied","Native timing/both-facing movement untested"]}
    for folder in (output,report):
        (folder/"receipt.json").write_text(original.encoded(receipt),encoding="utf-8")
    (output/"editable-inputs.json").write_text(original.encoded({"source_utf8":Path(__file__).read_text(),
                                                               "landmarks":landmarks,"prior_helper_hashes":{
            Path(module.__file__).relative_to(PROJECT).as_posix():original.digest(module.__file__) for module in (original,fit,previous)}}),encoding="utf-8")
    print(json.dumps({"unit":unit,"mode":mode,"seconds":receipt["seconds"],"receipt_sha256":original.digest(output/"receipt.json")}))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("unit",choices=original.UNITS)
    parser.add_argument("mode",choices=("contacts","cohort"))
    parser.add_argument("--label")
    args=parser.parse_args()
    run(args.unit,args.mode,args.label)
