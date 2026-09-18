import fs from 'node:fs';

const rawOrigin = process.env.PUBLIC_SITE_URL || process.env.VITE_PUBLIC_SITE_URL;
if (!rawOrigin) {
  console.error('Set PUBLIC_SITE_URL or VITE_PUBLIC_SITE_URL to an absolute production origin, e.g. https://example.com');
  process.exit(1);
}

let origin;
try {
  origin = new URL(rawOrigin);
} catch {
  console.error('PUBLIC_SITE_URL/VITE_PUBLIC_SITE_URL must be a valid absolute URL.');
  process.exit(1);
}
if (!['http:', 'https:'].includes(origin.protocol)) {
  console.error('Site URL must use http or https.');
  process.exit(1);
}
origin.pathname = '/';
origin.search = '';
origin.hash = '';

const routes = [
  ['/', 'weekly', '1.0'],
  ['/learn', 'monthly', '0.8'],
  ['/limitations', 'monthly', '0.7'],
  ['/privacy', 'monthly', '0.6'],
];

const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${routes.map(([path, freq, priority]) => `  <url><loc>${new URL(path, origin).toString()}</loc><changefreq>${freq}</changefreq><priority>${priority}</priority></url>`).join('\n')}\n</urlset>\n`;
fs.writeFileSync('public/sitemap.xml', xml);
console.log(`Wrote public/sitemap.xml for ${origin.origin}`);
