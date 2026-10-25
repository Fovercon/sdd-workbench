/* Independent real-browser checks for native-authored, source-bound snapshots. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {pathToFileURL}=require('url');
(async()=>{const runs=process.argv.slice(2).map(p=>path.resolve(p));assert(runs.length,'Supply completed trial directories');const browser=await chromium.launch({channel:process.env.SDD_BROWSER_CHANNEL||'chrome'});try{
 for(const run of runs){const q=JSON.parse(fs.readFileSync(path.join(run,'quality.json')));assert.equal(q.automated_quality,'PASS');const root=q.latest;const snapshot=JSON.parse(fs.readFileSync(path.join(root,'snapshot.json')));const before=fs.readFileSync(path.join(root,'receipt.json'));const checks=[],errors=[],remote=[];const out=path.join(run,'browser');fs.mkdirSync(out,{recursive:true});
  function ok(name,value){assert(value,name);checks.push(name);}
  for(const width of [390,1440]){const page=await browser.newPage({viewport:{width,height:1080}});page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url());});
   for(const stage of ['Constitution','Align','Implement','Finish']){await page.goto(pathToFileURL(path.join(root,'index.html')).href+'#stage-'+stage);ok(`${width}:${stage}:visible`,await page.locator(`[data-stage-reading="${stage}"]`).isVisible());ok(`${width}:${stage}:no overflow`,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    if(stage==='Align'){ok(`${width}:scope not fabricated as missing`,!(await page.locator('[data-stage-section="scope"]').textContent()).includes('尚未提供目标与范围记录'));ok(`${width}:question remains unanswered`,await page.locator('[data-stage-panel="Align"] .decision-form').count()===1&&await page.locator('[data-stage-panel="Align"] input:checked').count()===0);}
    if(stage==='Implement'){for(const i of snapshot.items.filter(i=>i.stage_detail?.type==='test_run')){const label={PASS:'通过',FAIL:'失败',NOT_RUN:'未执行'}[i.stage_detail.result];ok(`${width}:recorded ${i.stage_detail.result} visible`,(await page.locator(`[data-stage-record=${JSON.stringify(i.id)}]`).textContent()).includes('原记录中的运行结果'+label));}}
    if(stage==='Finish'){const i=snapshot.items.find(i=>i.stage_detail?.type==='deliverable');ok(`${width}:prepared is not delivered`,(await page.locator(`[data-stage-record=${JSON.stringify(i.id)}]`).textContent()).includes('已准备，待交付'));await page.screenshot({path:path.join(out,`finish-${width}.png`)});}
   }
   await page.goto(pathToFileURL(path.join(root,'index.html')).href);ok(`${width}:synthetic boundary visible`,(await page.locator('.project-overview').textContent()).includes('合成'));await page.close();
  }
  ok('receipt preserved',before.equals(fs.readFileSync(path.join(root,'receipt.json'))));ok('no page errors',errors.length===0);ok('no remote resources',remote.length===0);
  fs.writeFileSync(path.join(out,'receipt.json'),JSON.stringify({browser:browser.version(),checks,errors,remote,html_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'index.html'))).digest('hex'),scope:'Synthetic authored snapshots; not human comprehension or business acceptance.'},null,2));console.log(JSON.stringify({trial:path.basename(run),checks:checks.length}));
 }
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
