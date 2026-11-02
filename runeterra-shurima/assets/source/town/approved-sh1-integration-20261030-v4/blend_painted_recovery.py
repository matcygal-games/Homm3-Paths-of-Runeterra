"""Standard gradient-domain raster composition of painted recovery sources.

All visible original pixels are fixed Dirichlet boundary values. Only native
architecture-owned recovery samples are solved; no shapes/scenery are drawn.
"""
from build_candidate import *
import numpy as np


def seamless(source,target,selection):
    box=selection.getbbox();left,top,right,bottom=box
    box=(max(0,left-1),max(0,top-1),min(800,right+1),min(374,bottom+1))
    src=np.asarray(source.convert("RGB").crop(box),dtype=float)
    dst=np.asarray(target.convert("RGB").crop(box),dtype=float)
    active=np.asarray(selection.crop(box))>0
    yy,xx=np.nonzero(active);n=len(xx)
    indexes=np.full(active.shape,-1,dtype=int);indexes[yy,xx]=np.arange(n)
    degree=np.zeros(n);rhs=np.zeros((n,3));neighbours=[]
    height,width=active.shape
    for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
        nx,ny=xx+dx,yy+dy;valid=(nx>=0)&(nx<width)&(ny>=0)&(ny<height)
        ids=np.nonzero(valid)[0];vx,vy=nx[valid],ny[valid]
        degree[ids]+=1
        rhs[ids]+=src[yy[valid],xx[valid]]-src[vy,vx]
        ni=indexes[vy,vx];inside=ni>=0
        neighbours.append((ids[inside],ni[inside]))
        rhs[ids[~inside]]+=dst[vy[~inside],vx[~inside]]
    def multiply(value):
        output=degree*value
        for ids,other in neighbours:output[ids]-=value[other]
        return output
    solved=[];proof=[]
    for channel in range(3):
        value=dst[yy,xx,channel].copy();residual=rhs[:,channel]-multiply(value)
        direction=residual/degree;rz=float(residual@direction)
        for iteration in range(4000):
            if float(np.max(np.abs(residual)))<1e-8:break
            ad=multiply(direction);alpha=rz/float(direction@ad)
            value+=alpha*direction;residual-=alpha*ad
            preconditioned=residual/degree;new_rz=float(residual@preconditioned)
            direction=preconditioned+(new_rz/rz)*direction;rz=new_rz
        solved.append(value)
        proof.append({"channel":channel,"iterations":iteration,"maximum_equation_residual":float(np.max(np.abs(residual)))})
    output=dst.copy();output[yy,xx]=np.clip(np.rint(np.stack(solved,axis=1)),0,255)
    result=target.convert("RGB");result.paste(Image.fromarray(output.astype("uint8")),box)
    return result,proof


def main():
    approved=Image.open(HERE/"approved-full-native.png").convert("RGB")
    removal=Image.open(HERE/"geometry/removal-mask.png").convert("L")
    recovery=Image.open(HERE/"empty-recovery-native.png").convert("RGB")
    background=Image.composite(recovery,approved,removal)
    sky_mask=Image.open(HERE/"geometry/sky-recovery-budget.png").convert("L")
    sky=approved.copy();sky.paste(Image.open(HERE/"sky-inpaint-native-crop-v2.png"),(70,0))
    # Keep the genuinely painted ridge/rocks at the bottom of the recovery;
    # the clean v4 sky supplies only the upper cloud region.
    sky.paste(Image.open(HERE/"sky-repair-raw-v4.png").resize((127,34),Image.Resampling.LANCZOS),(70,0))
    background,sky_proof=seamless(sky,background,sky_mask)
    pole_raw=Image.open(HERE/"civic-finial-removal-raw-v1.png")
    # Remove the generator's black left margin before whole-crop conversion.
    pole_native=pole_raw.crop((27,0,pole_raw.width,pole_raw.height)).resize((25,81),Image.Resampling.LANCZOS)
    save(HERE/"civic-finial-removal-native-crop-v1.png",pole_native)
    pole_source=background.copy();pole_source.paste(pole_native,(443,36))
    pole_mask=ImageChops.multiply(Image.open(HERE/"geometry/capitol-body.png").convert("L"),mask([(443,36),(467,36),(467,116),(443,116)]))
    save(HERE/"geometry/civic-finial-recovery-budget.png",pole_mask)
    background,pole_proof=seamless(pole_source,background,pole_mask)
    skyline_proofs={}
    for name in ("solar-spire","guild-crown"):
        selected=Image.open(HERE/"geometry"/(name+"-recovery-budget.png")).convert("L")
        background,proof=seamless(recovery,background,selected)
        skyline_proofs[name]={"mask":ref(HERE/"geometry"/(name+"-recovery-budget.png")),"source":ref(HERE/"empty-recovery-native.png"),"solve":proof}
    save(HERE/"painted-recovery-seamless-native-v5.png",background)
    dump(HERE/"painted-recovery-seamless-conversion-v5.json",{
        "status":"authored configuration","method":"Standard Poisson/gradient-domain composition of genuinely painted imagegen sources; four-neighbour native Laplacian, fixed original/background values outside architecture-owned masks; RGB8 round-and-clip.",
        "producer":ref(HERE/"blend_painted_recovery.py"),"numpy_version":np.__version__,
        "painted_sources":[ref(HERE/"sky-inpaint-native-crop-v2.png"),ref(HERE/"sky-repair-raw-v4.png"),ref(HERE/"civic-finial-removal-raw-v1.png")],
        "source_transforms":{"sky_v2":"Preserve painted ridge: paste126x56at70,0","sky_v4":"Whole clean generated cloud painting Lanczos127x34, paste70,0 above the painted ridge","pole":"Crop generator black margin (27,0,width,height), whole remaining image Lanczos25x81, paste443,36"},
        "sky_mask":ref(HERE/"geometry/sky-recovery-budget.png"),"pole_mask":ref(HERE/"geometry/civic-finial-recovery-budget.png"),
        "solves":{"sky":sky_proof,"pole":pole_proof},"new_skyline_recoveries":skyline_proofs,"output":ref(HERE/"painted-recovery-seamless-native-v5.png"),
        "outside_recovery_mask_changes":ImageChops.multiply(union(ImageChops.difference(background,approved).split()).point(lambda p:255 if p else 0),ImageChops.invert(removal)).getbbox(),
        "visual_approval_granted":False})
    return background


if __name__=="__main__":main()
