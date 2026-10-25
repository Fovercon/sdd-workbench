/* Actual browser checks for source-bound rules, intent, runs and delivery. */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process'),{pathToFileURL}=require('node:url');
const assert=require('node:assert/strict');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'sdd-stage-reading-'));
const output=process.env.SDD_STAGE_BROWSER_OUTPUT?path.resolve(process.env.SDD_STAGE_BROWSER_OUTPUT):root;
fs.mkdirSync(output,{recursive:true});
const cli=path.resolve(__dirname,'../scripts/project_view.py');
function run(...args){const p=spawnSync(process.env.SDD_PYTHON||'python3',args,{encoding:'utf8'});assert.ok([0,2].includes(p.status),p.stderr);return p;}
run(path.join(__dirname,'stage_reading_fixture.py'),root);
const input=fs.readFileSync(path.join(root,'input.json'));
run(cli,'render','--root',root,'--input',path.join(root,'input.json'),'--output',path.join(root,'v1'));
const url=pathToFileURL(path.join(root,'v1/index.html')).href;
const checks=[],errors=[],remote=[];
function ok(name,value){assert.ok(value,name);checks.push(name);}
async function stage(page,name){await page.locator(`.stage-navigation [data-stage-nav="${name}"]`).click();await page.locator(`[data-stage-panel="${name}"]`).scrollIntoViewIfNeeded();}
async function shot(page,name){await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await page.screenshot({path:path.join(output,name),fullPage:false});}
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.SDD_BROWSER_CHANNEL||'chrome'});
try{
 for(const width of [390,768,1440,1920]){
  const page=await browser.newPage({viewport:{width,height:1080}});
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url());});
  page.on('console',m=>{if(m.type()==='error'&&/Content Security Policy|Refused to/.test(m.text()))errors.push(m.text());});
  await page.goto(url);await stage(page,'Constitution');
  ok(`${width}: rules have separate constraints and commands`,await page.locator('[data-stage-section="constraint"]').isVisible()&&await page.locator('[data-stage-section="command"]').isVisible());
  const command=page.locator('[data-stage-record="command 中文%"]');
  ok(`${width}: exact command source remains readable`,(await command.locator('pre').textContent())==='python3 -m unittest discover -s tests\n# 合成命令，仅供阅读');
  ok(`${width}: documented command stays unexecuted`,(await command.textContent()).includes('未执行')&&await command.locator('button').count()===0);
  const contrast=await page.locator('.stage-command>p:visible,.record-source-state:visible').evaluateAll(nodes=>nodes.map(e=>{
    function rgb(s){return (s.match(/[\d.]+/g)||[]).slice(0,3).map(Number);}
    function lum(c){return c.map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}).reduce((a,c,i)=>a+c*[.2126,.7152,.0722][i],0);}
    let p=e,bg='rgb(255,255,255)';while(p){const c=getComputedStyle(p).backgroundColor;if(c!=='rgba(0, 0, 0, 0)'&&c!=='transparent'){bg=c;break;}p=p.parentElement;}
    const a=lum(rgb(getComputedStyle(e).color)),b=lum(rgb(bg));return(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  }));
  ok(`${width}: small supporting text has readable contrast`,contrast.length>0&&contrast.every(r=>r>=4.5));
  await shot(page,`rules-${width}.png`);
  await command.locator('[data-select]').click();await page.reload();
  ok(`${width}: Unicode source deep link opens detail`,await page.locator('.detail-content[data-id="command 中文%"]' ).isVisible());
  await page.locator('.detail-content[data-id="command 中文%"] h2').focus();
  await page.keyboard.press('Escape');
  ok(`${width}: Escape returns reading space`,!(await page.locator('#detail-pane').isVisible()));
  await stage(page,'Align');
  ok(`${width}: clarification shows problem and actual scope`,await page.locator('[data-stage-section="context"]').isVisible()&&(await page.locator('[data-stage-section="scope"]').textContent()).includes('调用真实治理模型'));
  ok(`${width}: assumption remains unconfirmed`,await page.locator('[data-stage-record="assumption"] .stage-reading-warning').isVisible());
  ok(`${width}: real pending question retains its response route`,await page.locator('[data-stage-panel="Align"] .decision-form').count()===1&&await page.locator('[data-stage-panel="Align"] .decision-form input:checked').count()===0);
  await shot(page,`clarification-${width}.png`);
  await stage(page,'Implement');
  for(const [id,result]of [['run-pass','通过'],['run-fail','失败'],['run-pending','未执行']])ok(`${width}: ${id} retains recorded result`,(await page.locator(`[data-stage-record="${id}"]`).textContent()).includes(result));
  ok(`${width}: actual file mapping is separate from run result`,(await page.locator('[data-stage-section="task-files"]').textContent()).includes('component-1.py'));
  ok(`${width}: failed and unexecuted runs appear in pending work`,(await page.locator('[data-stage-section="issues"]').textContent()).includes('成功结果保护检查')&&(await page.locator('[data-stage-section="issues"]').textContent()).includes('暂停后继续的浏览器检查'));
  await shot(page,`implementation-${width}.png`);
  await page.locator('[data-stage-section="task-files"] [data-select="code1"]').click();
  await page.locator('.detail-content[data-id="code1"] details.evidence').evaluate(e=>e.open=true);
  const source=page.locator('.detail-content[data-id="code1"] .source-link');
  ok(`${width}: actual code source is linked`,await source.getAttribute('href')===pathToFileURL(fs.realpathSync(path.join(root,'component-1.py'))).href);
  if(width===1440){const event=page.waitForEvent('popup');await source.click();const pop=await event;await pop.waitForLoadState();ok('code file opens in genuine browser',(await pop.textContent('body')).includes('Synthetic implementation source'));await pop.close();}
  await stage(page,'Finish');
  ok(`${width}: prepared file is not called delivered`,(await page.locator('[data-stage-record="candidate"]').textContent()).includes('已准备，待交付'));
  ok(`${width}: delivered output names actual receipt`,(await page.locator('[data-stage-record="delivered"]').textContent()).includes('delivery-receipt.json'));
  ok(`${width}: future file remains a plan`,(await page.locator('[data-stage-record="planned"]').textContent()).includes('计划交付')&&!fs.existsSync(path.join(root,'future-guide.md')));
  for(const section of ['usage','limitation','handoff','recovery'])ok(`${width}: delivery has ${section}`,await page.locator(`[data-stage-section="${section}"]`).isVisible());
  ok(`${width}: named owner and steps are clear`,(await page.locator('[data-stage-record="handoff"]').textContent()).includes('演示维护者'));
  ok(`${width}: page does not overflow horizontally`,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await shot(page,`finish-${width}.png`);
  await page.close();
 }
 fs.writeFileSync(path.join(root,'component-1.py'),'changed code');
 run(cli,'update','--root',root,'--previous',path.join(root,'v1'),'--output',path.join(root,'v2'));
 const changed=await browser.newPage({viewport:{width:1440,height:1080}});
 await changed.goto(pathToFileURL(path.join(root,'v2/index.html')).href+'#stage-Implement');
 ok('changed code withdraws current support for PASS',await changed.locator('[data-stage-record="run-pass"] .stage-reading-warning').isVisible());
 ok('historical PASS is preserved',(await changed.locator('[data-stage-record="run-pass"]').textContent()).includes('原记录中的运行结果通过'));
 await stage(changed,'Finish');ok('changed input invalidates dependent prepared output',await changed.locator('[data-stage-record="candidate"] .stage-reading-warning').isVisible());await changed.close();
 const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:1080}});const plain=await nojs.newPage();await plain.goto(url);
 for(const name of ['Constitution','Align','Implement','Finish'])ok(`no JS retains ${name}`,await plain.locator(`[data-stage-reading="${name}"]`).isVisible());await nojs.close();
 ok('all interactions preserve observations',input.equals(fs.readFileSync(path.join(root,'input.json'))));ok('no remote resources',remote.length===0);ok('no browser or CSP errors',errors.length===0);
 fs.writeFileSync(path.join(output,'browser-receipt.json'),JSON.stringify({browser:browser.version(),checks,errors,remote,synthetic:true,root,html_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'v1/index.html'))).digest('hex')},null,2));
 console.log(JSON.stringify({passed:checks.length,browser:browser.version(),output}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
