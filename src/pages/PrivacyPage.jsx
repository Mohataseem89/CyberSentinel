import { LockKeyhole, ScanLine, UserRoundCheck } from 'lucide-react';
import SEO from '../components/SEO';

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-12">
      <SEO title="CyberSentinel Privacy and Data Handling" description="Understand what CyberSentinel processes when you scan a URL, when scan history is retained, and how feedback and account data are handled." path="/privacy" />
      <article className="mx-auto max-w-4xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">Privacy</p>
        <h1 className="mt-2 text-4xl font-bold text-slate-950">Data handling in CyberSentinel</h1>
        <p className="mt-4 max-w-3xl text-lg text-slate-600">CyberSentinel is built to minimize unnecessary URL retention. This page describes the behavior implemented in the current source code; production operators are responsible for keeping deployment settings and third-party disclosures consistent with it.</p>

        <section className="mt-10 grid gap-5 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-6"><ScanLine className="h-7 w-7 text-blue-700"/><h2 className="mt-4 text-xl font-semibold">Scanning</h2><p className="mt-2 text-slate-600">A submitted URL is processed to calculate the result. When VirusTotal is configured, CyberSentinel performs a lookup of an existing VirusTotal report using the URL-derived report identifier; it does not submit the URL for a new VirusTotal scan. The server does not fetch the submitted webpage itself.</p></div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6"><UserRoundCheck className="h-7 w-7 text-blue-700"/><h2 className="mt-4 text-xl font-semibold">History</h2><p className="mt-2 text-slate-600">Persistent scan history is only written for an authenticated user when the request explicitly opts into retention. Stored history uses a URL hash plus a redacted domain form instead of the raw URL.</p></div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6"><LockKeyhole className="h-7 w-7 text-blue-700"/><h2 className="mt-4 text-xl font-semibold">Private surfaces</h2><p className="mt-2 text-slate-600">Dashboard, history, authentication, feedback workflow, QR scanning, and admin routes are excluded from search indexing through application metadata and crawler rules.</p></div>
        </section>

        <section className="mt-10 space-y-8 rounded-2xl border border-slate-200 bg-white p-7 text-slate-700">
          <div><h2 className="text-2xl font-semibold text-slate-950">Accounts</h2><p className="mt-2">Registered accounts store the username, email address, a one-way password hash, role, account status, and creation time. Passwords should never be logged or stored in plaintext.</p></div>
          <div><h2 className="text-2xl font-semibold text-slate-950">User feedback</h2><p className="mt-2">When you submit a URL report, the current application stores the reported URL, classification fields, description, review status, and user identifier when authenticated. Approved feedback does not automatically retrain the model; it requires offline human curation.</p></div>
          <div><h2 className="text-2xl font-semibold text-slate-950">Third-party reputation checks</h2><p className="mt-2">VirusTotal is an optional integration. When enabled, CyberSentinel requests an existing VirusTotal URL report using a URL-derived identifier. VirusTotal operates under its own terms and privacy practices. Deployments that enable additional providers must disclose them before use.</p></div>
          <div><h2 className="text-2xl font-semibold text-slate-950">Sensitive data</h2><p className="mt-2">Do not submit passwords, API keys, authentication tokens, private document links, password-reset links, or confidential intranet URLs. A security scanner is not a secret-storage service.</p></div>
          <div><h2 className="text-2xl font-semibold text-slate-950">Browser extension</h2><p className="mt-2">The CyberSentinel extension operates in manual mode. It may read the active tab URL when you open the extension, but it does not send that URL until you choose Check URL. It does not collect browsing history, page contents, cookies, passwords, forms, or unrelated tabs. Before transmission it removes URL fragments and redacts common sensitive query values. The extension stores only the last checked domain, verdict, and timestamp locally.</p></div>
          <div><h2 className="text-2xl font-semibold text-slate-950">Bulk scans</h2><p className="mt-2">Authenticated bulk jobs temporarily retain normalized submitted URLs while queued or processing so a worker can analyze them. Completed or failed rows clear the working URL and retain a redacted display form plus the result. Jobs expire according to the configured retention period; operators must align backups and infrastructure logs with that policy.</p></div>
          <div><h2 className="text-2xl font-semibold text-slate-950">Operator responsibility</h2><p className="mt-2">Retention schedules, backups, infrastructure logs, database access, deletion workflows, and regional legal requirements depend on the deployment. Operators should document these choices and avoid claiming stronger privacy guarantees than their actual hosting configuration provides.</p></div>
        </section>
      </article>
    <section className="mt-8"><h2 className="text-xl font-semibold">File analysis</h2><p className="mt-2 text-gray-700">File analysis requires explicit consent. Uploads are treated as untrusted, stored privately under randomized names only while queued/scanning, and deleted immediately after analysis attempts. Scan metadata and sanitized results may be retained for the configured retention period. Raw file contents are not logged or exposed through public URLs. HTML analysis is static and does not execute scripts or load remote resources.</p></section>
    </main>
  );
}
