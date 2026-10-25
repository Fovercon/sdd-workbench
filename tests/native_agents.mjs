/** Opt-in upstream integration: node tests/native_agents.mjs /isolated/npm/prefix [pi-package-dir]. */
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, realpath, readdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root = fileURLToPath(new URL('../', import.meta.url));
const prefix = path.resolve(process.argv[2]);
const require = createRequire(path.join(prefix, 'package.json'));
const load = name => import(pathToFileURL(require.resolve(name)).href);
const names = JSON.parse(await readFile(path.join(root, 'suite.json'), 'utf8')).skills.sort();
const scratch = await mkdtemp(path.join(tmpdir(), 'sdd-native-agents-'));
const home = path.join(scratch, 'home');
const shared = path.join(home, '.agents/skills');
const run = (command, args, env = {}) => {
  const childEnv = { ...process.env, ...env };
  // Let upstream fall back to the test-only os.homedir stub, without assigning HOME.
  delete childEnv.HOME;
  return execFileSync(command, args, {
    cwd: scratch, env: childEnv, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
  });
};
try {
  await mkdir(home);
  const packed = JSON.parse(run('npm', ['pack', root, '--dry-run', '--json']))[0];
  const packedPaths = new Set(packed.files.map(file => file.path));
  assert.ok(![...packedPaths].some(file => /__pycache__|\.py[cod]$|\.sqlite3/.test(file)));
  for (const file of ['adapters/deepseek.mjs', 'suite.json', 'cordis.patch.yml']) assert.ok(packedPaths.has(file));
  const shim = path.join(scratch, 'home-shim.mjs');
  await writeFile(shim, `import os from 'node:os';\nimport {syncBuiltinESMExports} from 'node:module';\nos.homedir=()=>process.env.SDD_TEST_HOME;\nsyncBuiltinESMExports();\n`);
  run(process.execPath, ['--import', shim, path.join(prefix, 'node_modules/skills/bin/cli.mjs'),
    'add', root, '-g', '-a', 'codex', 'hermes-agent', 'zcode', 'opencode', 'pi', '-y'], {
    SDD_TEST_HOME: home, HERMES_HOME: path.join(home, '.hermes'),
    XDG_CONFIG_HOME: path.join(home, '.config'), DISABLE_TELEMETRY: '1',
  });
  assert.deepEqual((await readdir(shared)).sort(), names);
  // All resources must survive installation, including scripts, templates and vendor bytes.
  async function compare(from, to) {
    for (const item of await readdir(from, { withFileTypes: true })) {
      if (item.name === '__pycache__' || item.name.endsWith('.pyc')) continue;
      const a = path.join(from, item.name), b = path.join(to, item.name);
      if (item.isDirectory()) await compare(a, b);
      else {
        assert.ok(packedPaths.has(path.relative(root, a).split(path.sep).join('/')), a);
        assert.deepEqual(await readFile(b), await readFile(a), a);
      }
    }
  }
  for (const name of names) {
    const canonical = await realpath(path.join(shared, name));
    for (const target of ['.hermes/skills', '.zcode/skills'])
      assert.equal(await realpath(path.join(home, target, name)), canonical);
    await compare(path.join(root, 'skills', name), canonical);
  }
  console.log('skills@1.7.4: 12 complete canonical skills; Hermes/ZCode links resolve to same bytes');

  const { Context } = await load('@deepseek-ai/cordis');
  const { SkillRegistry } = await load('@deepseek-ai/dsh-skill');
  const fsProvider = await load('@deepseek-ai/dsh-skill-filesystem');
  const adapter = await import(pathToFileURL(path.join(root, 'adapters/deepseek.mjs')).href);
  for (const [label, provider, config] of [
    ['bundled adapter', adapter, {}],
    ['shared filesystem', fsProvider, { includeDefaultRoots: false, customSkillDirs: [shared], watch: false }],
  ]) {
    const ctx = new Context();
    const registryFiber = ctx.plugin(SkillRegistry); await registryFiber;
    const providerFiber = ctx.plugin(provider, config); await providerFiber;
    try {
      const catalog = await ctx.skills.list();
      assert.deepEqual(catalog.map(s => s.name).sort(), names);
      for (const skill of catalog) {
        const loaded = await ctx.skills.get(skill.name);
        const text = await readFile(loaded.path, 'utf8');
        const body = /^---\r?\n[\s\S]*?\r?\n---\r?\n([\s\S]*)$/.exec(text)[1];
        assert.equal(loaded.content, label === 'shared filesystem' ? body.trim() : body);
        assert.equal(loaded.resourceBase.kind, 'directory');
      }
      console.log(`DeepSeek 0.2.1-rc.2 ${label}: 12 discovered and bodies verified`);
    } finally { await providerFiber.dispose(); await registryFiber.dispose(); }
  }

  if (process.argv[3]) {
    const pi = path.resolve(process.argv[3]);
    const sharedProbe = path.join(scratch, 'pi-shared.mjs');
    await writeFile(sharedProbe, `import assert from 'node:assert/strict';
import {DefaultResourceLoader} from ${JSON.stringify(pathToFileURL(path.join(pi, 'dist/core/resource-loader.js')).href)};
const loader=new DefaultResourceLoader({cwd:${JSON.stringify(scratch)},agentDir:${JSON.stringify(path.join(home, '.pi/agent'))},noExtensions:true,noPromptTemplates:true,noThemes:true});
await loader.reload();
assert.deepEqual(loader.getSkills().skills.map(s=>s.name).sort(),${JSON.stringify(names)});
assert.deepEqual(loader.getSkills().diagnostics,[]);
`);
    run(process.execPath, ['--import', shim, sharedProbe], { SDD_TEST_HOME: home,
      PI_CODING_AGENT_DIR: path.join(home, '.pi/agent') });
    console.log('Pi shared directory: 12 skills discovered with isolated home');
    const piDir = path.join(scratch, 'pi');
    run(process.execPath, [path.join(pi, 'dist/cli.js'), 'install', root], { PI_CODING_AGENT_DIR: piDir });
    const { DefaultResourceLoader } = await import(pathToFileURL(path.join(pi, 'dist/core/resource-loader.js')).href);
    const loader = new DefaultResourceLoader({ cwd: scratch, agentDir: piDir,
      noExtensions: true, noPromptTemplates: true, noThemes: true });
    await loader.reload();
    const result = loader.getSkills();
    assert.deepEqual(result.skills.map(s => s.name).sort(), names);
    assert.deepEqual(result.diagnostics, []);
    console.log('Pi native package install/resource loader: 12 skills, no diagnostics');
  }
} finally { await rm(scratch, { recursive: true, force: true }); }
