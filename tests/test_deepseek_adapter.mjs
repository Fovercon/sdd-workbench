import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { apply, name, inject } from '../adapters/deepseek.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const suite = JSON.parse(await readFile(path.join(root, 'suite.json'), 'utf8'));
function provider() {
  let result;
  apply({ skills: { registerProvider(factory) { result = factory({ signal: new AbortController().signal }); } } });
  return result;
}

test('DSH injection and complete catalog preserve all shared skill identities', async () => {
  assert.equal(name, 'sdd-workbench'); assert.deepEqual(inject, ['skills']);
  const rows = await provider().list();
  assert.deepEqual(rows.map(x => x.name), suite.skills);
  for (const row of rows) {
    assert.equal(row.content, undefined);
    assert.equal(row.rank, 600);
    assert.deepEqual(row.invocation, { modelInvocable: true, userInvocable: true });
    assert.equal(row.resourceBase.path, path.join(root, 'skills', row.name));
    assert.equal(row.path, path.join(row.resourceBase.path, 'SKILL.md'));
  }
});

test('Each loaded body is verbatim from the only skills tree and relative references exist', async () => {
  const source = provider();
  for (const row of await source.list()) {
    const loaded = await source.get(row);
    const raw = await readFile(row.path, 'utf8');
    assert.equal(loaded.content, raw.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, ''));
    for (const match of loaded.content.matchAll(/\]\((references\/[^)]+|\.\.\/sdd-[^)]+)\)/g)) {
      await readFile(path.resolve(loaded.resourceBase.path, match[1]));
    }
  }
});

test('Forged locators cannot escape the declared suite', async () => {
  const source = provider(); const [row] = await source.list();
  assert.equal(await source.get({ ...row, locator: '../../plugin.json' }), undefined);
  assert.equal(await source.get({ ...row, name: 'unlisted', locator: 'unlisted' }), undefined);
  assert.equal(await source.get({ ...row, provider: 'other' }), undefined);
});

test('Aborted discovery never reports a completed catalog', async () => {
  const controller = new AbortController(); controller.abort();
  await assert.rejects(provider().list({ signal: controller.signal }), { name: 'AbortError' });
});
