import { BookOpen, Database, ShieldCheck, TriangleAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import SEO from '../components/SEO';

export default function LearnPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-12">
      <SEO
        title="Learn How CyberSentinel Checks Suspicious URLs"
        description="Learn how CyberSentinel combines lexical machine learning and optional VirusTotal reputation evidence, what each verdict means, and how to verify suspicious links safely."
        path="/learn"
        schema={{
          '@context': 'https://schema.org',
          '@type': 'Article',
          headline: 'How CyberSentinel checks suspicious URLs',
          description: 'A plain-language explanation of CyberSentinel phishing URL analysis, evidence, verdicts, and safe follow-up steps.',
          author: { '@type': 'Organization', name: 'CyberSentinel' },
        }}
      />
      <article className="mx-auto max-w-4xl">
        <header className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">Learn</p>
          <h1 className="mt-2 text-4xl font-bold text-slate-950">How CyberSentinel checks a suspicious link</h1>
          <p className="mt-4 text-lg text-slate-600">CyberSentinel is designed to provide a cautious risk signal, not a promise that a website is safe. The backend analyses the submitted URL and may use an existing reputation report, but it does not open or execute the submitted webpage.</p>
        </header>

        <section className="mt-10 grid gap-5 md:grid-cols-2" aria-label="Detection approach">
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <ShieldCheck className="h-7 w-7 text-blue-700" />
            <h2 className="mt-4 text-xl font-semibold text-slate-950">1. URL-only machine learning</h2>
            <p className="mt-2 text-slate-600">The model extracts local lexical features from the URL text. That means it can notice patterns that often occur in phishing links without visiting the destination.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <Database className="h-7 w-7 text-blue-700" />
            <h2 className="mt-4 text-xl font-semibold text-slate-950">2. Reputation evidence</h2>
            <p className="mt-2 text-slate-600">When VirusTotal is configured and has usable evidence, CyberSentinel can combine that independent reputation signal with the model score. Missing reputation data is treated as unavailable, not as proof that a link is safe.</p>
          </div>
        </section>

        <section className="mt-10 rounded-2xl border border-slate-200 bg-white p-7">
          <BookOpen className="h-7 w-7 text-blue-700" />
          <h2 className="mt-4 text-2xl font-semibold text-slate-950">What the verdicts mean</h2>
          <dl className="mt-5 space-y-5 text-slate-700">
            <div><dt className="font-semibold text-emerald-800">Safe</dt><dd className="mt-1">Current configured evidence does not show elevated risk. It is still not a guarantee of safety.</dd></div>
            <div><dt className="font-semibold text-amber-800">Suspicious</dt><dd className="mt-1">One or more signals justify extra caution. Do not enter passwords, payment details, or sensitive information until you independently verify the destination.</dd></div>
            <div><dt className="font-semibold text-red-800">Dangerous</dt><dd className="mt-1">Strong risk evidence is present. Avoid opening the link or submitting information, and verify the request through a trusted channel.</dd></div>
            <div><dt className="font-semibold text-slate-800">Unknown</dt><dd className="mt-1">CyberSentinel does not have enough corroborated evidence to make a stronger classification. Unknown must not be interpreted as safe.</dd></div>
          </dl>
        </section>

        <section className="mt-10 rounded-2xl border border-amber-200 bg-amber-50 p-7">
          <TriangleAlert className="h-7 w-7 text-amber-800" />
          <h2 className="mt-4 text-2xl font-semibold text-slate-950">Safer verification steps</h2>
          <ul className="mt-4 list-disc space-y-2 pl-6 text-slate-700">
            <li>Do not follow a suspicious link just to test whether it looks legitimate.</li>
            <li>Open the organization through a known bookmark or type its official domain yourself.</li>
            <li>Confirm urgent account, payment, or password requests through a separate trusted channel.</li>
            <li>Do not paste passwords, authentication tokens, private reset links, or confidential URLs into the scanner.</li>
          </ul>
        </section>

        <p className="mt-10 text-slate-600">For important constraints, dataset caveats, and false-positive/false-negative risks, read the <Link className="font-semibold text-blue-700 underline" to="/limitations">limitations page</Link>. For data handling, read the <Link className="font-semibold text-blue-700 underline" to="/privacy">privacy page</Link>.</p>
      </article>
    </main>
  );
}
