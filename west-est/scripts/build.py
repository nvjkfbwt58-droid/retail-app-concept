#!/usr/bin/env python3
"""Build every public route as plain HTML. No frontend framework or build dependencies."""
from pathlib import Path
import json, re, html, shutil
from urllib.parse import quote
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
DATA=json.loads((ROOT/'data/catalogue.json').read_text())
PRODUCTS=DATA['products']; CATEGORIES=DATA['categories']
SITE='https://nvjkfbwt58-droid.github.io/retail-app-concept/west-est/'
TG='https://telegram.me/westestminsk'
EMAIL='westest.minsk@gmail.com'
SHORT={186:'Сыры',151:'Оливковое масло',154:'Паста, рис и ньокки',152:'Молочные продукты и яйца',157:'Кофе и сладости',156:'Мясные деликатесы',150:'Овощи и консервация',153:'Бальзамический уксус',188:'Соль и сахар',16:'Другие продукты'}
CATS={c['id']:c for c in CATEGORIES}
for c in CATEGORIES:c['displayName']=SHORT.get(c['id'],c['name'])
# Source titles contain verified article/brand information absent in some API fields.
known_brands=['Granoro','Masiello','Lovascio','De Nigris','Trevalli','Molisana']
for p in PRODUCTS:
    if not p['sku']:
        m=re.match(r'^(?:Арт\.?\s*)?(\d{3,6})\b',p['name'],re.I)
        if m:p['sku']=m.group(1)
    if not p['brand']:
        p['brand']=next((b for b in known_brands if b.casefold() in p['name'].casefold()),'')

def e(s):return html.escape(str(s or ''),quote=True)
def path_product(p):return 'product/'+p['slug']+'/'
def path_category(c):return 'product-category/'+c['slug']+'/'
def href(prefix,path):return prefix+quote(path,safe='/?=&-_.~')
def name(p):return re.sub(r'^(?:Арт\.?\s*)?\d{3,6}\s*[:.\-]?\s*','',p['name'],flags=re.I).strip()
def count_word(n):return 'товар' if n%10==1 and n%100!=11 else 'товара' if n%10 in [2,3,4] and not 12<=n%100<=14 else 'товаров'
def icon(kind='arrow'):
    paths={'arrow':'<path d="M5 12h14m-6-6 6 6-6 6"/>','diagonal':'<path d="M6 18 18 6M6 6h12v12"/>','search':'<circle cx="10.5" cy="10.5" r="6.7"/><path d="m16 16 5 5"/>','menu':'<path d="M4 8h16M4 16h16"/>','close':'<path d="m6 6 12 12M6 18 18 6"/>','plus':'<path d="M5 12h14M12 5v14"/>','chat':'<path d="M20 11.5a8 8 0 0 1-8 8H5l-3 2v-10a9 9 0 0 1 18 0Z"/><path d="M7 10h8M7 14h5"/>','pin':'<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2"/>','grid':'<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>','list':'<path d="M4 5h16M4 12h16M4 19h16"/>'}
    return '<svg class="icon'+(' arrow' if kind in ('arrow','diagonal') else '')+'" viewBox="0 0 24 24" aria-hidden="true">'+paths.get(kind,paths['arrow'])+'</svg>'
def wordmark(prefix):return f'<a class="wordmark" href="{prefix}" aria-label="WEST-EST, главная">WEST-EST<span class="tricolore" aria-hidden="true"><i></i><i></i><i></i></span></a>'
def link(prefix,path,label,cls='text-link'):return f'<a class="{cls}" href="{href(prefix,path)}">{label} {icon()}</a>'
def header(prefix,page):
    nav=''.join(f'<a href="{href(prefix,p)}"'+(' aria-current="page"' if page==key else '')+f'>{label}</a>' for p,label,key in [('shop/','Каталог','catalog'),('producers/','Производители','producers'),('business/','Для бизнеса','business'),('contact/','Контакты','contact')])
    return f'<a class="skip-link" href="#main">К содержимому</a><header class="site-header"><div class="wrap header-inner">{wordmark(prefix)}<nav class="header-nav" id="main-nav" data-mobile-menu aria-label="Основная навигация">{nav}</nav><div class="header-actions"><button class="search-toggle" data-open-search aria-label="Открыть поиск">{icon("search")}<span>Поиск</span></button><button class="menu-toggle" data-menu-toggle aria-label="Открыть меню" aria-expanded="false" aria-controls="main-nav">{icon("menu")}<span>Меню</span></button></div></div></header>'
