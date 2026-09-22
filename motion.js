/* Motion has a job: acknowledge a press, orient a transition, dismiss a sheet.
   No DOM screenshots, image parallax, scroll listeners or idle rendering loops. */
const Motion=(()=>{
 const reduce=matchMedia('(prefers-reduced-motion: reduce)');
 const ease='cubic-bezier(.2,.8,.2,1)';
 const running=new Set();let pageAnimation=null,press=null,drag=null,dismiss=null;
 const enabled=()=>!reduce.matches&&!document.hidden;
 function animate(el,frames,options={}){if(!el||!enabled())return null;const a=el.animate(frames,{duration:260,easing:ease,...options});running.add(a);a.finished.catch(()=>{}).finally(()=>running.delete(a));return a;}
 function page(from,to){pageAnimation?.cancel();const el=document.querySelector('#app-content>.page');if(!enabled()||!el)return;pageAnimation=animate(el,[{opacity:.72,transform:'translateY(7px)'},{opacity:1,transform:'translateY(0)'}],{duration:280});}
 function nav(){const host=document.querySelector('#bottom-nav'),b=host?.querySelector('button.active');if(!b)return;let marker=host.querySelector('.nav-liquid');if(!marker){marker=document.createElement('i');marker.className='nav-liquid';marker.setAttribute('aria-hidden','true');host.prepend(marker);}marker.style.width=b.offsetWidth+'px';marker.style.transform=`translateX(${b.offsetLeft}px)`;}
 function releasePress(){if(!press)return;const {el,a}=press;press=null;a?.cancel();if(el.isConnected)animate(el,[{scale:'.98'},{scale:'1'}],{duration:220});}
 document.addEventListener('pointerdown',e=>{if(!enabled())return;const handle=e.target.closest('.dialog-handle');if(handle){drag={id:e.pointerId,y:e.clientY,dy:0,dialog:handle.closest('dialog'),handle};handle.setPointerCapture(e.pointerId);return;}const el=e.target.closest('button');if(!el||el.disabled||el.closest('#bottom-nav')||el.classList.contains('city-marker'))return;releasePress();press={el,id:e.pointerId,x:e.clientX,y:e.clientY,a:animate(el,[{scale:'1'},{scale:'.98'}],{duration:110,easing:'ease-out',fill:'forwards'})};},{passive:true});
 document.addEventListener('pointermove',e=>{if(press&&(Math.abs(e.clientX-press.x)>8||Math.abs(e.clientY-press.y)>8)){press.a?.cancel();press=null;}if(!drag||e.pointerId!==drag.id)return;const scale=drag.dialog.getBoundingClientRect().width/drag.dialog.offsetWidth;drag.dy=Math.max(0,(e.clientY-drag.y)/scale);drag.dialog.style.translate=`0 ${Math.min(drag.dy,220)}px`;},{passive:true});
 function endDrag(cancelled=false){releasePress();if(!drag)return;const {dialog,dy}=drag;drag=null;if(!cancelled&&dy>72&&dismiss){dismiss();return;}animate(dialog,[{translate:dialog.style.translate||'0 0'},{translate:'0 0'}],{duration:260});dialog.style.translate='';}
 document.addEventListener('pointerup',()=>endDrag());document.addEventListener('pointercancel',()=>endDrag(true));
 function success(button){if(!button||!enabled())return;animate(button,[{scale:'.98'},{scale:'1.006',offset:.6},{scale:'1'}],{duration:260});}
 function stop(){for(const a of running)a.cancel();running.clear();press=null;pageAnimation=null;if(drag)drag.dialog.style.translate='';drag=null;}
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});reduce.addEventListener('change',()=>{if(reduce.matches)stop();});
 return {page,nav,animate,success,capture:()=>null,origin:()=>null,morph:()=>{},observe:()=>{},setDismiss:fn=>dismiss=fn,closed:()=>{const d=document.querySelector('#app-dialog');if(d)d.style.translate='';}};
})();
