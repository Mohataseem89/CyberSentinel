import { AlertOctagon, FlaskConical, ShieldQuestion } from 'lucide-react';
import SEO from '../components/SEO';

export default function LimitationsPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-12">
      <SEO title="CyberSentinel Limitations and Model Caveats" description="Review CyberSentinel's model limitations, evidence gaps, false-positive and false-negative risks, and the actions it intentionally does not perform." path="/limitations" />
      <article className="mx-auto max-w-4xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">Limitations</p>
        <h1 className="mt-2 text-4xl font-bold text-slate-950">What CyberSentinel cannot tell you</h1>
        <p className="mt-4 max-w-3xl text-lg text-slate-600">A URL classification system can reduce uncertainty, but it cannot prove that a destination is harmless. Novel attacks, compromised legitimate sites, dataset shift, missing reputation reports, and benign URLs with unusual patterns can all produce errors.</p>

        <section className="mt-10 grid gap-5 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-6"><ShieldQuestion className="h-7 w-7 text-blue-700"/><h2 className="mt-4 text-xl font-semibold">No webpage execution</h2><p className="mt-2 text-slate-600">The backend intentionally does not open the target page, execute JavaScript, inspect rendered content, or submit forms. This limits SSRF exposure but also means some content-based attacks cannot be detected.</p></div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6"><FlaskConical className="h-7 w-7 text-blue-700"/><h2 className="mt-4 text-xl font-semibold">Model scope</h2><p className="mt-2 text-slate-600">The current model uses a fixed local lexical feature set and probability calibration. Its evaluation describes an immutable domain-grouped holdout, not every real-world traffic population.</p></div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6"><AlertOctagon className="h-7 w-7 text-blue-700"/><h2 className="mt-4 text-xl font-semibold">Evidence can be missing</h2><p className="mt-2 text-slate-600">Third-party reputation data may be unavailable, delayed, rate-limited, or absent for a new URL. Missing evidence is not evidence of safety.</p></div>
        </section>

        <section className="mt-10 rounded-2xl border border-slate-200 bg-white p-7">
          <h2 className="text-2xl font-semibold text-slate-950">Known error modes</h2>
          <ul className="mt-4 list-disc space-y-2 pl-6 text-slate-700">
            <li><strong>False negative:</strong> a malicious link may look lexically ordinary or use a compromised legitimate domain.</li>
            <li><strong>False positive:</strong> a benign tracking, redirect, internationalized, or unusually structured URL may resemble known phishing patterns.</li>
            <li><strong>Novel attack:</strong> attacker behavior can change faster than a trained model or reputation database.</li>
            <li><strong>Population shift:</strong> evaluation metrics from one dataset do not guarantee identical performance on another user population.</li>
            <li><strong>Temporal uncertainty:</strong> the current source dataset does not provide trustworthy collection timestamps, so the model card does not claim a temporal holdout.</li>
          </ul>
        </section>

        <section className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-7">
          <h2 className="text-2xl font-semibold text-slate-950">Do not use a result as a sole authorization decision</h2>
          <p className="mt-3 text-slate-700">Do not use CyberSentinel alone to approve payments, release confidential data, bypass browser warnings, disable endpoint controls, or make high-impact security decisions. Use independent verification and layered security controls.</p>
        </section>
      </article>
    </main>
  );
}