def footer(prefix):
    return f'''<footer class="site-footer"><div class="wrap"><div class="footer-top"><div class="footer-brand">{wordmark(prefix)}<p>Продукты с характером.<br>Итальянский вкус в Минске.</p></div><div class="footer-col"><h3>Коллекция</h3><a href="{href(prefix,'shop/')}">Весь каталог</a><a href="{href(prefix,path_category(CATS[186]))}">Сыры</a><a href="{href(prefix,path_category(CATS[151]))}">Оливковое масло</a><a href="{href(prefix,path_category(CATS[154]))}">Паста и рис</a></div><div class="footer-col"><h3>WEST-EST</h3><a href="{href(prefix,'producers/')}">Производители</a><a href="{href(prefix,'business/')}">Для бизнеса</a><a href="{href(prefix,'contact/')}">Контакты</a><a href="{TG}" target="_blank" rel="noopener">Написать в Telegram ↗</a></div><div class="footer-col"><h3>Всегда на связи</h3><a href="tel:+375296500536">+375 (29) 650-05-36</a><a href="mailto:{EMAIL}">{EMAIL}</a><p>Офис: Минск, ул. Киселёва, 12<br>Склад: Минск, ул. Красная, 7</p><p>Пн–пт, 09:00–17:00</p></div></div><div class="footer-bottom"><span>© {date.today().year} WEST-EST</span><span>Продукты из Италии · Минск, Беларусь</span><span>Хороший вкус начинается с продукта.</span></div></div></footer><a class="manager-link" href="{TG}" target="_blank" rel="noopener" aria-label="Чат с менеджером WEST-EST в Telegram">{icon('chat')}<span>Чат с менеджером</span></a><nav class="mobile-dock" aria-label="Быстрые действия"><a href="{href(prefix,'shop/')}">{icon('grid')}<span>Каталог</span></a><button data-open-search aria-label="Открыть поиск по товарам">{icon('search')}<span>Поиск</span></button><a href="{TG}" target="_blank" rel="noopener">{icon('chat')}<span>Менеджер ↗</span></a></nav>'''
def dialogs(prefix):
    options=''.join(f'<option value="{c["id"]}">{e(c["displayName"])}</option>' for c in CATEGORIES)
    close=f'<button class="round-button dialog-close" data-close aria-label="Закрыть">{icon("close")}</button>'
    return f'''<dialog class="search-dialog" id="search-dialog" aria-labelledby="search-title">{close}<h2 id="search-title">Найти свой продукт</h2><form class="search-form" id="global-search-form" action="{href(prefix,'shop/')}" role="search">{icon('search')}<input id="global-search" name="q" type="search" placeholder="Название, марка или артикул" autocomplete="off" aria-label="Поиск по каталогу"><button type="submit" aria-label="Показать результаты поиска">{icon()}</button></form><label class="search-category" for="search-category">Категория<select id="search-category" name="category"><option value="">Все категории</option>{options}</select></label><div class="search-results" id="search-results" aria-live="polite"><p class="search-hint">Например: Granoro, оливковое масло или артикул товара.</p></div></dialog><dialog class="quick-dialog" id="quick-dialog" aria-labelledby="quick-title">{close}<div id="quick-content"></div></dialog><dialog class="image-dialog" id="image-dialog" aria-label="Фотография продукта в полном размере">{close}<img id="zoom-image" alt="" width="1000" height="1000"></dialog>'''
