#!/usr/bin/env python3
"""Validate every generated internal link, asset, catalogue route and media file."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist'
data=json.loads((ROOT/'data/catalogue.json').read_text());errors=[]
presentation=json.loads((ROOT/'data/product-presentation.json').read_text())['images']
class Check(HTMLParser):
    def __init__(self,path):super().__init__();self.path=path;self.h1=0
    def handle_starttag(self,tag,attributes):
        attrs=dict(attributes)
        if tag=='h1':self.h1+=1
        for key in ('href','src'):
            value=attrs.get(key,'');url=urlsplit(value)
            if not value or value.startswith('#') or url.scheme or url.netloc:continue
            target=(self.path.parent/unquote(url.path)).resolve()
            if not target.exists():errors.append((str(self.path.relative_to(OUT)),key,value))
        if tag=='img' and not ('width' in attrs and 'height' in attrs) and attrs.get('id')!='zoom-image':errors.append((str(self.path),'image dimensions',attrs.get('src')))
for path in OUT.rglob('*.html'):
    if '_qa' in path.parts:continue
    parser=Check(path);parser.feed(path.read_text())
    if parser.h1!=1:errors.append((str(path.relative_to(OUT)),'h1 count',parser.h1))
assert len(data['products'])==205 and len({p['id'] for p in data['products']})==205
for product in data['products']:
    assert (OUT/'product'/product['slug']/'index.html').is_file(),product['slug']
    for image in product['images']:
        assert image['local'] in presentation,('Missing original-photo presentation',image['local'])
        assert '--media-clip:polygon(' in presentation[image['local']]['style'],image['local']
        for key in ('local','localLarge'):assert (OUT/image[key]).is_file(),image[key]
for category in data['categories']:
    assert (OUT/'product-category'/category['slug']/'index.html').is_file(),category['slug']
if errors:raise SystemExit(json.dumps(errors[:30],ensure_ascii=False))
assert (OUT/'assets/italy-pencil-v2.webp').is_file()
report={'products':205,'categories':len(data['categories']),'contentPages':sum(1 for p in OUT.rglob('index.html') if '_qa' not in p.parts and '404' not in p.parts),'brokenLocalReferences':0,'validation':'passed'}
print(json.dumps(report,ensure_ascii=False))
