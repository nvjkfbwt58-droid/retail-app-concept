from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import unquote,quote,urlsplit,urlunsplit
from concurrent.futures import ThreadPoolExecutor,as_completed
from PIL import Image,ImageOps
import json,io,re
ROOT=Path('/workspace/sites/west-est');RAW=ROOT/'data/raw';OUT=ROOT/'dist/assets/categories';OUT.mkdir(parents=True,exist_ok=True)
def get(u):
 p=urlsplit(u);u=urlunsplit((p.scheme,p.netloc,quote(unquote(p.path),safe='/%:@'),p.query,p.fragment))
 with urlopen(Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=60)as r:return r.read()
cats=json.loads((RAW/'store-categories.json').read_text());report=[]
def catimg(c):
 if not c.get('image'):return c['id'],None
 b=get(c['image']['src']);im=ImageOps.exif_transpose(Image.open(io.BytesIO(b))).convert('RGB');w,h=im.size;im.thumbnail((1000,1100),Image.Resampling.LANCZOS);im.save(OUT/f'{c["id"]}.webp','WEBP',quality=84,method=5)
 return c['id'],{'image':f'assets/categories/{c["id"]}.webp','imageSource':c['image']['src'],'imageWidth':w,'imageHeight':h}
with ThreadPoolExecutor(max_workers=5)as p:
 for f in as_completed([p.submit(catimg,c)for c in cats]):
  try:k,x=f.result();report.append({'id':k,**(x or {})});print('category image',k,flush=True)
  except Exception as e:print('category image failed',e,flush=True)
json.dump(report,open(ROOT/'data/category-images.json','w'),ensure_ascii=False,separators=(',',':'))
def meta(page):
 path=RAW/f'wp-product-meta-{page}.json'
 if page==1: data=json.loads((RAW/'wp-product-meta.json').read_text())
 else:
  b=get(f'https://westestminsk.by/wp-json/wp/v2/product?per_page=100&page={page}&_fields=id,date,modified,menu_order,link,title');path.write_bytes(b);data=json.loads(b)
 return data
metadata=[]
with ThreadPoolExecutor(max_workers=3)as p:
 for f in as_completed([p.submit(meta,k)for k in [1,2,3]]):metadata+=f.result()
json.dump(metadata,open(ROOT/'data/product-dates.json','w'),ensure_ascii=False,separators=(',',':'))
print('Downloaded category photos',len(report),'dates',len(metadata),flush=True)
# Atomically merge authentic taxonomy photos, default category aliases and dates.
from datetime import datetime,timezone
catalogue=json.loads((ROOT/'data/catalogue.json').read_text())
photos={x['id']:x for x in report}
sourcecats={x['id']:x for x in cats}
oldorder=[183,186,184,182,16,150,154,152,156,151,157,153,185,188]
existing={x['id']:x for x in catalogue['categories']}
if 16 not in existing:
 existing[16]={'id':16,'name':'Uncategorized','slug':'uncategorized','count':4,'sourceUrl':'https://westestminsk.by/product-category/uncategorized/'}
catalogue['categories']=[existing[k]for k in oldorder]
for c in catalogue['categories']:
 c.update({k:v for k,v in photos.get(c['id'],{}).items()if k!='id'})
 c['sourceCount']=sourcecats[c['id']]['count']
 c['image']=c.get('image','')
dates={x['id']:x for x in metadata}
apiorder=[]
for k in [1,2,3]:apiorder+=json.loads((RAW/f'products-page-{k}.json').read_text())
order={x['id']:i for i,x in enumerate(apiorder)}
for p in catalogue['products']:
 if p['id']in [38807,38805,38896,38898]and 16 not in p['categories']:p['categories'].append(16)
 if p['id']in dates:
  p['date']=dates[p['id']]['date'];p['modified']=dates[p['id']]['modified']
 p['sourceOrder']=order[p['id']]
tmp=ROOT/'data/catalogue.json.tmp';tmp.write_text(json.dumps(catalogue,ensure_ascii=False,separators=(',',':')));tmp.replace(ROOT/'data/catalogue.json')
print('Final catalogue saved',len(catalogue['products']),len(catalogue['categories']),flush=True)
