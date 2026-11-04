#!/usr/bin/env python3
"""Analyze original packshots into non-destructive CSS clipping and placement.

This script never rewrites a raster source. The browser clips the original
photograph using a static polygon; all product pixels and labels stay original.
Analysis dependencies (build-time only): rembg[cpu], opencv-python-headless,
scipy, numpy, Pillow. The published website needs none of these packages.
"""
from pathlib import Path
import os,json,argparse
os.environ.setdefault('OMP_NUM_THREADS','2')
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
from rembg import new_session

ROOT=Path(__file__).resolve().parents[1]
QA=Path(os.environ.get('WEST_EST_QA_DIR',str(ROOT/'tmp/product-qa')))

def segments(image,session,force_white=False):
    probability=np.array(session.predict(image)[0])
    foreground=probability>105
    foreground=ndimage.binary_closing(foreground,iterations=1)
    labels,n=ndimage.label(foreground)
    h,w=foreground.shape
    components=[]
    for k in range(1,n+1):
        ys,xs=np.where(labels==k)
        if len(xs)<max(25,h*w*.0012):continue
        x,y,bw,bh=int(xs.min()),int(ys.min()),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)
        edge_count=sum([x<=2,y<=2,x+bw>=w-2,y+bh>=h-2])
        fill=len(xs)/(bw*bh)
        # Scan/phone-photo border strips are not the product.
        border_strip=(edge_count>=2 and (bw<w*.17 or bh<h*.12))
        if border_strip:continue
        score=len(xs)*(1-.40*abs((xs.mean()/w)-.5)-.25*abs((ys.mean()/h)-.5))
        components.append((score,k,(x,y,bw,bh),len(xs),edge_count,fill))
    if not components:return np.ones_like(foreground,dtype=bool),['no confident silhouette']
    components.sort(reverse=True)
    score,k,box,area,edges,fill=components[0]
    mask=labels==k
    # Preserve additional food slices or the other packs in source group shots.
    x,y,bw,bh=box
    for _,other,bbox,count,edge_count,_ in components[1:]:
        ox,oy,ow,oh=bbox
        distance=max(0,max(x-ox-ow,ox-x-bw,y-oy-oh,oy-y-bh))
        if count>=area*.018 and distance<max(w,h)*.25 and edge_count<2:
            mask|=labels==other
    # A retail box may show a food photograph: generic saliency can select only
    # the food/logo printed on the box and miss the actual packaging. For true
    # white-background packshots preserve the entire connected physical object.
    rgb=np.array(image.convert('RGB'),dtype=np.int16)
    perimeter=np.concatenate([rgb[:3].reshape(-1,3),rgb[-3:].reshape(-1,3),rgb[:,:3].reshape(-1,3),rgb[:,-3:].reshape(-1,3)])
    white_fraction=(perimeter.min(axis=1)>239).mean()
    if white_fraction>.70 or force_white:
        ink=rgb.min(axis=2)<235
        ink=ndimage.binary_closing(ink,iterations=1)
        color_labels,nc=ndimage.label(ink)
        expanded=ndimage.binary_dilation(mask,iterations=3)
        sizes=np.bincount(color_labels.ravel(),minlength=nc+1)
        allowed=np.zeros(nc+1,dtype=bool);allowed[np.unique(color_labels[expanded])]=True
        allowed&=sizes>=max(30,h*w*.0004);allowed[0]=False
        for ck in np.flatnonzero(allowed&(sizes>h*w*.8)):
            cy,cx=np.where(color_labels==ck)
            # A residual photo border/background is not a retail package.
            if not force_white and (cx.max()-cx.min())>w*.97 and (cy.max()-cy.min())>h*.97:allowed[ck]=False
        mask|=allowed[color_labels]
    mask=ndimage.binary_fill_holes(mask)
    mask=ndimage.binary_dilation(mask,iterations=1)
    notes=[]
    if mask.mean()<.008:notes.append('very small foreground')
    ys,xs=np.where(mask)
    if (xs.max()-xs.min())>w*.97 and (ys.max()-ys.min())>h*.97:notes.append('silhouette nearly full frame')
    return mask,notes

