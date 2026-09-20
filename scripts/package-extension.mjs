import fs from 'node:fs'; import path from 'node:path'; import {execFileSync} from 'node:child_process';
const origin=(process.env.EXTENSION_API_ORIGIN||'').replace(/\/$/,'');
if(!/^https:\/\/[^/]+$/.test(origin)) throw new Error('EXTENSION_API_ORIGIN must be an exact HTTPS origin, e.g. https://api.example.com');
const src='extension', out='dist-extension', zip='cybersentinel-extension.zip';
fs.rmSync(out,{recursive:true,force:true}); fs.cpSync(src,out,{recursive:true});
for(const file of ['manifest.json','utils/api.js']){const p=path.join(out,file);fs.writeFileSync(p,fs.readFileSync(p,'utf8').replaceAll('__CYBERSENTINEL_API_ORIGIN__',origin));}
console.log(`Prepared ${out} for ${origin}. Zip this directory for store submission.`);
