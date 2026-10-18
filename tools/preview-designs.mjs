import { pathToFileURL } from 'node:url';
import { realpathSync } from 'node:fs';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright');
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { writeFileSync, unlinkSync } from 'node:fs';
const root = realpathSync(process.cwd());
const browser = await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE ? {executablePath:process.env.CHROMIUM_EXECUTABLE} : {})});
const checks=[];
try {
  for (const theme of ['a','b','c']) {
    for (const [device,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]) {
      const page=await browser.newPage({viewport,deviceScaleFactor:1});
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      const response=await page.goto('http://127.0.0.1:8035/design/direction-'+theme+'.html',{waitUntil:'networkidle'});
      const state=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,images:[...document.images].every(i=>i.complete&&i.naturalWidth>0&&i.alt),h1:document.querySelectorAll('h1').length,ids:[...document.querySelectorAll('[id]')].map(e=>e.id)}));
      if(response.status()!==200||state.overflow||!state.images||state.h1!==1||errors.length||new Set(state.ids).size!==state.ids.length)throw Error(JSON.stringify({theme,device,state,errors}));
      const path=join(root,'design','direction-'+theme+'-'+device+'.png');
      await page.screenshot({path,animations:'disabled'});
      execFileSync('cwebp',['-quiet','-q','88',path,'-o',path.replace('.png','.webp')]);unlinkSync(path);
      checks.push({theme,device,...viewport,status:response.status(),overflow:state.overflow,imagesLoaded:state.images,jsErrors:errors});
      await page.close();
    }
  }
  writeFileSync(join(root,'reports','design-checks.json'),JSON.stringify(checks,null,2));
  console.log('Six design screenshots passed: 200, no overflow, loaded images, one h1, unique IDs, no JS errors.');
} finally {await browser.close();}
