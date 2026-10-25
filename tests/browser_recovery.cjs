/* Evaluator-only real UI recovery and controlled-mutant sensitivity. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const {spawn, spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const prep = path.join(root, 'skills/sdd-verification-design/evals/forward/prepare_recovery.py');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'sdd-recovery-browser-'));
const py = process.env.SDD_PYTHON || 'python3';
const results = [], errors = [], remote = [];
async function start(project) {
  const proc = spawn(py, ['-B', path.join(project,'app.py'), '--state',path.join(project,'state.json')], {cwd:project,stdio:['ignore','pipe','pipe']});
  let stderr=''; proc.stderr.on('data',data=>stderr+=data);
  const url = await new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>{proc.kill();reject(Error('Fixture startup timed out: '+stderr))},15000);
    let text='';proc.stdout.on('data',data=>{text+=data;if(text.includes('\n')){clearTimeout(timeout);try{resolve(JSON.parse(text.split('\n')[0]).url)}catch(e){reject(e)}}});
    proc.once('error',error=>{clearTimeout(timeout);reject(error)});
    proc.once('exit',code=>{clearTimeout(timeout);reject(Error(`Fixture exited ${code}: ${stderr}`))});
  });
  return {url,stop:()=>new Promise(resolve=>{if(proc.exitCode!==null)return resolve();proc.once('exit',resolve);proc.kill('SIGTERM')})};
}
(async()=>{
  let browser,server;
  try {
    browser=await chromium.launch({headless:true,channel:process.env.SDD_BROWSER_CHANNEL||'chrome'});
    for (const variant of ['preserving','lossy','stale-error','combined']) {
      const project=path.join(temp,variant);
      const result=spawnSync(py,['-B',prep,'--output',project,'--variant',variant,'--receipt',path.join(temp,variant+'.json')],{encoding:'utf8'});
      assert.equal(result.status,0,result.stderr);
      server=await start(project);
      for(const width of [390,1280]) {
        const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();
        page.on('pageerror',error=>errors.push(error.message));
        await context.route('**/*',route=>{
          const url=route.request().url();
          if(/^https?:/.test(url)&&!url.startsWith(server.url+'/')){remote.push(url);return route.abort()}
          return route.continue();
        });
        await page.goto(server.url);
        await page.waitForFunction(()=>document.querySelectorAll('#records li').length===2);
        const ids=()=>page.locator('#records li').evaluateAll(rows=>rows.map(row=>row.dataset.id));
        assert.deepEqual(await ids(),['kept-1','kept-2']);
        await page.locator('#start').fill('2026-03-01');await page.locator('#end').fill('2026-01-01');
        const rejected=page.waitForResponse(response=>response.url().includes('/api/records?')&&response.status()===400);
        await page.getByRole('button',{name:'Filter',exact:true}).click();await rejected;
        await page.waitForFunction(()=>document.querySelector('#filter-error').textContent.length>0);
        const invalid={ids:await ids(),error:await page.locator('#filter-error').innerText()};
        assert.deepEqual(invalid.ids,['kept-1','kept-2']);assert.ok(invalid.error);
        const evidence=process.env.SDD_RECOVERY_EVIDENCE;
        if(evidence){fs.mkdirSync(evidence,{recursive:true});await page.screenshot({path:path.join(evidence,`${variant}-${width}-invalid.png`)})}
        await page.locator('#start').fill('2026-01-01');await page.locator('#end').fill('2026-01-31');
        const accepted=page.waitForResponse(response=>response.url().includes('/api/records?')&&response.status()===200);
        await page.getByRole('button',{name:'Filter',exact:true}).click();await accepted;
        await page.waitForFunction(()=>document.querySelectorAll('#records li').length===1);
        const corrected={ids:await ids(),error:await page.locator('#filter-error').innerText()};
        assert.deepEqual(corrected.ids,['kept-1']);
        const clean=corrected.error==='';
        assert.equal(clean,!['stale-error','combined'].includes(variant),'UI oracle must distinguish stale errors');
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
        if(evidence)await page.screenshot({path:path.join(evidence,`${variant}-${width}-corrected.png`)});
        results.push({variant,width,invalid,corrected,uiRecoveryPass:clean});
        await context.close();
      }
      await server.stop();server=null;
    }
    assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
    const report={flows:results.length,observations:results,errors,remote};
    if(process.env.SDD_RECOVERY_EVIDENCE)fs.writeFileSync(path.join(process.env.SDD_RECOVERY_EVIDENCE,'observations.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify(report,null,2));
  } finally {if(server)await server.stop();if(browser)await browser.close();fs.rmSync(temp,{recursive:true,force:true})}
})().catch(error=>{console.error(error);process.exitCode=1});
