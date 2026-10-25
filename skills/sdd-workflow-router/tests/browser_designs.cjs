/* Run with NODE_PATH pointing to a Playwright installation; no npm install at consumption. */
const {chromium} = require('playwright');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const {pathToFileURL} = require('node:url');
const {spawnSync} = require('node:child_process');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'sdd-design-browser-'));
const cli = path.resolve(__dirname, '../scripts/project_view.py');
const longLabel = '完整中文标签需要保留输入校验失败原因与重试条件';
const definitions = [
  ['flow', `flowchart LR\nA["${longLabel}"] -->|通过校验| B[进入后台]`],
  ['sequence', 'sequenceDiagram\nparticipant A as 界面\nparticipant B as 服务\nA->>B: 提交任务\nalt 冲突\nB-->>A: 409\nelse 接受\nloop 查询进度\nA->>B: GET 状态\nB-->>A: 任务进度\nend\nend'],
  ['state', 'stateDiagram-v2\n[*] --> PENDING\nPENDING --> RUNNING: start\nRUNNING --> PARTIAL: 部分失败\nPARTIAL --> RUNNING: retry'],
  ['class', 'classDiagram\nclass Engine {\n+parse(str text) Unit\n}\nclass Unit {\n+str uid\n}\nEngine ..> Unit : parse'],
  ['er', 'erDiagram\nTASK ||--o{ UNIT : 包含\nTASK {\nstring id PK\n}\nUNIT {\nstring uid PK\n}'],
  ['large', 'flowchart LR\n' + Array.from({length: 24}, (_, i) => `N${i}[单元${i}] --> N${i+1}[单元${i+1}]`).join('\n')],
  ['bad', 'unsupportedDiagram\nthis is not a diagram'],
  ['directive', '%%{init: {"securityLevel":"loose"}}%%\nflowchart LR\nA --> B'],
  ['injection', 'flowchart LR\nA["&lt;img src=x onerror=window.INJECTED=1&gt;"] --> B[正常]']
  ,['中文% id', 'flowchart LR\nA[起点] --> B[终点]']
];
const source = definitions.map(([id, text]) => `## ${id}\n\n\`\`\`mermaid\n${text}\n\`\`\``).join('\n\n');
fs.writeFileSync(path.join(root, 'plan.md'), source);
const digest = crypto.createHash('sha256').update(source).digest('hex');
const sources = [{path: 'plan.md', line: 1, sha256: digest}];
const data = {
  project_id: 'design-browser', title: '设计视图回归', scope: '验证渲染和交互', captured_at: '2026-10-21',
  lifecycle: {current_stage: 'Align', stage_items: {Align: 'align', Plan: 'plan'}},
  items: [
    ...['Align', 'Plan'].map(stage => ({id: stage.toLowerCase(), stage, label: stage,
      view: 'progress', kind: 'assessment', state: 'PENDING_HUMAN', sources})),
    ...definitions.map(([id, mermaid]) => ({id, stage: 'Plan', label: id, view: 'design',
      kind: 'design', state: 'PENDING_HUMAN', sources, mermaid}))
  ]
};
fs.writeFileSync(path.join(root, 'observations.json'), JSON.stringify(data));
const result = spawnSync(process.env.SDD_PYTHON || 'python3', [cli, 'render', '--root', root,
  '--input', path.join(root, 'observations.json'), '--output', path.join(root, 'view')], {encoding:'utf8'});
