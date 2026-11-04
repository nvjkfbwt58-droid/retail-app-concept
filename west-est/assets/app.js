(() => {
  'use strict';
  const script = document.currentScript;
  const root = new URL('../', script.src);
  const $ = (s, p = document) => p.querySelector(s);
  const $$ = (s, p = document) => [...p.querySelectorAll(s)];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
  const url = path => new URL(path, root).href;
  const productUrl = p => url(`product/${encodeURIComponent(p.slug)}/`);
  const catName = c => c.displayName || c.name;
  const niceName = p => p.name.replace(/^(?:(?:Арт|Атр)\.?\s*)?\d{3,6}\s*[:.\-]?\s*/iu, '').trim().replace(/(\d)\s*(кг|гр\.?|г|мл|л)(?=$|[\s,.;])/giu,(_,n,u)=>n+'\u00a0'+(u.toLowerCase().startsWith('гр')?'г':u.toLowerCase()));
  const imageMarkup = (photo,alt='',large=false,eager=false) => `<img class="product-cutout${photo?.presentation?' is-normalized':''}" style="${esc(photo?.presentation||'')}" src="${url(photo?.[large?'localLarge':'local']||'assets/placeholder.svg')}" alt="${esc(alt)}" width="${large?1200:520}" height="${large?1200:520}" ${eager?'':'loading="lazy"'} decoding="async">`;
  const norm = s => String(s || '').toLowerCase().replace(/ё/g, 'е').normalize('NFKC');
  const plural = n => n%10===1 && n%100!==11 ? 'товар' : n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 'товара' : 'товаров';
  let cataloguePromise;
  const loadData = () => cataloguePromise ||= fetch(url('assets/catalogue.json')+'?v='+(new URL(script.src).searchParams.get('v')||'1')).then(r => { if(!r.ok) throw new Error('catalogue'); return r.json(); });
  const closeDialog = dialog => { if(dialog?.open) dialog.close(); };
  $$('dialog').forEach(dialog => {
    dialog.addEventListener('click', e => { if(e.target === dialog) { const r=dialog.getBoundingClientRect(); if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom) dialog.close(); } });
    $$('[data-close]',dialog).forEach(b=>b.addEventListener('click',()=>dialog.close()));
  });
  const menu = $('[data-mobile-menu]');
  $('[data-menu-toggle]')?.addEventListener('click', e => { const b=e.currentTarget; const open=b.getAttribute('aria-expanded')!=='true'; b.setAttribute('aria-expanded',String(open)); menu.classList.toggle('is-open',open); });
  document.addEventListener('keydown', e=>{if(e.key==='Escape'&&menu?.classList.contains('is-open')){menu.classList.remove('is-open');$('[data-menu-toggle]').setAttribute('aria-expanded','false');}});
  const sidebar = $('.catalog-sidebar details');
  if(sidebar && matchMedia('(max-width:760px)').matches) sidebar.open=false;
  const searchDialog=$('#search-dialog'), searchInput=$('#global-search'), searchCat=$('#search-category'), results=$('#search-results');
  let searchVersion=0;
  async function search() {
    const version=++searchVersion, q=searchInput.value.trim();
    if(!q){results.innerHTML='<p class="search-hint">Например: Granoro, оливковое масло или артикул товара.</p>';return;}
    try{
      const data=await loadData();if(version!==searchVersion)return;
      const tokens=norm(q).split(/\s+/).filter(Boolean);
      const found=data.products.filter(p=>(!searchCat.value||p.categories.includes(Number(searchCat.value))) && tokens.every(t=>norm([p.name,p.sku,p.brand,p.description].join(' ')).includes(t)));
      const target=new URL('shop/',root);target.searchParams.set('q',q);if(searchCat.value)target.searchParams.set('category',searchCat.value);
      results.innerHTML=found.length?found.slice(0,6).map(p=>`<a class="search-result" href="${productUrl(p)}"><span class="search-product-visual product-stage">${imageMarkup(p.images[0])}</span><span><strong>${esc(niceName(p))}</strong><small>${esc(p.brand||'WEST-EST')}${p.sku?' · Арт. '+esc(p.sku):''}</small></span></a>`).join('')+`<a class="btn search-all" href="${target.href}">Все результаты (${found.length}) <span aria-hidden="true">↗</span></a>`:'<p class="search-hint" role="status">Ничего не найдено. Попробуйте другое название или артикул.</p>';
    }catch{results.innerHTML=`<p class="search-hint">Не удалось загрузить поиск. <a class="text-link" href="${url('shop/')}">Открыть каталог</a></p>`;}
  }
  $$('[data-open-search]').forEach(b=>b.addEventListener('click',()=>{searchDialog.showModal();searchInput.focus();loadData().catch(()=>{});}));
  searchInput?.addEventListener('input',search);searchCat?.addEventListener('change',search);
  $('#global-search-form')?.addEventListener('submit',e=>{e.preventDefault();const target=new URL('shop/',root);if(searchInput.value.trim())target.searchParams.set('q',searchInput.value.trim());if(searchCat.value)target.searchParams.set('category',searchCat.value);location.assign(target.href);});
  function card(p) {
    const name=niceName(p), image=p.images[0]?.local||'assets/placeholder.svg';
    return `<article class="product-card"><div class="product-visual"><a class="product-stage" href="${productUrl(p)}" tabindex="-1" aria-hidden="true">${imageMarkup(p.images[0],name)}</a><button class="quick-view" data-quick="${p.id}" aria-label="Быстрый просмотр: ${esc(name)}"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg></button></div><div class="product-info"><span class="product-brand">${esc(p.brand||'WEST-EST')}</span><h3><a href="${productUrl(p)}">${esc(name)}</a></h3><div class="product-meta"><span>${p.sku?'Арт. '+esc(p.sku):'WEST-EST'}</span><span>${p.isInStock?'Уточнить цену':'Под заказ'}</span></div></div></article>`;
  }
  document.addEventListener('click',async e=>{
    const btn=e.target.closest('[data-quick]');if(!btn)return;
    const dialog=$('#quick-dialog');btn.disabled=true;
    try{const data=await loadData(),p=data.products.find(p=>p.id===Number(btn.dataset.quick));if(!p)return;
      $('#quick-content').innerHTML=`<div class="quick-dialog-inner"><div class="quick-product-visual product-stage">${imageMarkup(p.images[0],niceName(p),true,true)}</div><div><span class="eyebrow">${esc(p.brand||'Коллекция WEST-EST')}</span><h2 id="quick-title">${esc(niceName(p))}</h2><p class="muted">${p.sku?'Артикул '+esc(p.sku):''}</p><p class="product-description">${esc(p.description||'Подробности о продукте, фасовке и условиях поставки уточните у менеджера.')}</p><a class="btn" href="${productUrl(p)}">Подробнее о продукте <span aria-hidden="true">↗</span></a><p class="muted">Цену и наличие уточняйте у менеджера.</p></div></div>`;
      dialog.showModal();
    }catch{location.assign(btn.closest('.product-card').querySelector('h3 a').href);}finally{btn.disabled=false;}
  });
  $$('[data-gallery-src]').forEach(b=>b.addEventListener('click',()=>{const image=$('#product-image');image.src=url(b.dataset.gallerySrc);image.style.cssText=b.dataset.presentation||'';image.classList.toggle('is-normalized',!!b.dataset.presentation);$$('[data-gallery-src]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));}));
  $('[data-zoom]')?.addEventListener('click',()=>{const main=$('#product-image'),zoom=$('#zoom-image');zoom.src=main.src;zoom.alt=main.alt;zoom.style.cssText=main.style.cssText;zoom.classList.toggle('is-normalized',main.classList.contains('is-normalized'));$('#image-dialog').showModal();});
  $('[data-load-map]')?.addEventListener('click',e=>{const panel=e.currentTarget.closest('.contact-map');const frame=document.createElement('iframe');frame.title='Склад WEST-EST, Минск, улица Красная, 7';frame.src=panel.dataset.map;frame.referrerPolicy='no-referrer-when-downgrade';frame.allowFullscreen=true;panel.replaceChildren(frame);});
  const catalogGrid=$('#catalog-grid');
  if(catalogGrid) initCatalogue();
  async function initCatalogue(){
    let data;try{data=await loadData();}catch{return;}
    const query=$('#catalog-query'),sort=$('#catalog-sort'),brand=$('#catalog-brand'),count=$('#catalog-count'),pagination=$('#catalog-pagination');
    const fixedCategory=Number(document.body.dataset.category||0),params=new URLSearchParams(location.search);
    let page=Math.max(1,Number(params.get('page'))||Number(document.body.dataset.listPage)||1),view=params.get('view')||'3';
    query.value=params.get('q')||params.get('s')||'';sort.value=params.get('orderby')||'menu_order';
    const category=fixedCategory||Number(params.get('category')||0);
    let brandValue=params.get('brand')||'';
    const relevant=data.products.filter(p=>!category||p.categories.includes(category));
    const brands=[...new Set(relevant.map(p=>p.brand).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'ru'));
    brand.innerHTML='<option value="">Все производители</option>'+brands.map(b=>`<option value="${esc(b)}">${esc(b)}</option>`).join('');brand.value=brandValue;
    if(category&&!fixedCategory){const c=data.categories.find(c=>c.id===category);if(c){$('#catalog-title').textContent=catName(c);$$('.category-list a').forEach(a=>{if(a.dataset.cat===String(category))a.setAttribute('aria-current','page');});}}
    const setQuery=(push=false)=>{const u=new URL(location.href);for(const key of ['q','s','brand','orderby','page','view'])u.searchParams.delete(key);if(query.value.trim())u.searchParams.set('q',query.value.trim());if(brand.value)u.searchParams.set('brand',brand.value);if(sort.value!=='menu_order')u.searchParams.set('orderby',sort.value);if(page>1)u.searchParams.set('page',page);if(view!=='3')u.searchParams.set('view',view);history[push?'pushState':'replaceState']({},'',u);};
    function render(update=true,push=false){
      const tokens=norm(query.value.trim()).split(/\s+/).filter(Boolean);
      let list=relevant.filter(p=>(!brand.value||norm(p.brand)===norm(brand.value))&&tokens.every(t=>norm([p.name,p.sku,p.brand,p.description].join(' ')).includes(t)));
      switch(sort.value){case'date':list.sort((a,b)=>String(b.date).localeCompare(String(a.date)));break;case'popularity':list.sort((a,b)=>(b.totalSales||0)-(a.totalSales||0)||(a.sourceOrder||0)-(b.sourceOrder||0));break;case'price':list.sort((a,b)=>(a.price??0)-(b.price??0)||(a.sourceOrder||0)-(b.sourceOrder||0));break;case'price-desc':list.sort((a,b)=>(b.price??0)-(a.price??0)||(a.sourceOrder||0)-(b.sourceOrder||0));break;case'title':list.sort((a,b)=>niceName(a).localeCompare(niceName(b),'ru'));break;default:list.sort((a,b)=>(a.sourceOrder||0)-(b.sourceOrder||0));}
      const total=list.length,pages=Math.max(1,Math.ceil(total/12));page=Math.min(page,pages);const start=(page-1)*12;
      if(update)setQuery(push);
      count.textContent=total?`${start+1}–${Math.min(start+12,total)} из ${total}`:'Товары не найдены';
      catalogGrid.innerHTML=total?list.slice(start,start+12).map(card).join(''):`<div class="empty-state"><h2>Ничего не найдено</h2><p>Попробуйте другое название, артикул или производителя.</p><button class="btn btn-outline" id="clear-catalog-filters">Сбросить фильтры</button></div>`;
      catalogGrid.dataset.view=view;$$('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
      const makePage=(n,label,aria='')=>{const u=new URL(location.href);u.searchParams.set('page',n);return `<a href="${u.href}" data-page-number="${n}" ${n===page?'aria-current="page"':''} ${aria?'aria-label="'+aria+'"':''}>${label}</a>`;};
      pagination.innerHTML=pages>1?(page>1?makePage(page-1,'←','Предыдущая страница'):'')+Array.from({length:pages},(_,i)=>i+1).filter(n=>n===1||n===pages||Math.abs(n-page)<=2).map((n,i,ns)=>(i&&n-ns[i-1]>1?'<span aria-hidden="true">…</span>':'')+makePage(n,n)).join('')+(page<pages?makePage(page+1,'→','Следующая страница'):''):'';
      $('#clear-catalog-filters')?.addEventListener('click',()=>{query.value='';brand.value='';page=1;render();});
    }
    query.addEventListener('input',()=>{page=1;render();});$('#catalog-search-form').addEventListener('submit',e=>{e.preventDefault();page=1;render();});sort.addEventListener('change',()=>{page=1;render(true,true);});brand.addEventListener('change',()=>{page=1;render(true,true);});
    $$('[data-view]').forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;render();}));
    pagination.addEventListener('click',e=>{const a=e.target.closest('[data-page-number]');if(!a||e.ctrlKey||e.metaKey||e.shiftKey)return;e.preventDefault();page=Number(a.dataset.pageNumber);render(true,true);$('#catalog-tools').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth',block:'start'});});
    window.addEventListener('popstate',()=>{const p=new URLSearchParams(location.search);query.value=p.get('q')||'';brand.value=p.get('brand')||'';sort.value=p.get('orderby')||'menu_order';page=Number(p.get('page'))||1;view=p.get('view')||'3';render(false);});
    render(false);
  }
  const legacy=new URLSearchParams(location.search);
  if(document.body.dataset.page==='home'&&(legacy.has('s')||legacy.has('product_cat'))){loadData().then(data=>{const target=new URL('shop/',root);if(legacy.get('s'))target.searchParams.set('q',legacy.get('s'));let slug=legacy.get('product_cat')||'';try{slug=decodeURIComponent(slug);}catch{}const c=data.categories.find(c=>c.slug===slug);if(c)target.searchParams.set('category',c.id);location.replace(target.href);}).catch(()=>{});}
})();
