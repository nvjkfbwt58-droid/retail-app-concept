#!/usr/bin/env python3
"""Reproduce optimized media from the checked-in, fixed public catalogue snapshot."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit,urlunsplit,quote,unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageOps
import io,json,time

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/catalogue.json').read_text())
ASSETS=ROOT/'dist/assets'
def download(url):
    parsed=urlsplit(url)
    url=urlunsplit((parsed.scheme,parsed.netloc,quote(unquote(parsed.path),safe='/%:@'),parsed.query,parsed.fragment))
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'WEST-EST catalogue build / public assets'}),timeout=60) as r:return r.read()
        except Exception:
            if attempt==2:raise
            time.sleep(attempt+1)
def product(job):
    src,small,large=job
    if (ROOT/'dist'/small).exists() and (ROOT/'dist'/large).exists():return
    image=ImageOps.exif_transpose(Image.open(io.BytesIO(download(src)))).convert('RGB')
    for dest,size,quality in [(small,520,82),(large,1200,88)]:
        im=image.copy();im.thumbnail((size,size),Image.Resampling.LANCZOS)
        path=ROOT/'dist'/dest;path.parent.mkdir(parents=True,exist_ok=True);im.save(path,'WEBP',quality=quality,method=6)
def main():
    jobs={i['local']:(i['src'],i['local'],i['localLarge']) for p in DATA['products'] for i in p['images']}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(product,job) for job in jobs.values()]
        for n,future in enumerate(as_completed(futures),1):
            future.result()
            if n%40==0:print('Product media',n,'/',len(jobs),flush=True)
    categories=json.loads((ROOT/'data/category-images.json').read_text())
    if isinstance(categories,list):categories={str(c['id']):c.get('imageSource') for c in categories}
    for c in DATA['categories']:
        if not c.get('image'):continue
        path=ROOT/'dist'/c['image']
        if path.exists():continue
        source=categories.get(str(c['id'])) if isinstance(categories,dict) else None
        if isinstance(source,dict):source=source.get('src') or source.get('url')
        if not source:raise ValueError('Missing category source '+str(c['id']))
        im=ImageOps.exif_transpose(Image.open(io.BytesIO(download(source)))).convert('RGB');im.thumbnail((1000,1000),Image.Resampling.LANCZOS)
        path.parent.mkdir(parents=True,exist_ok=True);im.save(path,'WEBP',quality=84,method=6)
    hero=Image.open(ASSETS/'hero-1600.webp').convert('RGB')
    if not (ASSETS/'story-900.webp').exists():
        hero.resize((900,round(hero.height*900/hero.width)),Image.Resampling.LANCZOS).save(ASSETS/'story-900.webp','WEBP',quality=82,method=6)
    if not (ASSETS/'og.jpg').exists():
        hero.resize((1200,round(hero.height*1200/hero.width)),Image.Resampling.LANCZOS).save(ASSETS/'og.jpg','JPEG',quality=85,optimize=True)
    print('Media ready:',len(jobs),'product images; complete catalogue snapshot retained.',flush=True)
if __name__=='__main__':main()