def page(path,title,content,page_type='content',category=0,list_page=1,description='',hero=False):
    folder=OUT/path;folder.mkdir(parents=True,exist_ok=True)
    depth=len([x for x in str(path).split('/') if x and x!='.']);prefix='../'*depth or './'
    body=content(prefix) if callable(content) else content
    desc=description or title+' · WEST-EST. Каталог продуктов, характеристики и связь с менеджером. Минск, Беларусь.'
    preload=f'<link rel="preload" as="image" href="{prefix}assets/hero-1600.webp" imagesrcset="{prefix}assets/hero-960.webp 960w, {prefix}assets/hero-1600.webp 1600w" imagesizes="100vw">' if hero else ''
    canonical=SITE+quote(str(path).strip('./')+'/' if path else '',safe='/')
    schema={'@context':'https://schema.org','@type':'Organization','name':'WEST-EST','url':SITE,'telephone':'+375296500536','email':EMAIL,'address':{'@type':'PostalAddress','addressLocality':'Минск','streetAddress':'ул. Киселёва, 12','addressCountry':'BY'}}
    if page_type=='product':
        p=next((p for p in PRODUCTS if path_product(p).strip('/')==path.strip('/')),None)
        if p:schema={'@context':'https://schema.org','@type':'Product','name':p['name'],'sku':p['sku'] or str(p['id']),'description':p['description'] or p['name'],'image':[SITE+i['localLarge'] for i in p['images']],'url':canonical}
    schema_json=json.dumps(schema,ensure_ascii=False).replace('</','<\\/')
    text=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="theme-color" content="#f3efe6"><title>{e(title)} | WEST-EST</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:title" content="{e(title)} | WEST-EST"><meta property="og:description" content="{e(desc)}"><meta property="og:image" content="{SITE}assets/og.jpg"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">{preload}<link rel="preload" href="{prefix}assets/fonts/prata.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="{prefix}assets/styles.css"><script type="application/ld+json">{schema_json}</script><script src="{prefix}assets/app.js" defer></script></head><body data-page="{page_type}" data-category="{category}" data-list-page="{list_page}">{header(prefix,page_type)}<main id="main">{body}</main>{footer(prefix)}{dialogs(prefix)}</body></html>'''
    (folder/'index.html').write_text(text)

def card(p,prefix):
    title=name(p);image=p['images'][0]['local'] if p['images'] else 'assets/placeholder.svg'
    return f'''<article class="product-card"><div class="product-visual"><a href="{href(prefix,path_product(p))}" tabindex="-1" aria-hidden="true"><img src="{prefix}{image}" alt="{e(title)}" width="520" height="572" loading="lazy" decoding="async"></a><button class="quick-view" data-quick="{p['id']}" aria-label="Быстрый просмотр: {e(title)}">{icon('plus')}</button></div><div class="product-info"><span class="product-brand">{e(p['brand'] or 'WEST-EST')}</span><h3><a href="{href(prefix,path_product(p))}">{e(title)}</a></h3><div class="product-meta"><span>{'Арт. '+e(p['sku']) if p['sku'] else 'WEST-EST'}</span><span>{'Уточнить цену' if p['isInStock'] else 'Под заказ'}</span></div></div></article>'''
def breadcrumbs(prefix,items):return '<nav class="breadcrumbs" aria-label="Навигационная цепочка"><a href="'+prefix+'">Главная</a>'+''.join(' <span aria-hidden="true">/</span> '+(f'<a href="{href(prefix,p)}">{e(n)}</a>' if p else f'<span aria-current="page">{e(n)}</span>') for p,n in items)+'</nav>'
def cat_tile(c,prefix,index):
    img=c.get('image') or next((p['images'][0]['local'] for p in PRODUCTS if c['id'] in p['categories'] and p['images']),'assets/placeholder.svg')
    return f'<a class="category-tile" href="{href(prefix,path_category(c))}"><div class="tile-top"><h3><span class="small">{index:02d} / </span>{e(c["displayName"])}</h3>{icon("diagonal")}</div><div class="tile-image"><img src="{prefix}{img}" alt="{e(c["displayName"])}" width="520" height="390" loading="lazy" decoding="async"></div><span class="tile-caption">{c["count"]} {count_word(c["count"])}</span></a>'
