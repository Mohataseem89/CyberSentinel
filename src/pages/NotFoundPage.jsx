import { Link } from 'react-router-dom';
import SEO from '../components/SEO';
export default function NotFoundPage() {
  return <main className="min-h-[70vh] bg-slate-50 px-4 py-20"><SEO title="Page Not Found — CyberSentinel" description="The requested CyberSentinel page was not found." path={window.location.pathname} noindex/><div className="mx-auto max-w-2xl rounded-2xl border border-slate-200 bg-white p-8 text-center"><p className="text-sm font-semibold text-blue-700">404</p><h1 className="mt-2 text-3xl font-bold text-slate-950">Page not found</h1><p className="mt-3 text-slate-600">The address may be outdated or incorrect.</p><Link className="mt-6 inline-block rounded-lg bg-blue-700 px-5 py-3 font-semibold text-white" to="/">Open the URL checker</Link></div></main>;
}
