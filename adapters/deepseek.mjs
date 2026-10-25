/** Read-only DSH skill provider. All instructions/resources stay in ../skills/. */
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const name = 'sdd-workbench';
export const inject = ['skills'];
const root = fileURLToPath(new URL('../', import.meta.url));
const providerName = 'sdd-workbench';

async function names(signal) {
  const suite = JSON.parse(await readFile(path.join(root, 'suite.json'), { encoding: 'utf8', signal }));
  if (!Array.isArray(suite.skills) || !suite.skills.length ||
      suite.skills.some(value => typeof value !== 'string' || !/^sdd-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value)) ||
      new Set(suite.skills).size !== suite.skills.length) throw Error('Invalid suite skill list');
  return suite.skills;
}

async function definition(skill, signal) {
  const directory = path.join(root, 'skills', skill);
  const file = path.join(directory, 'SKILL.md');
  const text = await readFile(file, { encoding: 'utf8', signal });
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/.exec(text);
  if (!match) throw Error(`Missing frontmatter: ${skill}`);
  const value = key => {
    const raw = new RegExp(`^${key}:\\s*(.+)$`, 'm').exec(match[1])?.[1].trim();
    if (!raw) throw Error(`Missing ${key}: ${skill}`);
    return raw.startsWith('"') ? JSON.parse(raw) : raw.startsWith("'") && raw.endsWith("'")
      ? raw.slice(1, -1).replaceAll("''", "'") : raw;
  };
  const description = value('description');
  if (value('name') !== skill || typeof description !== 'string' || description.length > 1024)
    throw Error(`Invalid skill metadata: ${skill}`);
  return { name: skill, description, path: file, content: match[2],
    invocation: { modelInvocable: true, userInvocable: true }, source: 'bundled',
    provider: providerName, resourceBase: { kind: 'directory', path: directory } };
}

export function apply(ctx) {
  ctx.skills.registerProvider(() => ({
    name: providerName,
    async list({ signal } = {}) {
      return Promise.all((await names(signal)).map(async skill => {
        const { content, ...summary } = await definition(skill, signal);
        return { ...summary, rank: 600, locator: skill };
      }));
    },
    async get(candidate, { signal } = {}) {
      if (candidate.provider !== providerName || candidate.locator !== candidate.name ||
          !(await names(signal)).includes(candidate.name)) return undefined;
      return definition(candidate.name, signal);
    },
  }));
}
