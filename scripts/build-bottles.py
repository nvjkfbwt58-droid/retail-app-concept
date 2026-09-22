"""Build self-contained product SVGs: no runtime label requests or layout layers."""
from pathlib import Path
import json,base64,html
root=Path(__file__).resolve().parents[1]
assets=root/'dist/assets'
products=json.loads((root/'dist/flanders.js').read_text().split('const FLANDERS_PRODUCTS=')[1].rstrip(';\n'))
def data(name):
 return 'data:image/png;base64,'+base64.b64encode((Path('/tmp/retail-bottle-sources')/(name+'.png')).read_bytes()).decode()
for p in products:
 if p['line']=='Пивные напитки':continue
 label=p['image'] if p['poster'] else p['image'].replace('flanders-medal-','label-')
 art=f'<image href="{data(label)}" x="8" y="355" width="139" height="160" preserveAspectRatio="xMidYMid slice"/>' if p['poster'] else f'<image href="{data(label)}" x="12" y="360" width="131" height="139" preserveAspectRatio="xMidYMid meet"/><text x="77.5" y="516" text-anchor="middle" font-family="sans-serif" font-size="9" font-weight="700" fill="#624825">{html.escape(p["abv"])}</text>'
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="155" height="600" viewBox="0 0 155 600">
<defs><linearGradient id="paper"><stop stop-color="#bba976"/><stop offset=".24" stop-color="#f5e7bc"/><stop offset=".53" stop-color="#fff0c8"/><stop offset=".8" stop-color="#e0d1a3"/><stop offset="1" stop-color="#9e8b58"/></linearGradient><linearGradient id="neck"><stop stop-color="#182e21"/><stop offset=".45" stop-color="#3f5942"/><stop offset="1" stop-color="#182c20"/></linearGradient><linearGradient id="curve"><stop stop-color="#392000" stop-opacity=".3"/><stop offset=".25" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".14"/><stop offset=".72" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#392000" stop-opacity=".34"/></linearGradient><clipPath id="label"><path d="M8 354 Q77 364 147 354 L147 520 Q77 533 8 520Z"/></clipPath></defs>
<image href="{data('bottle-blank.webp')}" width="155" height="600"/>
<path d="M48 125 Q77 129 107 125 L110 152 Q78 158 45 152Z" fill="url(#neck)" stroke="#b29d69" stroke-width=".8"/>
<text x="77.5" y="144" text-anchor="middle" font-family="serif" font-size="7" letter-spacing=".7" fill="#ead29a">FLANDERS</text>
<g clip-path="url(#label)"><path d="M8 354H147V533H8Z" fill="url(#paper)"/>{art}<path d="M8 354H147V533H8Z" fill="url(#curve)"/></g>
<path d="M8 354 Q77 364 147 354 M8 520 Q77 533 147 520" stroke="#8d713b" stroke-opacity=".4" fill="none"/>
</svg>'''
 (assets/(p['id']+'-bottle.svg')).write_text(svg)
print('Built',len(list(assets.glob('*-bottle.svg'))),'bottles;',sum(p.stat().st_size for p in assets.glob('*-bottle.svg')),'bytes')
