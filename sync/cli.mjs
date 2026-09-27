// Runs the sync locally, writing into site/ instead of S3. Reads the Etsy key from .env in the main
// checkout's root (shared by any worktrees):
//   node sync/cli.mjs

import { mkdir, readdir, rm, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { sync } from './sync.mjs';

const repoDir = join(dirname(fileURLToPath(import.meta.url)), '..');
const siteDir = join(repoDir, 'site');
const gitDir = execFileSync('git', ['-C', repoDir, 'rev-parse', '--path-format=absolute', '--git-common-dir'], { encoding: 'utf8' });
const envFile = join(dirname(gitDir.trim()), '.env');
if (existsSync(envFile)) process.loadEnvFile(envFile);

const dirStore = {
  async list(prefix) {
    const names = await readdir(join(siteDir, prefix)).catch(() => []);
    return names.map((name) => prefix + name);
  },
  async put(key, body) {
    await mkdir(dirname(join(siteDir, key)), { recursive: true });
    await writeFile(join(siteDir, key), body);
  },
  async delete(key) {
    await rm(join(siteDir, key));
  },
};

const result = await sync({
  store: dirStore,
  apiKey: process.env.ETSY_API_KEY,
  sharedSecret: process.env.ETSY_SHARED_SECRET,
  shopName: process.env.SHOP_NAME ?? 'ScalarOrgone',
});
console.log(result);
