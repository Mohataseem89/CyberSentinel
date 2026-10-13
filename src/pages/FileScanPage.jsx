import { useEffect, useMemo, useState } from 'react';
import { createFileScan, getFileScanCapabilities, listFileScans } from '../services/api';

const verdictLabel={CLEAN_CHECKS_COMPLETED:'No known threat detected',THREAT_DETECTED:'Threat detected',SUSPICIOUS_INDICATORS:'Suspicious indicators',UNABLE_TO_COMPLETE:'Analysis incomplete'};
const verdictClass={CLEAN_CHECKS_COMPLETED:'bg-emerald-50 text-emerald-800',THREAT_DETECTED:'bg-red-50 text-red-800',SUSPICIOUS_INDICATORS:'bg-amber-50 text-amber-800',UNABLE_TO_COMPLETE:'bg-slate-100 text-slate-700'};

export default function FileScanPage(){
  const [caps,setCaps]=useState(null),[file,setFile]=useState(null),[consent,setConsent]=useState(false),[jobs,setJobs]=useState([]),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const refresh=async()=>{try{setJobs((await listFileScans()).jobs||[])}catch{/* displayed by explicit actions */}};
  useEffect(()=>{getFileScanCapabilities().then(setCaps).catch(e=>setError(e.message));refresh()},[]);
  const maxMB=useMemo(()=>caps?Math.round(caps.max_bytes/1024/1024):null,[caps]);
  const submit=async(e)=>{e.preventDefault();const form=e.currentTarget;setError('');if(!file||!consent)return setError('Choose a file and acknowledge consent.');if(caps&&file.size>caps.max_bytes)return setError(`File exceeds the ${maxMB} MB limit.`);setBusy(true);try{await createFileScan(file,true);setFile(null);setConsent(false);form.reset();await refresh()}catch(err){setError(err.message)}finally{setBusy(false)}};
  return <main className="mx-auto max-w-5xl px-4 py-10">
    <h1 className="text-3xl font-bold">File & HTML Analysis</h1>
    <p className="mt-2 text-gray-600">Files are treated as untrusted data and are never executed. Results are risk indicators, not a guarantee of safety.</p>
    <section className="mt-6 rounded-xl border bg-white p-6" aria-labelledby="upload-title">
      <h2 id="upload-title" className="text-lg font-semibold">Analyze a file</h2>
      <p className="mt-1 text-sm text-gray-600">Supported: {caps?.allowed_types?.join(', ')||'loading…'} · Maximum: {maxMB?`${maxMB} MB`:'…'} · Archives are not supported.</p>
      <form onSubmit={submit} className="mt-4 space-y-4">
        <input aria-label="Choose file to analyze" type="file" accept=".html,.htm,.txt,.pdf,.png,.jpg,.jpeg,.gif" onChange={e=>setFile(e.target.files?.[0]||null)} className="block w-full rounded border p-3"/>
        {file&&<p className="text-sm text-gray-600">Selected: <strong>{file.name}</strong> · {(file.size/1024).toFixed(1)} KB</p>}
        <label className="flex gap-2 text-sm"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/><span>I consent to malware/static analysis. The uploaded original is deleted immediately after analysis; only scan metadata/results may be retained for the configured retention period.</span></label>
        <button disabled={busy||!caps?.enabled||!file||!consent} className="rounded bg-blue-700 px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50">{busy?'Analyzing…':caps?.enabled?'Analyze file':'File analysis disabled'}</button>
        {error&&<p role="alert" className="text-sm text-red-700">{error}</p>}
      </form>
    </section>
    <section className="mt-8" aria-labelledby="recent-title"><div className="flex items-center justify-between"><h2 id="recent-title" className="text-xl font-semibold">Recent scans</h2><button type="button" onClick={refresh} className="text-sm font-medium text-blue-700">Refresh</button></div>
      {jobs.length===0?<p className="mt-3 text-sm text-gray-500">No recent file scans.</p>:<div className="mt-3 space-y-3">{jobs.map(j=><article key={j.id} className="rounded-xl border bg-white p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div><strong>{j.file_name}</strong><p className="text-xs text-gray-500">{j.file_type||'file'} · {j.mime_type||'unknown MIME'} · {j.size_bytes?`${(j.size_bytes/1024).toFixed(1)} KB`:''}</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold ${verdictClass[j.verdict]||'bg-slate-100 text-slate-700'}`}>{verdictLabel[j.verdict]||j.status}</span></div>
        {j.malware_status==='clean'&&<p className="mt-2 text-sm text-gray-600">Antivirus found no known malware. New or unknown malware may still evade detection.</p>}
        {j.indicators?.length>0&&<div className="mt-3"><p className="text-sm font-medium">Indicators</p><ul className="mt-1 list-disc pl-5 text-sm text-gray-700">{j.indicators.map((x,i)=><li key={`${x.code}-${i}`}>{x.code.replaceAll('_',' ')}{x.severity?` · ${x.severity}`:''}</li>)}</ul></div>}
        {j.error_code&&<p className="mt-2 text-sm text-amber-700">Analysis could not complete: {j.error_code.replaceAll('_',' ')}. The file was not classified as safe.</p>}
      </article>)}</div>}
    </section>
  </main>;
}
