/* Real Chrome regression. Set SDD_BROWSER_OUTPUT to preserve screenshots and receipts. */
const {chromium} = require('playwright');
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const {spawnSync} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'sdd-workstream-'));
const output = process.env.SDD_BROWSER_OUTPUT ? path.resolve(process.env.SDD_BROWSER_OUTPUT) : root;
fs.mkdirSync(output, {recursive:true});
const cli = path.resolve(__dirname, '../scripts/project_view.py');
function run(...args) {
  const r = spawnSync(process.env.SDD_PYTHON || 'python3', args, {encoding:'utf8'});
  assert.ok([0,2].includes(r.status), r.stderr); return r;
}
run(path.join(__dirname, 'workstream_fixture.py'), root);
run(cli, 'render', '--root', root, '--input', path.join(root, 'input.json'), '--output', path.join(root, 'v1'));
const data = JSON.parse(fs.readFileSync(path.join(root, 'input.json')));
const byId = id => data.items.find(i => i.id === id);
const inputBefore = fs.readFileSync(path.join(root,'input.json'));
const html = path.join(root, 'v1/index.html');
const url = pathToFileURL(html).href;
const checks = [], errors = [], remote = [];
function ok(name, value) { assert.ok(value, name); checks.push(name); }
async function stage(page, name) {
  await page.locator(`.stage-navigation [data-stage-nav="${name}"]`).click();
  await page.locator(`[data-stage-panel="${name}"]`).scrollIntoViewIfNeeded();
}
async function screenshot(page, name) {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await page.screenshot({path:path.join(output, name), fullPage:false});
}
(async () => {
  const browser = await chromium.launch({headless:true, channel:process.env.SDD_BROWSER_CHANNEL || 'chrome'});
  try {
    for (const width of [390, 768, 1440, 1920]) {
      const context = await browser.newContext({viewport:{width,height:1080}});
      const page = await context.newPage();
      page.on('pageerror', e => errors.push(e.message));
      page.on('request', r => {if (/^https?:/.test(r.url())) remote.push(r.url());});
      page.on('console', m=>{if(m.type()==='error' && /Content Security Policy|Refused to/.test(m.text())) errors.push(m.text());});
      await page.goto(url);
      ok(`${width}: starts with overview`, await page.locator('[data-stage-panel="Overview"]').isVisible());
      ok(`${width}: overview keeps evidence pane out of reading area`, !(await page.locator('#detail-pane').isVisible()));
      ok(`${width}: goal and explicit exclusions`, (await page.locator('.work-brief').textContent()).includes('调用真实治理模型'));
      ok(`${width}: bounded counts, no fake percent`, (await page.locator('.work-stats').textContent()).includes('1 / 3') && !(await page.locator('.work-stats').textContent()).includes('%'));
      ok(`${width}: key missing check on overview`, (await page.locator('.work-attention').textContent()).includes('缺少验证记录'));
      await screenshot(page, `overview-${width}.png`);
      await page.getByRole('link', {name:'01 · 需求 需求与验收条件'}).click();
      ok(`${width}: reading path opens Spec`, await page.locator('[data-stage-panel="Spec"]').isVisible());
      ok(`${width}: stage reading uses the full content area`, !(await page.locator('#detail-pane').isVisible()));
      if(width>=1000) ok(`${width}: stage navigation stays above project content`, await page.locator('.lifecycle-section').evaluate(e => e.getBoundingClientRect().bottom <= document.querySelector('#workspace').getBoundingClientRect().top+1));
      ok(`${width}: acceptance immediately readable`, await page.locator('[data-requirement="R1"]').getByText('编号优先；找不到编号时明确提示，不能改用标题匹配。').isVisible());
      await screenshot(page, `requirements-${width}.png`);
      await page.locator('[data-requirement="R1"] [data-select="S1 范围%"]' ).click();
      ok(`${width}: requirement to slice navigation`, await page.locator('[data-stage-panel="Tasks"]').isVisible() && await page.locator('.detail-content[data-id="S1 范围%"]' ).isVisible());
      ok(`${width}: slice execution separate from evidence`, (await page.locator('.detail-content[data-id="S1 范围%"]' ).textContent()).includes('原记录中的任务状态'));
      await page.getByRole('button',{name:'收起详情',exact:true}).click();
      ok(`${width}: inspector can be dismissed`, !(await page.locator('#detail-pane').isVisible()));
      ok(`${width}: dismiss restores a visible reading target`, await page.evaluate(()=>!document.querySelector('#detail-pane').contains(document.activeElement) && document.activeElement.getClientRects().length>0));
      const deep = page.url();
      await page.reload();
      ok(`${width}: Unicode deep link survives reload`, await page.locator('.detail-content[data-id="S1 范围%"]' ).isVisible());
      const actualHash = await page.evaluate(()=>location.hash);
      await page.locator('.detail-content[data-id="S1 范围%"] [data-select="R1"]').click();
      ok(`${width}: slice back to requirement`, await page.locator('[data-stage-panel="Spec"]').isVisible());
      await page.goBack();
      await page.locator('.detail-content[data-id="S1 范围%"]' ).waitFor({state:'visible'});
      ok(`${width}: browser back restores slice`, await page.locator('.detail-content[data-id="S1 范围%"]' ).isVisible());
      await stage(page,'Tasks');
      ok(`${width}: all execution columns exist`, await page.locator('[data-slice-column]').count()===4);
      ok(`${width}: actual blocker visible`, await page.locator('[data-slice="S3"] .work-blocker').isVisible());
      ok(`${width}: dependency points to actual predecessor`, await page.locator('[data-slice="S3"] [data-select="S2"]').count()===1);
      await screenshot(page, `tasks-${width}.png`);
      await stage(page,'Converge');
      if(width<=900) ok(`${width}: current stage remains visible in compact flow navigation`, await page.locator('.lifecycle-section [data-stage-nav="Converge"]').evaluate(e=>{
        const a=e.getBoundingClientRect(),r=e.closest('.lifecycle-section').getBoundingClientRect();return a.left>=r.left-1 && a.right<=r.right+1;
      }));
      ok(`${width}: mixed outcomes remain distinct`, await page.locator('[data-coverage="R1"]').getAttribute('data-verdict')==='COVERED' && await page.locator('[data-coverage="R2"]').getAttribute('data-verdict')==='GAP');
      ok(`${width}: NOT_RUN never shown as pass`, (await page.locator('[data-coverage="R2"]').textContent()).includes('未执行'));
      ok(`${width}: missing coverage for other slice remains visible`, (await page.locator('[data-coverage="R3"]').textContent()).includes('缺少验证记录'));
      ok(`${width}: concrete blocker is readable before expanding details`, await page.locator('[data-coverage="R3"] > td:last-child > ul').getByText(/阻塞：等待暂停与继续路径稳定/).isVisible());
      ok(`${width}: no page horizontal overflow`, await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      if(width===390) ok('390: coverage table scrolls within region', await page.locator('.coverage-scroll').evaluate(e=>e.scrollWidth>e.clientWidth));
      if(width===390) ok('390: horizontal table reading has a visible cue', await page.locator('.table-scroll-hint').isVisible());
      await screenshot(page, `coverage-${width}.png`);
      const more = page.locator('[data-coverage="R3"] .coverage-gap-details');
      await more.locator('summary').click();
      ok(`${width}: complete gap detail can be expanded`, await more.getAttribute('open')!==null && (await more.textContent()).includes('缺少验证记录'));
      await page.locator('[data-coverage="R1"] [data-select="code1"]').click();
      ok(`${width}: trace reaches actual code record`, (await page.locator('.detail-content[data-id="code1"]').textContent()).includes('component-1.py'));
      await page.locator('.detail-content[data-id="code1"] details.evidence').evaluate(e=>e.open=true);
      const source = page.locator('.detail-content[data-id="code1"] .source-link');
      ok(`${width}: original source reachable`, (await source.getAttribute('href'))===pathToFileURL(fs.realpathSync(path.join(root,'component-1.py'))).href);
      if(width===1440) {
        const popupPromise = page.waitForEvent('popup');
        await source.click();
        const popup = await popupPromise;
        await popup.waitForLoadState();
        ok('actual evidence file opens', (await popup.textContent('body')).includes('Synthetic implementation source'));
        await popup.close();
        await page.keyboard.press('Escape');
        ok('Escape dismisses the evidence inspector', !(await page.locator('#detail-pane').isVisible()));
        await page.keyboard.press('Tab');
        ok('keyboard navigation retains visible focus', await page.evaluate(()=>document.activeElement.matches(':focus-visible')));
      }
      await page.goto(url);
      await stage(page, 'Spec');
      await page.goBack();
      await page.locator('[data-stage-panel="Overview"]').waitFor({state:'visible'});
      ok(`${width}: browser back restores initial overview`, await page.locator('[data-stage-panel="Overview"]').isVisible());
      await context.close();
    }
    const partial = structuredClone(data);
    partial.summary = '合成的长项目说明。'.repeat(35);
    const req = partial.items.find(i=>i.id==='R1');
    req.work.acceptance.push('未命中时必须提供明确的界面提示。');
    const reqSource = path.join(root, req.sources[0].path);
    fs.writeFileSync(reqSource, '# Synthetic partial acceptance\n' + req.work.acceptance.join('\n'));
    req.sources[0].sha256 = crypto.createHash('sha256').update(fs.readFileSync(reqSource)).digest('hex');
    fs.writeFileSync(path.join(root,'partial.json'),JSON.stringify(partial));
    run(cli,'render','--root',root,'--input',path.join(root,'partial.json'),'--output',path.join(root,'partial'));
    const partialPage = await browser.newPage({viewport:{width:1440,height:1080}});
    await partialPage.goto(pathToFileURL(path.join(root,'partial/index.html')).href + '#stage-Spec');
    const description = partialPage.locator('#project-description');
    const collapsedHeight = await description.evaluate(e=>e.getBoundingClientRect().height);
    await partialPage.getByRole('button',{name:'展开项目说明',exact:true}).click();
    ok('long description expands with truthful aria state', await partialPage.locator('[data-summary-toggle]').getAttribute('aria-expanded')==='true' && await description.evaluate((e,h)=>e.getBoundingClientRect().height>h,collapsedHeight));
    ok('long description is never rewritten or lost', await description.textContent()===partial.summary);
    await partialPage.getByRole('button',{name:'收起说明',exact:true}).click();
    ok('long description can be collapsed again', await partialPage.locator('[data-summary-toggle]').getAttribute('aria-expanded')==='false');
    ok('partial acceptance exposes individual unverified condition', (await partialPage.locator('[data-requirement="R1"] .acceptance-list li').nth(1).textContent()).includes('缺少通过记录'));
    await stage(partialPage,'Converge');
    ok('a passing slice cannot green an uncovered acceptance condition', await partialPage.locator('[data-coverage="R1"]').getAttribute('data-verdict')==='GAP');
    ok('uncovered acceptance is visible on its requirement row', (await partialPage.locator('[data-coverage="R1"]').textContent()).includes('验收条件 2'));
    await screenshot(partialPage,'partial-acceptance.png');
    await partialPage.close();
    fs.writeFileSync(path.join(root, byId('R1').sources[0].path), 'Requirements changed');
    run(cli,'update','--root',root,'--previous',path.join(root,'v1'),'--output',path.join(root,'v2'));
    const page = await browser.newPage({viewport:{width:1440,height:1080}});
    await page.goto(pathToFileURL(path.join(root,'v2/index.html')).href + '#stage-Converge');
    ok('update invalidates dependent passing chain', await page.locator('[data-coverage="R1"]').getAttribute('data-verdict')==='RECHECK');
    ok('historical PASS preserved with recheck warning', (await page.locator('[data-coverage="R1"]').textContent()).includes('记录或相关来源需核对'));
    await screenshot(page,'stale-coverage.png');
    await page.close();
    const nojs = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:1080}});
    const plain = await nojs.newPage(); await plain.goto(url);
    ok('no JavaScript retains requirements and matrix', await plain.locator('[data-requirement="R1"]').isVisible() && await plain.locator('[data-coverage="R3"]').isVisible());
    await nojs.close();
    const sparse=structuredClone(data);
    sparse.items=sparse.items.filter(i=>!i.work||i.work.type==='brief');delete sparse.next_id;
    fs.writeFileSync(path.join(root,'sparse.json'),JSON.stringify(sparse));
    run(cli,'render','--root',root,'--input',path.join(root,'sparse.json'),'--output',path.join(root,'sparse'));
    for(const width of [390,1440]){
      const emptyPage=await browser.newPage({viewport:{width,height:1080}});
      await emptyPage.goto(pathToFileURL(path.join(root,'sparse/index.html')).href);
      ok(`${width}: absent observations are unrecorded rather than zero completed work`,(await emptyPage.locator('.work-stats strong').allTextContents()).every(t=>t==='未记录'));
      ok(`${width}: missing observation label fits its card`,await emptyPage.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      await emptyPage.close();
    }
    ok('no external resource requests', remote.length===0);
    ok('no browser errors or CSP violations', errors.length===0);
    ok('interaction does not mutate observations', inputBefore.equals(fs.readFileSync(path.join(root,'input.json'))));
    const receipt={browser:browser.version(),root,synthetic:true,checks,errors,remote,
      html_sha256:crypto.createHash('sha256').update(fs.readFileSync(html)).digest('hex'),
      script_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex')};
    fs.writeFileSync(path.join(output,'browser-receipt.json'),JSON.stringify(receipt,null,2));
    console.log(JSON.stringify({checks:checks.length,output,browser:browser.version()}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
