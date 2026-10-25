/* Real local saves, refresh/restart, conflicting tabs and lost-response retries. */
const {chromium}=require('playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {spawn,spawnSync}=require('node:child_process');
const assert=require('node:assert/strict');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'sdd-live-feedback-'));
const scripts=path.resolve(__dirname,'../scripts'),py=process.env.SDD_PYTHON||'python3';
const results=[],errors=[],remote=[];
function ok(name,value){assert.ok(value,name);results.push(name)}
function save(name,value){fs.writeFileSync(path.join(root,name),value)}
const planText='Plan baseline\n<script>window.SOURCE_EXECUTED=true</script>';
save('plan.md',planText);save('module.md','Module baseline');
function ref(name){return {path:name,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,name))).digest('hex')}}
const feedback={id:'feedback',label:'设计图的阅读体验',state:'GAP',view:'progress',kind:'assessment',stage:'Plan',sources:[ref('plan.md')],
 decision:{id:'D-F',kind:'feedback',subject:'设计图的阅读体验',owner:'测试使用者',scope:'只反馈图示表达、排版和操作体验。',prompt:'这版图示还有哪里需要调整？',options:[
  {id:'good',label:'这版可以',description:'图示表达清楚。',effect:'ANSWER'},
  {id:'changes',label:'还要调整',description:'告诉我们需要修改的位置。',effect:'REQUEST_CHANGES',requires_note:true},
  {id:'later',label:'先看看',description:'暂缓反馈。',effect:'DEFER'}]}};
const data={project_id:'local-feedback-browser',title:'本机反馈回归',scope:'隔离测试数据',captured_at:'2026-10-22',
 lifecycle:{current_stage:'Plan',stage_items:{Plan:'feedback'}},items:[feedback,
 {id:'sequence',label:'反馈提交流程',view:'design',kind:'design',state:'GAP',stage:'Plan',sources:[ref('module.md')],decision_ref:'feedback',
  mermaid:'sequenceDiagram\n  actor 用户\n  participant 看板\n  participant 本机服务\n  用户->>看板: 提交反馈\n  看板->>本机服务: 校验并保存\n  本机服务-->>看板: 保存结果\n  看板-->>用户: 更新状态'}]};
