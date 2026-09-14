import { readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
const limit = 500 * 1024, dir = 'dist/assets';
for (const file of await readdir(dir)) { const size = (await stat(join(dir, file))).size; if (file.endsWith('.js') && size > limit) throw new Error(`${file} exceeds the 500 KiB uncompressed JS budget`); }
console.log('Build budget passed.');
