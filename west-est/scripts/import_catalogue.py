#!/usr/bin/env python3
"""Import public WEST-EST catalogue and optimize authentic product imagery."""
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import unquote, quote, urlsplit, urlunsplit
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
import json, re, time, io, sys
from PIL import Image, ImageOps
BASE='https://westestminsk.by'
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; OUT=ROOT/'dist/assets/products'
RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
def fetch(url,timeout=60):
    url=urlunsplit((lambda p:(p.scheme,p.netloc,quote(unquote(p.path),safe='/%:@'),p.query,p.fragment))(urlsplit(url)))
    for attempt in range(2):
        try:
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=timeout) as r:
                return r.read(),dict(r.headers)
        except Exception:
            if attempt:raise
            time.sleep(0.2)
def jsonapi(path,name):
    b,h=fetch(BASE+path);(RAW/name).write_bytes(b)
    return json.loads(b),h
def plain(s):
    s=re.sub(r'<(?:br\s*/?|/p|/h[1-6]|/li|/div)>','\n',s,flags=re.I)
    s=re.sub(r'<[^>]*>','',s)
    return '\n'.join(' '.join(unescape(x).split()) for x in s.splitlines() if x.strip())
first=RAW/'products-page-1.json'
if first.exists():
    products=json.loads(first.read_text());h={}
else:
    products,h=jsonapi('/wp-json/wc/store/v1/products?per_page=100&page=1','products-page-1.json')
print('Page 1',len(products),h.get('X-WP-Total'),h.get('X-WP-TotalPages'),flush=True)
def get_page(i):return i,jsonapi(f'/wp-json/wc/store/v1/products?per_page=100&page={i}',f'products-page-{i}.json')[0]
with ThreadPoolExecutor(max_workers=4) as pool:
    tasks=[pool.submit(get_page,i) for i in [2,3,4]]
    for f in as_completed(tasks):
        try:
            i,ps=f.result();print('Page',i,len(ps),flush=True);products+=ps if isinstance(ps,list) else []
        except Exception as e:print('Page error',str(e),flush=True)
products=list({p['id']:p for p in products}.values())
print('Total products',len(products),flush=True)
json.dump(products,open(RAW/'products-all.json','w'),ensure_ascii=False,separators=(',',':'))
cat={}
for p in products:
    for c in p['categories']:
        if c['id'] not in cat:cat[c['id']]={'id':c['id'],'name':unescape(c['name']),'slug':unquote(c['slug']),'count':0,'sourceUrl':c['link']}
        cat[c['id']]['count']+=1
normalized=[]
for p in products:
    desc=plain(p.get('description',''));short=plain(p.get('short_description',''))
    brand=re.search(r'(?:Марка|Бренд|Производитель)\s*:\s*([^\n]+)',desc,re.I)
    imgs=[]
    srcs=[]
    for im in p.get('images',[]):
        if im['src'] in srcs:continue
        srcs.append(im['src']);imgs.append({'src':im['src'],'thumbnail':im.get('thumbnail',''),'local':f'assets/products/{p["id"]}-{len(imgs)}.webp','localLarge':f'assets/products/{p["id"]}-{len(imgs)}-large.webp','alt':im.get('alt','') or unescape(p['name'])})
    for m in re.findall(r'<img[^>]+src=[\"\']([^\"\']+)',p.get('short_description','')+p.get('description','')):
        m=m.replace('http://','https://')
        if m not in srcs:
            srcs.append(m);imgs.append({'src':m,'thumbnail':m,'local':f'assets/products/{p["id"]}-{len(imgs)}.webp','localLarge':f'assets/products/{p["id"]}-{len(imgs)}-large.webp','alt':unescape(p['name'])})
    normalized.append({'id':p['id'],'name':unescape(p['name']),'slug':unquote(p['slug']),'url':p['permalink'],'sku':p['sku'],'description':desc,'shortDescription':short,'images':imgs,'categories':[c['id'] for c in p['categories']],'brand':brand.group(1).strip() if brand else '', 'attributes':p.get('attributes',[]),'price':None if not p.get('price_html') else p['prices'],'priceHtml':p.get('price_html',''),'isInStock':p['is_in_stock'],'isPurchasable':p['is_purchasable'],'reviewCount':p['review_count'],'averageRating':p['average_rating']})
normalized.sort(key=lambda p:p['id'])
result={'source':BASE,'importedAt':'2026-11-04','categories':list(cat.values()),'products':normalized}
json.dump(result,open(ROOT/'data/catalogue.json','w'),ensure_ascii=False,separators=(',',':'))
print('Normalized saved',len(normalized),'categories',len(cat),flush=True)

def download(item):
    pid,idx,im=item
    small=ROOT/'dist'/im['local'];large=ROOT/'dist'/im['localLarge']
    if small.exists() and large.exists():return pid,idx,True,small.stat().st_size+large.stat().st_size,None
    try:
        b,_=fetch(im['src']); image=ImageOps.exif_transpose(Image.open(io.BytesIO(b)))
        if image.mode not in ['RGB','RGBA']:image=image.convert('RGB')
        if image.mode=='RGBA':
            back=Image.new('RGB',image.size,'white');back.paste(image,mask=image.getchannel('A'));image=back
        iw,ih=image.size
        # Preserve every real package: no generative editing, no potentially destructive cropping.
        a=image.copy();a.thumbnail((520,620),Image.Resampling.LANCZOS);a.save(small,'WEBP',quality=78,method=5)
        a=image.copy();a.thumbnail((1200,1400),Image.Resampling.LANCZOS);a.save(large,'WEBP',quality=84,method=5)
        return pid,idx,True,small.stat().st_size+large.stat().st_size,{'width':iw,'height':ih}
    except Exception as e:
        return pid,idx,False,0,str(e)
items=[(p['id'],i,im) for p in normalized for i,im in enumerate(p['images'])]
failed=[];total=0;done=0
with ThreadPoolExecutor(max_workers=10) as pool:
    fs=[pool.submit(download,x) for x in items]
    for f in as_completed(fs):
        pid,idx,ok,size,info=f.result();done+=1;total+=size
        if not ok:failed.append({'id':pid,'imageIndex':idx,'error':info});print('Image failed',pid,idx,info,flush=True)
        elif isinstance(info,dict):
            next(p for p in normalized if p['id']==pid)['images'][idx].update(info)
        if done%20==0:print('Images',done,'/',len(items),'bytes',total,flush=True)
json.dump(result,open(ROOT/'data/catalogue.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump({'products':len(products),'categories':len(cat),'images':len(items),'imagesFailed':failed,'optimizedImageBytes':total,'allNonPurchasable':all(not p['is_purchasable'] for p in products),'pricesShown':sum(bool(p['price_html']) for p in products)},open(ROOT/'data/import-report.json','w'),ensure_ascii=False,indent=2)
print('DONE',len(products),len(items),'failed',len(failed),'bytes',total,flush=True)
