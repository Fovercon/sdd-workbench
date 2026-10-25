/* End-to-end draft composition, version checks and zero automatic approvals. */
const {chromium}=require('playwright');
const fs=require('node:fs'), os=require('node:os'), path=require('node:path'), crypto=require('node:crypto');
const {pathToFileURL}=require('node:url'), {spawnSync}=require('node:child_process');
const assert=require('node:assert/strict');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'sdd-human-gates-'));
const cli=path.resolve(__dirname,'../scripts/project_view.py');
const checker=path.resolve(__dirname,'../scripts/decision_response.py');
const py=process.env.SDD_PYTHON||'python3';
fs.writeFileSync(path.join(root,'plan.md'),'Current plan baseline');
const sources=[{path:'plan.md',line:1,sha256:crypto.createHash('sha256').update('Current plan baseline').digest('hex')}];
const base={view:'progress',kind:'assessment',state:'PENDING_HUMAN',stage:'Plan',sources};
const data={project_id:'human-gates',title:'决策入口回归',scope:'界面与技术校验，不是实际项目审批',captured_at:'2026-10-21',
 lifecycle:{current_stage:'Plan',stage_items:{Plan:'gate'}},items:[
  {...base,id:'gate',label:'设计评审',decision:{id:'D-01',kind:'approval',owner:'测试用户',scope:'只确认测试接口设计。',
    prompt:'是否接受本轮接口设计？',options:[
      {id:'yes',label:'接受当前版本',description:'以此版本为本范围基线。',effect:'APPROVE'},
      {id:'changes',label:'需要修改',description:'请说明修改点。',effect:'REQUEST_CHANGES',requires_note:true},
      {id:'defer',label:'暂缓',description:'保留待确认。',effect:'DEFER'}]}},
  {...base,id:'child',label:'多个视图共用评审入口',decision_ref:'gate'},
  {...base,id:'input',label:'缺少领域资料',decision:{id:'D-02',kind:'input',owner:'测试用户',scope:'只说明资料来源。',prompt:'样例资料位于哪里？'}},
  {...base,id:'legacy',label:'历史待确认记录'}]};
fs.writeFileSync(path.join(root,'input.json'),JSON.stringify(data));
function render(output){const r=spawnSync(py,[cli,'render','--root',root,'--input',path.join(root,'input.json'),'--output',path.join(root,output)],{encoding:'utf8'});assert.ok(r.status===0||r.status===2,r.stderr)}
render('view');
const url=pathToFileURL(path.join(root,'view/index.html')).href;
const checks=[],errors=[],remote=[];
function ok(name,value){assert.ok(value,name);checks.push(name)}
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.SDD_BROWSER_CHANNEL||'chrome'});
try{
 for(const width of [390,768,1440]){
  const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true});
  const page=await context.newPage();
  await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.COPIED_ANSWER=text}}}));
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))remote.push(r.url())});
  await page.goto(url);
  const form=page.locator('.decision-form').first();
  ok(`${width}: shared decision has one form`,await page.locator('.decision-form').count()===2);
  ok(`${width}: no answer preselected`,await page.locator('input:checked').count()===0);
  ok(`${width}: context-specific review label`,await page.locator('.decision-heading .badge').first().textContent()==='待设计评审');
  await form.locator('.decision-tools').evaluate(e=>e.open=true);
  await form.locator('[data-decision-action="generate"]').click();
  ok(`${width}: unanswered question cannot generate`,await form.locator('.decision-output').isHidden());
  await form.locator('input[value="changes"]').check();
  await form.locator('[data-decision-action="generate"]').click();
  ok(`${width}: change option requires explanation`,await form.locator('.decision-output').isHidden());
  await form.locator('[data-decision-note]').fill('请补上超时失败分支。');
  await form.locator('[data-decision-action="copy"]').click();
  const copied=await page.evaluate(()=>window.COPIED_ANSWER);
  ok(`${width}: copy includes scope and exact version`,copied.includes('设计评审')&&copied.includes('D-01')&&/版本 [0-9a-f]{12}/.test(copied)&&!copied.includes('```json'));
  ok(`${width}: draft is clearly unsubmitted`,(await form.locator('.decision-status').textContent()).includes('收到后再处理'));
  ok(`${width}: composing never approves`,await page.locator('.decision-heading .badge').first().getAttribute('data-state')==='PENDING_HUMAN');
  const event=page.waitForEvent('download');await form.locator('[data-decision-action="download"]').click();
  const download=await event;const response=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  ok(`${width}: downloaded answer has stable IDs`,response.decision_id==='D-01'&&response.answer==='changes'&&response.origin==='board_draft');
  fs.writeFileSync(path.join(root,'answer.json'),JSON.stringify(response));
  const checked=spawnSync(py,[checker,'--root',root,'--view',path.join(root,'view'),'--response',path.join(root,'answer.json')],{encoding:'utf8'});
  ok(`${width}: response validates without authority or writes`,checked.status===0&&JSON.parse(checked.stdout).requires_human_authority&&JSON.parse(checked.stdout).writes===false);
  const input=page.locator('.decision-form').nth(1);
  await input.locator('[data-decision-answer]').fill('/example/samples.zip，版本 2026-10');
  await input.locator('.decision-tools').evaluate(e=>e.open=true);
  await input.locator('[data-decision-action="generate"]').click();
  ok(`${width}: input gate accepts free text`,(await input.locator('.decision-output textarea').inputValue()).includes('/example/samples.zip'));
  await page.locator('[data-copy-clarification]').click();
  ok(`${width}: legacy gate asks clarification instead of approval`,(await page.evaluate(()=>window.COPIED_ANSWER)).includes('先说明具体需要我决定什么'));
  await page.locator('.detail-content[data-id="child"] .decision-open').evaluate(e=>e.click());
  ok(`${width}: shared action opens owning question`,(await page.locator('.detail-content[data-id="gate"]').evaluate(e=>!e.hidden)));
  ok(`${width}: no horizontal page overflow`,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.reload();ok(`${width}: reload does not claim saved decision`,await page.locator('input:checked').count()===0);
  await context.close();
 }
 fs.writeFileSync(path.join(root,'plan.md'),'Changed plan');render('stale');
 const stale=await browser.newPage();await stale.goto(pathToFileURL(path.join(root,'stale/index.html')).href);
 ok('stale baselines disable answering',await stale.locator('.decision-form button:enabled').count()===0);
 const nojs=await browser.newContext({javaScriptEnabled:false});const page=await nojs.newPage();await page.goto(url);
 ok('no JS still exposes question and conversation route',(await page.locator('.decision-card').first().textContent()).includes('直接在项目对话中回复'));
 await nojs.close();ok('zero external requests',remote.length===0);ok('zero script errors',errors.length===0);
 console.log(JSON.stringify({passed:checks.length,checks,errors,remote},null,2));
}finally{await browser.close();fs.rmSync(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
