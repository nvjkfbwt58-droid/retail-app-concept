/* Motion has a job: acknowledge a press, orient a transition, dismiss a sheet.
   No DOM screenshots, image parallax, scroll listeners or idle rendering loops. */
const Motion=(()=>{
 const reduce=matchMedia('(prefers-reduced-motion: reduce)');
 const ease='cubic-bezier(.2,.8,.2,1)';
 const running=new Set();let pageAnimation=null,press=null,drag=null,dismiss=null;
 const enabled=()=>!reduce.matches&&!document.hidden;
 function animate(el,frames,options={}){if(!el||!enabled())return null;const a=el.animate(frames,{duration:260,easing:ease,...options});running.add(a);a.finished.catch(()=>{}).finally(()=>running.delete(a));return a;}
 let lastNav=null;
 const entrances=new Set();
 function clearEntrance(){for(const a of entrances)a.cancel();entrances.clear();pageAnimation?.cancel();pageAnimation=null;}
 function capture(){clearEntrance();}
 function page(from,to){
  clearEntrance();if(!enabled())return;
  const pane=document.querySelector('#app-content'),root=pane?.querySelector(':scope>.page');if(!root)return;
  const bounds=pane.getBoundingClientRect();
  // Animate individual visible surfaces, never a full catalogue texture.
  const candidates=[...root.children].flatMap(n=>n.matches('.product-grid,.horizontal-products,.extra-coupons,.service-shortcuts')?[...n.children]:[n]);
  const visible=candidates.filter(n=>{const r=n.getBoundingClientRect();return r.width>0&&r.height>18&&r.bottom>bounds.top&&r.top<bounds.bottom;}).slice(0,12);
  visible.forEach((node,i)=>{
   const card=node.matches('button,.member-pass,.loyalty,.product-card,.panel,.menu-group');
   const distance=card?24:16,blur=card?7:4;
   const a=animate(node,[
    {opacity:0,translate:`0 ${distance}px`,scale:card?'.987':'1',filter:`blur(${blur}px)`},
    {opacity:.75,translate:'0 10px',scale:'.996',filter:'blur(1px)',offset:.22},
    {opacity:1,translate:'0 4px',scale:'1',filter:'blur(0px)',offset:.38},
    {opacity:1,translate:'0 0',scale:'1',filter:'blur(0px)'}
   ],{duration:540,delay:Math.min(i*30,150),easing:'linear',fill:'backwards'});
   if(a){entrances.add(a);a.finished.catch(()=>{}).finally(()=>entrances.delete(a));}
  });
 }
 document.addEventListener('wheel',clearEntrance,{passive:true});
 document.addEventListener('pointerdown',e=>{if(e.target.closest('#app-content'))clearEntrance();},{passive:true});

 function nav(){const host=document.querySelector('#bottom-nav'),b=host?.querySelector('button.active');if(!b)return;let marker=host.querySelector('.nav-liquid');if(!marker){marker=document.createElement('i');marker.className='nav-liquid';marker.setAttribute('aria-hidden','true');host.prepend(marker);}if(lastNav&&lastNav!==b){animate(b.querySelector('svg'),[{translate:'0 0',scale:'1'},{translate:'0 -2px',scale:'1.1',offset:.38},{translate:'0 0',scale:'1'}],{duration:420});}lastNav=b;marker.style.width=b.offsetWidth+'px';marker.style.transform=`translateX(${b.offsetLeft}px)`;}
 // Scrub navigation without rendering intermediate screens under the finger.
 let scrub=null,suppressClickUntil=0;
 function finishScrub(cancelled=false){
  if(!scrub)return;const s=scrub;scrub=null;
  s.host.classList.remove('is-scrubbing');s.buttons.forEach(b=>b.classList.remove('scrub-target'));
  if(s.host.hasPointerCapture(s.id))s.host.releasePointerCapture(s.id);
  if(s.moved){suppressClickUntil=performance.now()+400;if(!cancelled&&s.target!==s.active){s.target.click();}else nav();}
  else nav();
 }
 document.addEventListener('pointerdown',e=>{
  const host=e.target.closest('#bottom-nav');if(!host||!e.isPrimary||e.button!==0||scrub)return;suppressClickUntil=0;
  const buttons=[...host.querySelectorAll('button')],active=host.querySelector('button.active'),marker=host.querySelector('.nav-liquid');if(!active||!marker)return;
  const rect=host.getBoundingClientRect(),scale=rect.width/host.offsetWidth;
  scrub={host,buttons,active,marker,id:e.pointerId,startX:e.clientX,startY:e.clientY,scale,left:rect.left,origin:active.offsetLeft,target:active,moved:false};
 },{passive:true});
 document.addEventListener('pointermove',e=>{
  if(!scrub||e.pointerId!==scrub.id)return;const s=scrub,dx=e.clientX-s.startX,dy=e.clientY-s.startY;
  if(!s.moved){if(Math.abs(dx)<5)return;s.moved=true;s.host.setPointerCapture(s.id);s.host.classList.add('is-scrubbing');}
  const first=s.buttons[0],last=s.buttons[s.buttons.length-1];
  const x=Math.max(first.offsetLeft,Math.min(last.offsetLeft,s.origin+dx/s.scale));
  s.marker.style.transform=`translateX(${x}px)`;
  s.target=s.buttons.reduce((best,b)=>Math.abs(b.offsetLeft-x)<Math.abs(best.offsetLeft-x)?b:best,first);
  s.buttons.forEach(b=>b.classList.toggle('scrub-target',b===s.target));
 },{passive:true});
 document.addEventListener('pointerup',e=>{if(scrub?.id===e.pointerId)finishScrub();});
 document.addEventListener('pointercancel',e=>{if(scrub?.id===e.pointerId)finishScrub(true);});
 document.addEventListener('lostpointercapture',e=>{if(scrub?.id===e.pointerId)finishScrub(true);});
 document.addEventListener('click',e=>{if(e.isTrusted&&e.target.closest('#bottom-nav')&&performance.now()<suppressClickUntil){e.preventDefault();e.stopImmediatePropagation();}},true);
 window.addEventListener('resize',()=>finishScrub(true));
 function releasePress(){if(!press)return;const {el,a}=press;press=null;a?.cancel();if(el.isConnected)animate(el,[{scale:'.98'},{scale:'1'}],{duration:220});}
 document.addEventListener('pointerdown',e=>{if(!enabled())return;const handle=e.target.closest('.dialog-handle');if(handle){drag={id:e.pointerId,y:e.clientY,dy:0,dialog:handle.closest('dialog'),handle};handle.setPointerCapture(e.pointerId);return;}const el=e.target.closest('button');if(!el||el.disabled||el.closest('#bottom-nav')||el.classList.contains('city-marker'))return;releasePress();press={el,id:e.pointerId,x:e.clientX,y:e.clientY,a:animate(el,[{scale:'1'},{scale:'.98'}],{duration:110,easing:'ease-out',fill:'forwards'})};},{passive:true});
 document.addEventListener('pointermove',e=>{if(press&&(Math.abs(e.clientX-press.x)>8||Math.abs(e.clientY-press.y)>8)){press.a?.cancel();press=null;}if(!drag||e.pointerId!==drag.id)return;const scale=drag.dialog.getBoundingClientRect().width/drag.dialog.offsetWidth;drag.dy=Math.max(0,(e.clientY-drag.y)/scale);drag.dialog.style.translate=`0 ${Math.min(drag.dy,220)}px`;},{passive:true});
 function endDrag(cancelled=false){releasePress();if(!drag)return;const {dialog,dy}=drag;drag=null;if(!cancelled&&dy>72&&dismiss){dismiss();return;}animate(dialog,[{translate:dialog.style.translate||'0 0'},{translate:'0 0'}],{duration:260});dialog.style.translate='';}
 document.addEventListener('pointerup',()=>endDrag());document.addEventListener('pointercancel',()=>endDrag(true));
 function success(button){if(!button||!enabled())return;animate(button,[{scale:'.98'},{scale:'1.006',offset:.6},{scale:'1'}],{duration:260});}
 function stop(){clearEntrance();finishScrub(true);for(const a of running)a.cancel();running.clear();press=null;pageAnimation=null;if(drag)drag.dialog.style.translate='';drag=null;}
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});reduce.addEventListener('change',()=>{if(reduce.matches)stop();});
 return {page,nav,animate,success,capture,origin:()=>null,morph:()=>{},observe:()=>{},setDismiss:fn=>dismiss=fn,closed:()=>{const d=document.querySelector('#app-dialog');if(d)d.style.translate='';}};
})();
// Stop decorative motion when the page is not visible.
document.addEventListener('visibilitychange',()=>document.documentElement.classList.toggle('page-hidden',document.hidden));
