// Development only: npm install sharp, then node scripts/render-bottles.cjs.
const sharp=require('sharp'),fs=require('fs'),path=require('path'),{execFileSync}=require('child_process');
(async()=>{
 const dir=path.join(__dirname,'../dist/assets'),tmp='/tmp/retail-bottle-sources';fs.mkdirSync(tmp,{recursive:true});
 for(const f of fs.readdirSync(dir).filter(x=>x.endsWith('.webp')&&(x.startsWith('label-')||x.startsWith('flanders-poster-')||x==='bottle-blank.webp')))await sharp(path.join(dir,f)).png().toFile(path.join(tmp,f+'.png'));
 execFileSync('python3',[path.join(__dirname,'build-bottles.py')],{stdio:'inherit'});
 for(const f of fs.readdirSync(dir).filter(x=>x.endsWith('-bottle.svg'))){await sharp(path.join(dir,f),{density:96}).resize({height:600}).webp({quality:86,alphaQuality:95}).toFile(path.join(dir,f.replace('.svg','.webp')));fs.unlinkSync(path.join(dir,f));}
})();