def business_cta(prefix):return f'<section class="wrap business-cta"><div><p class="eyebrow">ДЛЯ ВАШЕГО БИЗНЕСА</p><h2>Хороший продукт.<br>Начало хорошего дела.</h2></div><div><p class="muted">Подберём продукты для вашей кухни или ассортимента магазина. Обсудим фасовку, наличие и условия поставки.</p>{link(prefix,"business/","Обсудить сотрудничество","btn btn-outline")}</div></section>'
def home(prefix):
    featured=[]
    for term in ['5246','1124','1006','4024']:
        p=next((p for p in PRODUCTS if p['sku']==term or term in p['name']),None)
        if p:featured.append(p)
    if len(featured)<4:featured=PRODUCTS[:4]
    more=''.join(f'<a href="{href(prefix,path_category(c))}">{e(c["displayName"])}<sup>{c["count"]}</sup></a>' for c in CATEGORIES if c['id'] not in [186,151,154,16])
    brandlinks=''.join(f'<a href="{href(prefix,"shop/")}?brand={quote(b)}">{b}</a>' for b in ['Granoro','Masiello','Lovascio','De Nigris','Trevalli'])
    return f'''<section class="hero" aria-labelledby="hero-title"><picture class="hero-picture"><source type="image/webp" srcset="{prefix}assets/hero-960.webp 960w, {prefix}assets/hero-1600.webp 1600w" sizes="100vw"><img src="{prefix}assets/hero-1600.webp" alt="Оливковое масло, сыр и паста на тёплом камне" width="1672" height="941" fetchpriority="high"></picture><div class="hero-content"><p class="eyebrow">ПРОДУКТЫ ИЗ ИТАЛИИ</p><h1 id="hero-title">Вкус начинается<br>с происхождения.</h1><p class="hero-copy">Паста, оливковое масло, томаты и деликатесы.<br>Продукты, которые говорят сами за себя.</p><div class="button-row">{link(prefix,'shop/','Открыть каталог','btn')}{link(prefix,'business/','Для бизнеса')}</div></div><span class="hero-endnote">WEST-EST · MINSK</span><a class="hero-annotation" href="{href(prefix,path_category(CATS[151]))}"><span class="annotation-line"></span><span>01 / Оливковое масло<small>Смотреть категорию ↗</small></span></a></section><div class="wrap intro-line"><span>Итальянский вкус. Внимание к деталям.</span><span>Для вашей кухни и бизнеса</span><a href="{href(prefix,'contact/')}">Минск, Беларусь ↗</a></div><section class="wrap section"><div class="section-head"><div><p class="eyebrow">КОЛЛЕКЦИЯ WEST-EST</p><h2>Ингредиенты с характером</h2></div>{link(prefix,'shop/','Весь каталог')}</div><div class="category-grid">{''.join(cat_tile(CATS[id],prefix,i+1) for i,id in enumerate([186,151,154]))}</div><div class="category-index">{more}</div></section><section class="wrap section" style="padding-top:0"><div class="section-head"><div><p class="eyebrow">ЗНАКОМСТВО С КОЛЛЕКЦИЕЙ</p><h2>Начните с хорошего</h2></div>{link(prefix,'shop/','Смотреть продукты')}</div><div class="products-grid">{''.join(card(p,prefix) for p in featured)}</div></section><section class="story-section"><div class="story-photo"><img src="{prefix}assets/story-900.webp" alt="Фактура сыра, оливковое масло и итальянская паста" width="900" height="950" loading="lazy" decoding="async"></div><div class="story-content"><p class="eyebrow">ДЕТАЛИ, КОТОРЫЕ ИМЕЮТ ЗНАЧЕНИЕ</p><h2>За каждым вкусом<br>стоит свой продукт.</h2><p>Форма пасты, характер масла, текстура сыра. Всё начинается с ингредиентов, которые вы выбираете.</p><p>Познакомьтесь с производителями в нашей коллекции и найдите продукты для своих рецептов.</p>{link(prefix,'producers/','Познакомиться с производителями')}</div></section><section class="wrap section"><div class="section-head"><div><p class="eyebrow">ИМЕНА В НАШЕЙ КОЛЛЕКЦИИ</p><h2>Знакомство по вкусу</h2></div>{link(prefix,'producers/','Все производители')}</div><div class="brand-strip">{brandlinks}</div></section>{business_cta(prefix)}'''

