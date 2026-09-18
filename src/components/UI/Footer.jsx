import { Link } from 'react-router-dom';
export default function Footer() {
  return <footer className="border-t border-slate-200 bg-white"><div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-slate-600 sm:flex-row sm:items-center sm:justify-between"><p>CyberSentinel provides risk indicators, not guarantees of safety.</p><nav aria-label="Footer" className="flex flex-wrap gap-x-5 gap-y-2"><Link className="hover:text-slate-950" to="/learn">Learn</Link><Link className="hover:text-slate-950" to="/limitations">Limitations</Link><Link className="hover:text-slate-950" to="/privacy">Privacy</Link><a className="hover:text-slate-950" href="https://github.com/Mohataseem89/CyberSentinel" rel="noreferrer" target="_blank">GitHub</a></nav></div></footer>;
}