def polygon(mask):
    h,w=mask.shape
    contours,_=cv2.findContours(mask.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    contours=sorted(contours,key=cv2.contourArea,reverse=True)
    contours=[c for c in contours if cv2.contourArea(c)>max(20,w*h*.0006)]
    paths=[]
    epsilon=max(w,h)*.003
    # Keep the actual silhouette but avoid hundreds of noisy contour vertices.
    for attempt in range(10):
        paths=[]
        for contour in contours:
            approx=cv2.approxPolyDP(contour,epsilon,True).reshape(-1,2)
            if len(approx)>=3:paths.append([(float(x)/w*100,float(y)/h*100) for x,y in approx])
        if sum(len(p)+3 for p in paths)<=110:break
        epsilon*=1.3
    if not paths:return 'polygon(0% 0%,100% 0%,100% 100%,0% 100%)'
    # Even-odd closed sub-polygons are connected with a zero-area retraced bridge.
    points=[];origin=paths[0][0]
    for path in paths:
        if points:points.append(origin)
        points.extend(path+[path[0]])
        points.append(origin)
    return 'polygon(evenodd, '+','.join(f'{x:.2f}% {y:.2f}%' for x,y in points)+')'

def record(image,mask,clip,notes):
    ys,xs=np.where(mask);h,w=mask.shape
    x,y,bw,bh=int(xs.min()),int(ys.min()),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)
    scale=min(76/bw,74/bh)
    values={'x':round(50-(x+bw/2)*scale,4),'y':round(86-(y+bh)*scale,4),'w':round(w*scale,4),'h':round(h*scale,4)}
    style=';'.join(f'--media-{k}:{value:g}%' for k,value in values.items())+';--media-clip:'+clip
    return {'width':image.width,'height':image.height,'bbox':[x,y,bw,bh],**values,'style':style,'confidence':'review' if notes else 'good','notes':notes}

def preview(image,mask,info,canvas=150):
    # QA surrogate only: renders exactly the same clipping/position as CSS.
    bg=Image.new('RGB',(canvas,canvas),'#eeeae1')
    draw=ImageDraw.Draw(bg);draw.ellipse((canvas*.27,canvas*.84,canvas*.73,canvas*.87),fill='#dcd7cc')
    image=image.convert('RGBA');image.putalpha(Image.fromarray(mask.astype('uint8')*255))
    size=(max(1,round(info['w']/100*canvas)),max(1,round(info['h']/100*canvas)))
    image=image.resize(size,Image.Resampling.LANCZOS)
    bg.paste(image,(round(info['x']/100*canvas),round(info['y']/100*canvas)),image)
    return bg

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ids',default='');parser.add_argument('--qa',action='store_true');args=parser.parse_args()
    data=json.loads((ROOT/'data/catalogue.json').read_text())
    session=new_session('u2netp')
    entries={};previews=[];review=[]
    wanted={int(s) for s in args.ids.split(',') if s}
    for p in data['products']:
        if wanted and p['id'] not in wanted:continue
        for number,media in enumerate(p['images']):
            image=Image.open(ROOT/'dist'/media['local']).convert('RGB')
            # This source packshot is tightly cropped to a blue retail box;
            # fewer than half of its perimeter pixels are background white.
            mask,notes=segments(image,session,force_white=p['id'] in {38870});clip=polygon(mask)
            info=record(image,mask,clip,notes)
            info['productId']=p['id'];info['imageIndex']=number
            entries[media['local']]=info
            if notes:review.append({'productId':p['id'],'path':media['local'],'notes':notes})
            if args.qa:
                cell=preview(image,mask,info,150)
                canvas=Image.new('RGB',(150,175),'#f3efe6');canvas.paste(cell,(0,0));ImageDraw.Draw(canvas).text((7,154),str(p['id'])+' / '+str(number),fill='#242c24');previews.append(canvas)
            if len(entries)%40==0:print('Analyzed',len(entries),'media entries',flush=True)
    output={'version':1,'canvas':{'shape':'square','widthLimit':76,'heightLimit':74,'baseline':86},'images':entries,'review':review,'missingImageProducts':[p['id'] for p in data['products'] if not p['images']]}
    dest=ROOT/'data/product-presentation.json' if not wanted else QA/'sample-metadata.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')))
    if args.qa:
        QA.mkdir(parents=True,exist_ok=True)
        for group,start in enumerate(range(0,len(previews),36)):
            sheet=Image.new('RGB',(900,1050),'#f3efe6')
            for j,cell in enumerate(previews[start:start+36]):sheet.paste(cell,((j%6)*150,(j//6)*175))
            sheet.save(QA/f'{"sample" if wanted else "normalized"}-{group}.jpg')
    print(json.dumps({'records':len(entries),'media':len(entries),'review':review,'file':str(dest),'bytes':dest.stat().st_size}),flush=True)
if __name__=='__main__':main()