def catalog_content(c=None,list_page=1):
    def render(prefix):
        items=sorted([p for p in PRODUCTS if not c or c['id'] in p['categories']],key=lambda p:p['sourceOrder'])
        total=len(items);pageitems=items[(list_page-1)*12:list_page*12]
        title=c['displayName'] if c else 'Коллекция WEST-EST'
        catlinks=f'<li><a href="{href(prefix,"shop/")}"'+(' aria-current="page"' if not c else '')+f'>Все продукты<span>{len(PRODUCTS)}</span></a></li>'
        catlinks+=''.join(f'<li><a data-cat="{cc["id"]}" href="{href(prefix,path_category(cc))}"'+(' aria-current="page"' if c and cc['id']==c['id'] else '')+f'>{e(cc["displayName"])}<span>{cc["count"]}</span></a></li>' for cc in CATEGORIES)
        nav=''.join(f'<a href="{href(prefix,(path_category(c) if c else "shop/")+("page/"+str(n)+"/" if n>1 else ""))}"'+(' aria-current="page"' if n==list_page else '')+f'>{n}</a>' for n in range(1,(total+11)//12+1))
        view=''.join(f'<button type="button" data-view="{v}" aria-label="{label}" aria-pressed="{str(v=="3").lower()}">{icon("list") if v=="list" else v}</button>' for v,label in [('2','Сетка в две колонки'),('3','Сетка в три колонки'),('4','Сетка в четыре колонки'),('list','Список')])
        return f'''<div class="wrap">{breadcrumbs(prefix,[('shop/','Каталог'),('',title)] if c else [('', 'Каталог')])}<div class="page-intro"><p class="eyebrow">ПРОДУКТЫ С ХАРАКТЕРОМ</p><h1 id="catalog-title">{e(title)}</h1><p>Найдите свой продукт. Состав, фасовка и подробности в каждой карточке.</p></div><div class="catalog-layout"><aside class="catalog-sidebar"><details open><summary>Категории</summary><ul class="category-list">{catlinks}</ul></details><div class="sidebar-contact"><p>Нужна помощь с выбором?</p><a class="text-link" href="{TG}" target="_blank" rel="noopener">Написать менеджеру {icon('diagonal')}</a></div></aside><div><div id="catalog-tools"><form class="catalog-search" id="catalog-search-form" action="" role="search">{icon('search')}<input id="catalog-query" type="search" name="q" aria-label="Поиск в каталоге" placeholder="Название, производитель или артикул"><button type="submit" aria-label="Найти продукт">{icon()}</button></form><label class="brand-filter" for="catalog-brand">Производитель<select id="catalog-brand"><option value="">Все производители</option></select></label><div class="catalog-toolbar"><span id="catalog-count" role="status" aria-live="polite">{(list_page-1)*12+1}–{min(list_page*12,total)} из {total} {count_word(total)}</span><div class="view-controls" role="group" aria-label="Вид каталога">{view}</div><label><span class="sr-only">Сортировка</span><select id="catalog-sort" aria-label="Сортировка"><option value="menu_order">По умолчанию</option><option value="popularity">По популярности</option><option value="date">Сначала новые</option><option value="price">Цена: по возрастанию</option><option value="price-desc">Цена: по убыванию</option><option value="title">По алфавиту</option></select></label></div></div><div class="products-grid" id="catalog-grid" data-view="3">{''.join(card(p,prefix) for p in pageitems)}</div><nav class="pagination" id="catalog-pagination" aria-label="Страницы каталога">{nav}</nav><noscript><p class="noscript-notice">Откройте категорию и страницу по ссылке. Для поиска, фильтров и быстрого просмотра включите JavaScript.</p></noscript></div></div></div>'''
    return render

def product_content(p):
    def render(prefix):
        cats=[CATS[id] for id in p['categories'] if id in CATS and id!=16]
        cat=cats[0] if cats else CATS[p['categories'][0]]
        images=p['images'];image=images[0]['localLarge'] if images else 'assets/placeholder.svg'
        thumbs=''.join(f'<button data-gallery-src="{i["localLarge"]}" aria-label="Фото {n+1}" aria-pressed="{str(n==0).lower()}"><img src="{prefix}{i["local"]}" alt="" width="65" height="65" loading="lazy"></button>' for n,i in enumerate(images)) if len(images)>1 else ''
        specs=[]
        for line in p['description'].splitlines():
            if ':' in line:
                k,v=line.split(':',1)
                if k.strip() and v.strip() and len(k)<45:specs.append((k.strip(),v.strip()))
        spec_html='<dl class="product-specs">'+''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in specs)+'</dl>' if specs else ''
        related=[x for x in PRODUCTS if x['id']!=p['id'] and cat['id'] in x['categories']][:4]
        catlinks=', '.join(f'<a href="{href(prefix,path_category(cc))}">{e(cc["displayName"])}</a>' for cc in cats)
        return f'''<div class="wrap">{breadcrumbs(prefix,[('shop/','Каталог'),(path_category(cat),cat['displayName']),('',name(p))])}<div class="product-detail"><div class="product-gallery"><button class="product-main-image" data-zoom aria-label="Увеличить фотографию"><img id="product-image" src="{prefix}{image}" alt="{e(p['name'])}" width="1200" height="1200" fetchpriority="high"><span class="zoom-label">{icon('search')} Увеличить</span></button><div class="gallery-thumbs">{thumbs}</div></div><div><p class="eyebrow">{e(p['brand'] or cat['displayName'])}</p><h1>{e(name(p))}</h1><div class="product-number"><span>{'Артикул '+e(p['sku']) if p['sku'] else 'Коллекция WEST-EST'}</span><span>{'Наличие уточняйте у менеджера' if p['isInStock'] else 'Поставка под заказ'}</span></div>{spec_html}<details class="description-details" open><summary>О продукте {icon('plus')}</summary><p class="product-description">{e(p['description'] or 'Подробности о продукте, фасовке и условиях поставки уточните у менеджера.')}</p></details><p class="small muted">Категория: {catlinks}</p><div class="product-enquiry"><div class="button-row"><a class="btn" href="{TG}" target="_blank" rel="noopener">Уточнить цену {icon('diagonal')}</a><a class="text-link" href="tel:+375296500536">Позвонить {icon()}</a></div><p>Сообщите менеджеру название{' или артикул '+e(p['sku']) if p['sku'] else ' продукта'}, чтобы уточнить цену, наличие и условия поставки.</p></div></div></div><section class="related-section"><div class="section-head"><div><p class="eyebrow">ПРОДОЛЖИТЕ ЗНАКОМСТВО</p><h2>Из этой же коллекции</h2></div>{link(prefix,path_category(cat),'Все продукты')}</div><div class="products-grid">{''.join(card(x,prefix) for x in related)}</div></section></div>'''
    return render

def contacts(prefix):
    audit=json.loads((ROOT/'data/functional-audit.json').read_text());mp=audit['contacts']['map']
    return f'''<div class="wrap">{breadcrumbs(prefix,[('','Контакты')])}<div class="page-intro"><p class="eyebrow">WEST-EST · MINSK</p><h1>Будем на связи.</h1><p>Поможем с выбором продуктов и ответим на вопросы о сотрудничестве.</p></div><div class="contact-layout"><div><div class="contact-group"><p class="eyebrow">01 / ВАШ МЕНЕДЖЕР</p><a class="contact-phone" href="tel:+375296500536">+375 (29) 650-05-36</a><p><a href="mailto:{EMAIL}">{EMAIL}</a></p><a class="text-link" href="{TG}" target="_blank" rel="noopener">Написать в Telegram {icon('diagonal')}</a></div><div class="contact-group"><p class="eyebrow">02 / ОФИС</p><h2>Минск, Киселёва, 12</h2><p><a href="tel:+375296500785">+375 (29) 650-07-85</a></p><p class="muted">Понедельник–пятница, 09:00–17:00</p></div><div class="contact-group"><p class="eyebrow">03 / СКЛАД</p><h2>Минск, Красная, 7</h2><p><a href="tel:+375293629606">+375 (29) 362-96-06</a></p><p><a href="tel:+375296500481">+375 (29) 650-04-81</a></p><p class="muted">Понедельник–пятница, 09:00–17:00</p></div></div><div class="contact-map" data-map="{e(mp)}"><div class="contact-map-placeholder"><div class="map-pin">{icon('pin')}</div><strong>Ждём в Минске</strong><p>Склад WEST-EST<br>ул. Красная, 7</p><button class="btn btn-outline" data-load-map>Показать карту {icon('diagonal')}</button><p class="small">Google Maps</p></div></div></div></div>'''

def business(prefix):return f'''<div class="wrap">{breadcrumbs(prefix,[('','Для бизнеса')])}<section class="business-intro"><div><p class="eyebrow">WEST-EST ДЛЯ БИЗНЕСА</p><h1>В основе хорошей кухни.<br>Ваш выбор.</h1><p>Сыры, паста, оливковое масло, томаты и другие продукты для вашей кухни и ассортимента.</p><p>Подберите позиции в каталоге и свяжитесь с менеджером. Уточним наличие, фасовку, цены и условия поставки под вашу задачу.</p><div class="button-row"><a class="btn" href="{TG}" target="_blank" rel="noopener">Запросить прайс {icon('diagonal')}</a>{link(prefix,'shop/','Открыть каталог')}</div></div><div class="business-image"><img src="{prefix}assets/story-900.webp" alt="Оливковое масло, сыр и паста" width="900" height="950"></div></section><section class="business-steps"><div><span class="step-number">01</span><h2>Выберите продукты</h2><p>Весь ассортимент с фотографиями, артикулами и описаниями представлен в каталоге.</p></div><div><span class="step-number">02</span><h2>Расскажите о задаче</h2><p>Сообщите нужные позиции, фасовку и объём. Менеджер поможет уточнить детали.</p></div><div><span class="step-number">03</span><h2>Обсудите поставку</h2><p>Согласуйте актуальную стоимость, наличие и удобные условия получения.</p></div></section><section class="contact-group"><p class="eyebrow">ОБСУДИМ СОТРУДНИЧЕСТВО</p><h2><a href="tel:+375296500536">+375 (29) 650-05-36</a></h2><p><a href="mailto:{EMAIL}">{EMAIL}</a> · Пн–пт, 09:00–17:00</p></section></div>'''
def producers(prefix):
    excluded={'Italy','Беларусь','РБ','Тайланд'}
    brands=sorted(set(p['brand'] for p in PRODUCTS if p['brand'] and p['brand'] not in excluded),key=str.casefold)
    entries=''.join(f'<a class="brand-entry" href="{href(prefix,"shop/")}?brand={quote(b)}"><div><h2>{e(b)}</h2><p>{sum(1 for p in PRODUCTS if p["brand"]==b)} {count_word(sum(1 for p in PRODUCTS if p["brand"]==b))} в коллекции</p></div>{icon("diagonal")}</a>' for b in brands)
    return f'<div class="wrap">{breadcrumbs(prefix,[("","Производители")])}<div class="page-intro"><p class="eyebrow">ИМЕНА ЗА ПРОДУКТАМИ</p><h1>Каждый со своим характером.</h1><p>Познакомьтесь с марками из каталога WEST-EST. Выберите производителя, чтобы посмотреть его продукты.</p></div><div class="brands-grid">{entries}</div></div>'

def main():
    (OUT/'assets').mkdir(parents=True,exist_ok=True)
    css=(ROOT/'src/styles.css').read_text()
    (OUT/'assets/styles.css').write_text(css)
    shutil.copy2(ROOT/'src/app.js',OUT/'assets/app.js')
    compact={'categories':CATEGORIES,'products':[{k:p[k] for k in ['id','name','slug','sku','description','images','categories','brand','price','isInStock','date','sourceOrder']} for p in PRODUCTS]}
    for p in compact['products']:p['images']=[{k:i[k] for k in ['local','localLarge','alt']} for i in p['images']]
    (OUT/'assets/catalogue.json').write_text(json.dumps(compact,ensure_ascii=False,separators=(',',':')))
    page('', 'Продукты из Италии. Вкус начинается с происхождения',home,'home',hero=True,description='WEST-EST: паста, оливковое масло, сыры, томаты и деликатесы. Коллекция продуктов для вашей кухни и бизнеса. Минск, Беларусь.')
    page('shop','Каталог продуктов',catalog_content(), 'catalog')
    for n in range(2,(len(PRODUCTS)+11)//12+1):page('shop/page/'+str(n),'Каталог продуктов · страница '+str(n),catalog_content(list_page=n),'catalog',list_page=n)
    for c in CATEGORIES:
        path=path_category(c).strip('/')
        page(path,c['displayName'],catalog_content(c),'catalog',category=c['id'])
        for n in range(2,(c['count']+11)//12+1):page(path+'/page/'+str(n),c['displayName']+' · страница '+str(n),catalog_content(c,n),'catalog',category=c['id'],list_page=n)
    for p in PRODUCTS:page(path_product(p).strip('/'),name(p),product_content(p),'product',description=p['description'].replace('\n',' · ') or p['name'])
    page('contact','Контакты',contacts,'contact');page('business','Для бизнеса',business,'business');page('producers','Производители',producers,'producers')
    page('categories','Все категории',lambda prefix:f'<div class="wrap">{breadcrumbs(prefix,[("","Все категории")])}<div class="page-intro"><p class="eyebrow">КОЛЛЕКЦИЯ WEST-EST</p><h1>Выберите свой вкус.</h1></div><div class="all-categories-grid">'+''.join(cat_tile(c,prefix,i+1) for i,c in enumerate(CATEGORIES))+'</div></div>','catalog')
    page('404','Страница не найдена',lambda prefix:f'<div class="wrap notfound"><p class="eyebrow">WEST-EST</p><h1>404</h1><p>Такой страницы нет. Хорошие продукты найдутся в каталоге.</p>{link(prefix,"shop/","Открыть каталог","btn")}</div>')
    shutil.copy2(OUT/'404/index.html',OUT/'404.html')
    # GitHub Pages 404 executes from the requested nested URL: ensure asset roots are absolute.
    p404=(OUT/'404.html').read_text().replace('../',SITE)
    (OUT/'404.html').write_text(p404)
    (OUT/'.nojekyll').write_text('')
    routes=sorted(p.relative_to(OUT).as_posix().removesuffix('index.html') for p in OUT.rglob('index.html') if '404' not in p.parts and '_qa' not in p.parts)
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+SITE+quote(r,safe='/')+'</loc></url>' for r in routes)+'</urlset>')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+SITE+'sitemap.xml\n')
    print(json.dumps({'pages':len(routes),'products':len(PRODUCTS),'categories':len(CATEGORIES),'cssBytes':len(css.encode()),'catalogueBytes':(OUT/'assets/catalogue.json').stat().st_size},ensure_ascii=False))
if __name__=='__main__':main()
