import { useCallback, useEffect, useState } from 'react';
import { Download, RefreshCw, Upload, XCircle } from 'lucide-react';
import {
  cancelBulkJob,
  createBulkJob,
  downloadBulkResults,
  getBulkJob,
  listBulkJobs,
} from '../services/api';
import SEO from '../components/SEO';

const ACTIVE = new Set(['QUEUED', 'RUNNING', 'CANCELLING']);
const DOWNLOADABLE = new Set(['COMPLETED', 'PARTIALLY_COMPLETED', 'CANCELLED']);
const VERDICTS = ['', 'Safe', 'Suspicious', 'Dangerous', 'Unknown'];

function badgeClass(verdict) {
  const styles = {
    Safe: 'bg-emerald-100 text-emerald-800',
    Suspicious: 'bg-amber-100 text-amber-900',
    Dangerous: 'bg-red-100 text-red-800',
    Unknown: 'bg-slate-200 text-slate-700',
  };
  return `inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${styles[verdict] || 'bg-slate-100 text-slate-700'}`;
}

export default function BulkScanPage() {
  const [file, setFile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selected, setSelected] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [page, setPage] = useState(1);
  const [verdict, setVerdict] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const loadSelected = useCallback(async (id, targetPage = page, targetVerdict = verdict) => {
    if (!id) return;
    const detail = await getBulkJob(id, { page: targetPage, perPage: 100, verdict: targetVerdict });
    setSelected(detail);
  }, [page, verdict]);

  const refresh = useCallback(async () => {
    try {
      const data = await listBulkJobs();
      setJobs(data.jobs || []);
      if (selectedId) await loadSelected(selectedId);
      setError('');
    } catch (e) {
      setError(e.message);
    }
  }, [loadSelected, selectedId]);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, 3000);
    return () => window.clearInterval(id);
  }, [refresh]);

  const selectJob = async (id) => {
    setSelectedId(id);
    setPage(1);
    setVerdict('');
    try {
      await loadSelected(id, 1, '');
    } catch (e) {
      setError(e.message);
    }
  };

  const changePage = async (nextPage) => {
    if (!selectedId) return;
    setPage(nextPage);
    try {
      await loadSelected(selectedId, nextPage, verdict);
    } catch (e) {
      setError(e.message);
    }
  };

  const changeVerdict = async (nextVerdict) => {
    if (!selectedId) return;
    setVerdict(nextVerdict);
    setPage(1);
    try {
      await loadSelected(selectedId, 1, nextVerdict);
    } catch (e) {
      setError(e.message);
    }
  };

  const submit = async () => {
    if (!file) return setError('Choose a CSV file first.');
    setBusy(true);
    setError('');
    try {
      const data = await createBulkJob(file);
      setSelectedId(data.job.id);
      setSelected({ ...data, results: [], pagination: null });
      setPage(1);
      setVerdict('');
      setFile(null);
      await refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const pagination = selected?.pagination;

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10">
      <SEO title="Bulk URL Scan — CyberSentinel" path="/bulk" noindex />
      <div className="mx-auto max-w-6xl">
        <h1 className="text-3xl font-bold">Bulk URL scan</h1>
        <p className="mt-2 text-slate-600">Authenticated asynchronous scanning. CSV must contain a <code>url</code> column. Jobs continue after you leave this page.</p>

        <section className="mt-6 rounded-xl border bg-white p-6">
          <div className="flex flex-wrap items-center gap-3">
            <input type="file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <button disabled={!file || busy} onClick={submit} className="rounded-lg bg-blue-700 px-4 py-2 text-white disabled:opacity-50">
              <Upload className="mr-2 inline h-4 w-4" />{busy ? 'Uploading…' : 'Start job'}
            </button>
          </div>
          {error && <p className="mt-3 text-red-700" role="alert">{error}</p>}
        </section>

        <section className="mt-6 rounded-xl border bg-white p-6">
          <div className="flex justify-between"><h2 className="text-xl font-semibold">Your jobs</h2><button onClick={refresh} aria-label="Refresh jobs"><RefreshCw className="h-5 w-5" /></button></div>
          <div className="mt-4 space-y-3">
            {jobs.map((job) => <button key={job.id} onClick={() => selectJob(job.id)} className="block w-full rounded-lg border p-3 text-left hover:bg-slate-50"><strong>{job.status}</strong> — {job.processed}/{job.total} ({job.progress_percent}%) <span className="break-all text-slate-500">{job.id}</span></button>)}
          </div>
        </section>

        {selected && <section className="mt-6 rounded-xl border bg-white p-6">
          <h2 className="break-all text-xl font-semibold">Job {selected.job.id}</h2>
          <p className="mt-2">{selected.job.status}: {selected.job.processed}/{selected.job.total}; successful {selected.job.successful}; failed {selected.job.failed}</p>
          <div className="mt-3 flex flex-wrap gap-3">
            {ACTIVE.has(selected.job.status) && <button onClick={async () => { await cancelBulkJob(selected.job.id); await refresh(); }} className="rounded bg-red-700 px-3 py-2 text-white"><XCircle className="mr-2 inline h-4 w-4" />Cancel</button>}
            {DOWNLOADABLE.has(selected.job.status) && <button onClick={() => downloadBulkResults(selected.job.id)} className="rounded bg-slate-800 px-3 py-2 text-white"><Download className="mr-2 inline h-4 w-4" />Download CSV</button>}
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-2" aria-label="Filter results by verdict">
            {VERDICTS.map((value) => <button key={value || 'all'} onClick={() => changeVerdict(value)} className={`rounded-full border px-3 py-1.5 text-sm ${verdict === value ? 'bg-slate-900 text-white' : 'bg-white text-slate-700'}`}>{value || 'All'}</button>)}
          </div>

          <div className="mt-4 overflow-x-auto rounded-lg border">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-100 text-slate-700"><tr><th className="px-3 py-2">Row</th><th className="px-3 py-2">URL</th><th className="px-3 py-2">Verdict</th><th className="px-3 py-2">Risk</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Error</th></tr></thead>
              <tbody>{(selected.results || []).map((result) => <tr key={result.row} className="border-t"><td className="px-3 py-2">{result.row}</td><td className="max-w-xs truncate px-3 py-2" title={result.url}>{result.url}</td><td className="px-3 py-2">{result.verdict ? <span className={badgeClass(result.verdict)}>{result.verdict}</span> : '—'}</td><td className="px-3 py-2">{result.threat_score ?? '—'}</td><td className="px-3 py-2 font-medium">{result.status}</td><td className="px-3 py-2 text-red-700">{result.error || '—'}</td></tr>)}</tbody>
            </table>
            {(selected.results || []).length === 0 && <p className="p-5 text-center text-slate-500">No results for this filter yet.</p>}
          </div>

          {pagination && <div className="mt-4 flex items-center justify-between gap-3">
            <button disabled={!pagination.has_previous} onClick={() => changePage(page - 1)} className="rounded border px-3 py-2 disabled:opacity-40">Previous</button>
            <span className="text-sm text-slate-600">Page {pagination.page} of {pagination.total_pages} · {pagination.total_items} results</span>
            <button disabled={!pagination.has_next} onClick={() => changePage(page + 1)} className="rounded border px-3 py-2 disabled:opacity-40">Next</button>
          </div>}
        </section>}
      </div>
    </main>
  );
}
