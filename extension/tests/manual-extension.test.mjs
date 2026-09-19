import test from 'node:test'; import assert from 'node:assert/strict'; import fs from 'node:fs';
const manifest=JSON.parse(fs.readFileSync(new URL('../manifest.json',import.meta.url)));
test('manifest uses least privilege',()=>{assert.deepEqual(manifest.permissions.sort(),['activeTab','storage']);assert.equal(manifest.permissions.includes('tabs'),false);assert.equal(manifest.permissions.includes('webNavigation'),false);assert.equal(manifest.host_permissions.includes('<all_urls>'),false);assert.equal(Boolean(manifest.content_scripts),false);assert.equal(Boolean(manifest.background),false);});
test('extension makes no automatic blocking claim',()=>{assert.equal(/automatic|real-time|blocking/i.test(manifest.description),false);});