save('input.json',JSON.stringify(data));
const rendered=spawnSync(py,['-B',path.join(scripts,'project_view.py'),'render','--root',root,'--input',path.join(root,'input.json'),'--output',path.join(root,'view')],{encoding:'utf8'});
assert.equal(rendered.status,0,rendered.stderr);
const original=fs.readFileSync(path.join(root,'view/snapshot.json'));
async function start(state,port=0){
 const proc=spawn(py,['-B',path.join(scripts,'feedback_server.py'),'--root',root,'--view',path.join(root,'view'),'--state',path.join(root,state),'--port',String(port)],{stdio:['ignore','pipe','pipe']});
 let stderr='';proc.stderr.on('data',d=>stderr+=d);
 const ready=await new Promise((resolve,reject)=>{let buffer='';proc.stdout.on('data',d=>{buffer+=d;if(buffer.includes('\n'))resolve(JSON.parse(buffer.split('\n')[0]))});proc.once('exit',c=>reject(Error(`server exited ${c}: ${stderr}`)))});
 return {...ready,stop:()=>new Promise(resolve=>{proc.once('exit',resolve);proc.kill('SIGTERM')})};
}
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.SDD_BROWSER_CHANNEL||'chrome'});
 let server;
 try{
 for(const width of [390,1440]){
  save('module.md','Module baseline');server=await start('state-'+width);
  const context=await browser.newContext({viewport:{width,height:1050}}),page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith(server.url))remote.push(r.url())});
  await page.goto(server.url+'/#feedback-Plan');
  const card=page.locator('[data-decision-item="feedback"]'),form=card.locator('form'),button=form.locator('[data-decision-action="submit"]');
  await button.waitFor();await page.waitForFunction(()=>!document.querySelector('[data-decision-action="submit"]').disabled);
  ok(`${width}: direct submit replaces copy`,await button.textContent()==='提交反馈');
  ok(`${width}: no preselected feedback`,await form.locator('input:checked').count()===0);
  await page.waitForFunction(()=>document.querySelector('.design-figure svg'));
  ok(`${width}: diagram still renders offline`,await page.locator('.design-figure svg').count()===1);
  await page.goto(server.url+'/#item-feedback');
  await page.locator('#item-feedback .evidence > summary').click();
  const sourceLink=page.locator('#item-feedback .source-link');
  ok(`${width}: served source link uses local HTTP`,(await sourceLink.getAttribute('href')).startsWith('/sources/'));
  const opened=context.waitForEvent('page');await sourceLink.click();const source=await opened;
  await source.waitForLoadState();
  ok(`${width}: source opens in real browser as exact text`,await source.locator('body').innerText()===planText);
  ok(`${width}: source markup never executes`,!(await source.evaluate(()=>window.SOURCE_EXECUTED))&&await source.locator('script').count()===0);
  const sourceUrl=source.url();await source.reload();
  ok(`${width}: source reload remains readable`,await source.locator('body').innerText()===planText);
  await source.close();await page.goto(server.url+'/#feedback-Plan');
  await page.waitForFunction(()=>!document.querySelector('[data-decision-action="submit"]').disabled);
  await form.locator('input[value="changes"]').check();await button.click();
  ok(`${width}: required explanation blocks submit`,await card.locator('.live-feedback-receipt').isHidden());
  const note='时序图中的失败分支再清楚一点。\n<script>window.INJECTED=true</script>';
  await form.locator('[data-decision-note]').fill(note);
  let dropped=false;
  await page.route('**/api/feedback',async route=>{
    if(route.request().method()==='POST'&&!dropped){dropped=true;await route.fetch();await route.abort('failed')}
    else await route.continue();
  });
  await button.click();await page.waitForFunction(()=>document.querySelector('.decision-status').textContent.includes('连接中断'));
  ok(`${width}: lost response preserves unsaved UI and input`,await form.isVisible()&&await form.locator('[data-decision-note]').inputValue()===note);
  await button.click();await card.locator('.live-feedback-receipt').waitFor({state:'visible'});
  ok(`${width}: retry shows committed pending-change status`,(await card.locator('.live-feedback-receipt').textContent()).includes('已收到，待调整'));
  ok(`${width}: saved note is text, never executable`,await card.locator('.live-feedback-note').textContent()===note&&!(await page.evaluate(()=>window.INJECTED)));
  ok(`${width}: engineering state is preserved`,await card.locator('.decision-heading .badge').getAttribute('data-state')==='GAP');
  await page.unroute('**/api/feedback');await page.reload();await card.locator('.live-feedback-receipt').waitFor({state:'visible'});
  ok(`${width}: reload restores receipt without resubmission`,await form.isHidden());
  const state=await page.evaluate(async()=>{const token=document.querySelector('meta[name="sdd-feedback-token"]').content;return (await fetch('/api/feedback',{headers:{'X-SDD-Token':token}})).json()});
  ok(`${width}: lost response retry recorded once`,state.records.feedback.revision===1);
  if(process.env.SDD_SCREENSHOT_DIR){fs.mkdirSync(process.env.SDD_SCREENSHOT_DIR,{recursive:true});await card.screenshot({path:path.join(process.env.SDD_SCREENSHOT_DIR,`${width}-saved.png`)})}
  const other=await context.newPage();await other.goto(server.url+'/#feedback-Plan');await other.locator('.live-feedback-receipt').waitFor({state:'visible'});
  await card.locator('.live-feedback-receipt button').click();await form.locator('input[value="good"]').check();await form.locator('[data-decision-note]').fill('');await button.click();
  await page.waitForFunction(()=>document.querySelector('.live-feedback-receipt').textContent.includes('这版可以'));
  ok(`${width}: editing saved feedback updates receipt`,(await card.locator('.live-feedback-receipt').textContent()).includes('已反馈'));
  await other.locator('.live-feedback-receipt button').click();await other.locator('[data-decision-action="submit"]').click();
  await other.waitForFunction(()=>document.querySelector('.decision-status').textContent.includes('另一处'));
  ok(`${width}: second tab cannot overwrite unseen feedback`,await other.locator('.decision-form').isVisible());await other.close();
  await card.locator('.live-feedback-receipt button').click();await form.locator('input[value="later"]').check();await button.click();
  await page.waitForFunction(()=>document.querySelector('.live-feedback-receipt').textContent.includes('已暂缓反馈'));
  ok(`${width}: deferral has its own status`,(await card.locator('.live-feedback-receipt').textContent()).includes('先看看'));
  const port=Number(new URL(server.url).port);await server.stop();server=await start('state-'+width,port);
  await page.reload();await card.locator('.live-feedback-receipt').waitFor({state:'visible'});
  ok(`${width}: server restart restores persistent record`,(await card.locator('.live-feedback-receipt').textContent()).includes('已暂缓反馈'));
  save('plan.md','Changed source after viewing');
  const changed=await context.newPage();const rejected=await changed.goto(sourceUrl);
  ok(`${width}: changed source is rejected instead of silently shown`,rejected.status()===409&&!(await changed.locator('body').innerText()).includes('Changed source after viewing'));
  await changed.close();save('plan.md',planText);
  save('module.md','Module source changed');await page.reload();await card.locator('.live-feedback-receipt').waitFor({state:'visible'});
  ok(`${width}: stale linked source labels saved feedback as historical`,(await card.locator('.decision-heading .badge').textContent()).includes('待核对')&&await card.locator('.live-feedback-receipt button').isDisabled());
  ok(`${width}: no page overflow`,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  ok(`${width}: immutable snapshot unchanged`,original.equals(fs.readFileSync(path.join(root,'view/snapshot.json'))));
  await context.close();await server.stop();server=null;
 }
 ok('no script errors',errors.length===0);ok('no remote requests',remote.length===0);
 console.log(JSON.stringify({passed:results.length,checks:results,errors,remote},null,2));
 }finally{if(server)await server.stop();await browser.close();fs.rmSync(root,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
