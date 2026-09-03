import { cp, readFile, readdir, writeFile } from 'node:fs/promises';
import { extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const output = new URL('../dist/client/', import.meta.url);
const base = '/haruka-birsday';
const textExtensions = new Set(['.html', '.js', '.css', '.json']);

async function rewrite(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await rewrite(path);
      continue;
    }
    if (!textExtensions.has(extname(entry.name))) continue;
    const source = await readFile(path, 'utf8');
    const updated = source
      .replaceAll('"/_next/', `"${base}/_next/`)
      .replaceAll("'/_next/", `'${base}/_next/`)
      .replaceAll('"/media/', `"${base}/media/`)
      .replaceAll("'/media/", `'${base}/media/`)
      .replaceAll('"/og.png', `"${base}/og.png`)
      .replaceAll("'/og.png", `'${base}/og.png`)
      .replaceAll('http://localhost:3000/og.png', 'https://satoshi05.github.io/haruka-birsday/og.png');
    if (updated !== source) await writeFile(path, updated);
  }
}

await rewrite(fileURLToPath(output));
await cp(new URL('../dist/client/index.html', import.meta.url), new URL('../dist/client/404.html', import.meta.url));
await writeFile(new URL('../dist/client/.nojekyll', import.meta.url), '');
