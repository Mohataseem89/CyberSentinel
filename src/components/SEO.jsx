import { useEffect } from 'react';

const DEFAULT_DESCRIPTION = 'CyberSentinel checks suspicious URLs using local lexical machine learning and optional reputation evidence without opening the submitted webpage.';
const DEFAULT_IMAGE = '/og-cybersentinel.svg';

function upsertMeta(selector, attributes) {
  let element = document.head.querySelector(selector);
  if (!element) {
    element = document.createElement('meta');
    document.head.appendChild(element);
  }
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
}

function upsertLink(rel, href) {
  let element = document.head.querySelector(`link[rel="${rel}"]`);
  if (!element) {
    element = document.createElement('link');
    element.setAttribute('rel', rel);
    document.head.appendChild(element);
  }
  element.setAttribute('href', href);
}

export default function SEO({
  title = 'CyberSentinel — Phishing URL Risk Checker',
  description = DEFAULT_DESCRIPTION,
  path = '/',
  noindex = false,
  schema = null,
}) {
  useEffect(() => {
    const configuredOrigin = import.meta.env.VITE_PUBLIC_SITE_URL?.trim();
    const origin = configuredOrigin || window.location.origin;
    const canonical = new URL(path, origin).toString();
    const image = new URL(DEFAULT_IMAGE, origin).toString();

    document.title = title;
    upsertMeta('meta[name="description"]', { name: 'description', content: description });
    upsertMeta('meta[name="robots"]', { name: 'robots', content: noindex ? 'noindex, nofollow, noarchive' : 'index, follow, max-image-preview:large' });
    upsertMeta('meta[property="og:title"]', { property: 'og:title', content: title });
    upsertMeta('meta[property="og:description"]', { property: 'og:description', content: description });
    upsertMeta('meta[property="og:type"]', { property: 'og:type', content: 'website' });
    upsertMeta('meta[property="og:url"]', { property: 'og:url', content: canonical });
    upsertMeta('meta[property="og:image"]', { property: 'og:image', content: image });
    upsertMeta('meta[name="twitter:card"]', { name: 'twitter:card', content: 'summary_large_image' });
    upsertMeta('meta[name="twitter:title"]', { name: 'twitter:title', content: title });
    upsertMeta('meta[name="twitter:description"]', { name: 'twitter:description', content: description });
    upsertMeta('meta[name="twitter:image"]', { name: 'twitter:image', content: image });
    upsertLink('canonical', canonical);

    let schemaElement = document.head.querySelector('script[data-cybersentinel-schema="true"]');
    if (!schemaElement) {
      schemaElement = document.createElement('script');
      schemaElement.type = 'application/ld+json';
      schemaElement.dataset.cybersentinelSchema = 'true';
      document.head.appendChild(schemaElement);
    }
    schemaElement.textContent = JSON.stringify(schema || {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: 'CyberSentinel',
      url: new URL('/', origin).toString(),
      description: DEFAULT_DESCRIPTION,
    });
  }, [title, description, path, noindex, schema]);

  return null;
}