assert.equal(result.status, 0, result.stderr);
const url = pathToFileURL(path.join(root, 'view/index.html')).href;
const checks = [], failures = [], remote = [];
function ok(name, value) { assert.ok(value, name); checks.push(name); }
(async () => {
  const browser = await chromium.launch({headless: true, channel: process.env.SDD_BROWSER_CHANNEL || 'chrome'});
  try {
    for (const width of [390, 768, 1440, 1920]) {
      const context = await browser.newContext({viewport: {width, height: 1000}, acceptDownloads: true});
      const page = await context.newPage();
      page.on('pageerror', error => failures.push(error.message));
      page.on('request', request => { if (/^https?:/.test(request.url())) remote.push(request.url()); });
      page.on('console', message => { if (message.type()==='error' && /Content Security Policy|Refused to/.test(message.text())) failures.push(message.text()); });
      await page.goto(url);
      await page.waitForFunction(() => document.documentElement.dataset.designsReady === 'true');
      const states = await page.locator('.design-viewer').evaluateAll(elements => Object.fromEntries(elements.map(e => [e.dataset.designId, e.dataset.renderState])));
      for (const id of ['flow', 'sequence', 'state', 'class', 'er', 'large', 'injection', '中文% id']) ok(`${width}: ${id} becomes SVG`, states[id] === 'ready');
      for (const id of ['bad', 'directive']) ok(`${width}: ${id} isolated with source`, states[id] === 'error');
      await page.locator('[data-stage-nav="Plan"]').click();
      await page.locator('.design-index').evaluate(e=>e.open=true);
      await page.locator('.design-index a').last().click();
      ok(`${width}: Unicode design index selects its record`, await page.locator('.detail-content[data-id="中文% id"]').evaluate(e => !e.hidden));
      await page.locator('.design-index').evaluate(e=>e.open=true);
      await page.locator('[data-design-select="flow"]').click();
      ok(`${width}: hidden-stage diagrams refit`, await page.locator('[data-design-id="flow"] svg').evaluate(e => e.getBoundingClientRect().width > 100));
      const viewer = page.locator('[data-design-id="flow"]');
      ok(`${width}: full label preserved`, (await viewer.locator('svg').textContent()).replace(/\s/g,'').includes(longLabel));
      ok(`${width}: page has no horizontal overflow`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1));
      const before = await viewer.locator('svg').evaluate(e => e.getBoundingClientRect().width);
      await viewer.locator('[data-diagram-action="zoom-in"]').click();
      ok(`${width}: zoom changes diagram`, await viewer.locator('svg').evaluate((e, w) => e.getBoundingClientRect().width > w, before));
      await viewer.locator('[data-diagram-action="fit"]').click();
      await viewer.locator('[data-diagram-action="expand"]').click();
      ok(`${width}: accessible enlarged view`, await page.locator('dialog[open]').count() === 1);
      ok(`${width}: approval state survives enlargement`, await page.locator('dialog .badge').getAttribute('data-state') === 'PENDING_HUMAN');
      const downloadEvent = page.waitForEvent('download');
      await page.locator('dialog [data-diagram-action="download"]').click();
      const download = await downloadEvent;
      const exported = fs.readFileSync(await download.path(), 'utf8');
      ok(`${width}: SVG export is standalone`, exported.includes('http://www.w3.org/2000/svg') && exported.includes('<svg') && !exported.includes('<script'));
      await page.keyboard.press('Escape');
      await page.waitForFunction(() => document.activeElement?.dataset.diagramAction === 'expand' && !document.querySelector('dialog').open);
      ok(`${width}: Escape restores focus`, await viewer.locator('[data-diagram-action="expand"]').evaluate(e => document.activeElement === e));
      await viewer.locator('summary').click();
      ok(`${width}: exact source preserved`, await viewer.locator('[data-design-source]').textContent() === definitions[0][1]);
      ok(`${width}: injection never executed`, await page.evaluate(() => !window.INJECTED));
      await page.locator('[data-stage-nav="Align"]').click();
      await page.locator('[data-stage-nav="Plan"]').click();
      ok(`${width}: navigation preserves graphics`, await page.locator('.design-viewer svg').count() === 8);
      await context.close();
    }
    const nojs = await browser.newContext({javaScriptEnabled: false, viewport:{width:390,height:900}});
    const page = await nojs.newPage();
    await page.goto(url);
    ok('no JS: every source remains visible', await page.locator('[data-design-source]:visible').count() === definitions.length);
    await nojs.close();
    ok('offline: zero remote requests', remote.length === 0);
    ok('no page or CSP errors', failures.length === 0);
    console.log(JSON.stringify({passed: checks.length, checks, remote, failures}, null, 2));
  } finally {
    await browser.close();
    fs.rmSync(root, {recursive:true, force:true});
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
