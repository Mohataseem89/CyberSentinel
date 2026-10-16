import { useEffect, useMemo, useState } from 'react';
import {
  createFileScan,
  getFileScanCapabilities,
  listFileScans,
} from '../services/api';

const verdictLabel = {
  CLEAN_CHECKS_COMPLETED: 'No suspicious indicators found',
  THREAT_DETECTED: 'Threat detected',
  SUSPICIOUS_INDICATORS: 'Suspicious indicators found',
  UNABLE_TO_COMPLETE: 'Analysis incomplete',
};

const verdictClass = {
  CLEAN_CHECKS_COMPLETED: 'bg-emerald-50 text-emerald-800',
  THREAT_DETECTED: 'bg-red-50 text-red-800',
  SUSPICIOUS_INDICATORS: 'bg-amber-50 text-amber-800',
  UNABLE_TO_COMPLETE: 'bg-slate-100 text-slate-700',
};

const indicatorLabels = {
  antivirus_detection: 'Antivirus detection',
  file_hash_reputation_detection: 'File hash reputation detection',

  powershell_reference: 'PowerShell command reference',
  command_shell_reference: 'Command shell reference',
  script_host_reference: 'Windows Script Host reference',
  mshta_reference: 'MSHTA reference',
  rundll32_reference: 'Rundll32 reference',
  certutil_reference: 'CertUtil reference',

  pdf_javascript: 'JavaScript embedded in PDF',
  pdf_javascript_action: 'JavaScript action in PDF',
  pdf_launch_action: 'Launch action in PDF',
  pdf_embedded_file: 'Embedded file in PDF',
  pdf_open_action: 'Automatic open action in PDF',
  pdf_additional_action: 'Additional automatic action in PDF',
  pdf_external_uri: 'External link in PDF',
  pdf_form: 'Interactive PDF form',
  pdf_header_mismatch: 'Invalid or mismatched PDF structure',

  image_signature_mismatch: 'Image format signature mismatch',
  embedded_executable_marker: 'Possible embedded executable marker',

  many_embedded_urls: 'Large number of embedded URLs',
  unusually_high_entropy: 'Unusually encoded or compressed content',

  scripts_present: 'Script content detected',
  embedded_content: 'Embedded external content',
  meta_redirect: 'Automatic page redirect',
  dangerous_uri_scheme: 'Potentially dangerous link scheme',
};

const errorLabels = {
  malware_reputation_unavailable:
    'Malware reputation was unavailable or this file hash is unknown.',
  static_analysis_failed:
    'Local static analysis could not be completed.',
  malware_evidence_unavailable:
    'Malware evidence was unavailable.',
};

function formatIndicator(code) {
  if (!code) {
    return 'Unknown indicator';
  }

  return (
    indicatorLabels[code] ||
    code
      .replaceAll('_', ' ')
      .replace(/\b\w/g, (character) => character.toUpperCase())
  );
}

function formatSeverity(severity) {
  if (!severity) {
    return null;
  }

  return (
    severity.charAt(0).toUpperCase() +
    severity.slice(1).toLowerCase()
  );
}

function ResultExplanation({ job }) {
  if (job.verdict === 'THREAT_DETECTED') {
    return (
      <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-800">
        <strong>Threat evidence was detected.</strong>{' '}
        Do not open or execute this file unless you know exactly what it is
        and have independently verified it.
      </div>
    );
  }

  if (job.verdict === 'SUSPICIOUS_INDICATORS') {
    return (
      <div className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
        <strong>Suspicious characteristics were detected.</strong>{' '}
        This does not automatically prove that the file is malicious, but
        it should be treated with caution.
      </div>
    );
  }

  if (
    job.verdict === 'CLEAN_CHECKS_COMPLETED' &&
    job.malware_status === 'reputation_clean'
  ) {
    return (
      <div className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">
        <strong>No suspicious indicators were found by the available checks.</strong>{' '}
        The file&apos;s SHA-256 reputation was also checked and no known
        detections were reported. This is not a guarantee that the file is
        safe.
      </div>
    );
  }

  if (
    job.verdict === 'CLEAN_CHECKS_COMPLETED' &&
    job.malware_status === 'static_checks_only'
  ) {
    return (
      <div className="mt-3 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
        <strong>No suspicious indicators were found by local static checks.</strong>{' '}
        Malware reputation was unavailable or the file hash was unknown, so
        this result has limited confidence and does not guarantee that the
        file is safe.
      </div>
    );
  }

  if (job.verdict === 'UNABLE_TO_COMPLETE' || job.status === 'FAILED') {
    return (
      <div className="mt-3 rounded-lg bg-slate-100 p-3 text-sm text-slate-700">
        <strong>Analysis could not be completed.</strong>{' '}
        CyberSentinel did not classify this file as safe.
      </div>
    );
  }

  return null;
}

function FileScanResult({ job }) {
  const createdAt = job.created_at
    ? new Date(job.created_at).toLocaleString()
    : null;

  return (
    <article className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <strong className="break-all text-gray-900">
            {job.file_name}
          </strong>

          <p className="mt-1 text-xs text-gray-500">
            {job.file_type || 'file'}
            {' · '}
            {job.mime_type || 'unknown MIME'}
            {job.size_bytes
              ? ` · ${(job.size_bytes / 1024).toFixed(1)} KB`
              : ''}
          </p>

          {createdAt && (
            <p className="mt-1 text-xs text-gray-400">
              {createdAt}
            </p>
          )}
        </div>

        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            verdictClass[job.verdict] ||
            'bg-slate-100 text-slate-700'
          }`}
        >
          {verdictLabel[job.verdict] || job.status}
        </span>
      </div>

      <ResultExplanation job={job} />

      {job.indicators?.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-gray-900">
            Detected indicators
          </h3>

          <ul className="mt-2 space-y-2">
            {job.indicators.map((indicator, index) => (
              <li
                key={`${indicator.code}-${index}`}
                className="rounded-lg border bg-gray-50 px-3 py-2 text-sm text-gray-700"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span>
                    {formatIndicator(indicator.code)}
                  </span>

                  {indicator.severity && (
                    <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
                      {formatSeverity(indicator.severity)}
                    </span>
                  )}
                </div>

                {typeof indicator.detections === 'number' && (
                  <p className="mt-1 text-xs text-gray-500">
                    Reputation detections: {indicator.detections}
                    {typeof indicator.vendors === 'number'
                      ? ` / ${indicator.vendors}`
                      : ''}
                  </p>
                )}

                {typeof indicator.count === 'number' && (
                  <p className="mt-1 text-xs text-gray-500">
                    Occurrences: {indicator.count}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {job.error_code && (
        <p className="mt-3 text-xs text-gray-500">
          {errorLabels[job.error_code] ||
            `Additional limitation: ${job.error_code.replaceAll('_', ' ')}`}
        </p>
      )}
    </article>
  );
}

export default function FileScanPage() {
  const [caps, setCaps] = useState(null);
  const [file, setFile] = useState(null);
  const [consent, setConsent] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState('');

  const maxMB = useMemo(() => {
    if (!caps) {
      return null;
    }

    return Math.round(
      caps.max_bytes / 1024 / 1024,
    );
  }, [caps]);

  const refresh = async () => {
    setLoadingHistory(true);

    try {
      const response = await listFileScans();
      setJobs(response.jobs || []);
    } catch {
      // History refresh errors should not replace errors from explicit
      // upload actions.
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const capabilities =
          await getFileScanCapabilities();

        if (active) {
          setCaps(capabilities);
        }
      } catch (err) {
        if (active) {
          setError(
            err.message ||
              'Unable to load file-analysis capabilities.',
          );
        }
      }

      if (active) {
        await refresh();
      }
    };

    load();

    return () => {
      active = false;
    };
  }, []);

  const submit = async (event) => {
    event.preventDefault();

    const form = event.currentTarget;

    setError('');

    if (!file) {
      setError('Choose a file to analyze.');
      return;
    }

    if (!consent) {
      setError(
        'Please acknowledge the analysis consent before continuing.',
      );
      return;
    }

    if (caps && file.size > caps.max_bytes) {
      setError(
        `File exceeds the ${maxMB} MB limit.`,
      );
      return;
    }

    setBusy(true);

    try {
      await createFileScan(
        file,
        true,
      );

      setFile(null);
      setConsent(false);
      form.reset();

      await refresh();
    } catch (err) {
      setError(
        err.message ||
          'File analysis could not be completed.',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">
          File &amp; HTML Analysis
        </h1>

        <p className="mt-2 max-w-3xl text-gray-600">
          Analyze supported files using non-executing static checks and
          SHA-256 reputation. Uploaded files are treated as untrusted data
          and are never executed.
        </p>
      </header>

      <section
        className="mt-6 rounded-xl border bg-white p-6 shadow-sm"
        aria-labelledby="upload-title"
      >
        <h2
          id="upload-title"
          className="text-lg font-semibold text-gray-900"
        >
          Analyze a file
        </h2>

        <p className="mt-1 text-sm text-gray-600">
          Supported:{' '}
          {caps?.allowed_types?.join(', ') || 'Loading...'}
          {' · '}
          Maximum:{' '}
          {maxMB ? `${maxMB} MB` : '...'}
          {' · '}
          Archives and executable files are not supported.
        </p>

        {!caps?.enabled && caps && (
          <div
            role="status"
            className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800"
          >
            File analysis is currently disabled on the server.
          </div>
        )}

        <form
          onSubmit={submit}
          className="mt-5 space-y-4"
        >
          <div>
            <label
              htmlFor="file-analysis-upload"
              className="mb-2 block text-sm font-medium text-gray-800"
            >
              Choose file
            </label>

            <input
              id="file-analysis-upload"
              aria-label="Choose file to analyze"
              type="file"
              accept=".html,.htm,.txt,.pdf,.png,.jpg,.jpeg,.gif"
              onChange={(event) =>
                setFile(
                  event.target.files?.[0] || null,
                )
              }
              className="block w-full rounded-lg border p-3 text-sm"
            />
          </div>

          {file && (
            <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
              <p>
                <strong>Selected:</strong>{' '}
                <span className="break-all">
                  {file.name}
                </span>
              </p>

              <p className="mt-1 text-xs text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
                {file.type
                  ? ` · ${file.type}`
                  : ''}
              </p>
            </div>
          )}

          <label className="flex items-start gap-3 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) =>
                setConsent(event.target.checked)
              }
              className="mt-1"
            />

            <span>
              I consent to static file analysis. The uploaded original is
              deleted immediately after analysis. Only scan metadata and
              results may be retained for the configured retention period.
            </span>
          </label>

          <button
            type="submit"
            disabled={
              busy ||
              !caps?.enabled ||
              !file ||
              !consent
            }
            className="rounded-lg bg-blue-700 px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy
              ? 'Analyzing...'
              : caps?.enabled
                ? 'Analyze file'
                : 'File analysis disabled'}
          </button>

          {error && (
            <p
              role="alert"
              className="text-sm text-red-700"
            >
              {error}
            </p>
          )}
        </form>

        <div className="mt-5 rounded-lg border bg-slate-50 p-4 text-xs leading-5 text-slate-600">
          <strong className="text-slate-700">
            Important:
          </strong>{' '}
          CyberSentinel performs static analysis and, when available,
          SHA-256 reputation checks. It does not execute uploaded files and
          does not upload the original file to VirusTotal. A result with no
          suspicious indicators is not a guarantee that a file is safe.
        </div>
      </section>

      <section
        className="mt-8"
        aria-labelledby="recent-title"
      >
        <div className="flex items-center justify-between gap-4">
          <h2
            id="recent-title"
            className="text-xl font-semibold text-gray-900"
          >
            Recent scans
          </h2>

          <button
            type="button"
            onClick={refresh}
            disabled={loadingHistory}
            className="text-sm font-medium text-blue-700 disabled:opacity-50"
          >
            {loadingHistory
              ? 'Refreshing...'
              : 'Refresh'}
          </button>
        </div>

        {jobs.length === 0 ? (
          <p className="mt-3 text-sm text-gray-500">
            No recent file scans.
          </p>
        ) : (
          <div className="mt-4 space-y-4">
            {jobs.map((job) => (
              <FileScanResult
                key={job.id}
                job={job}
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}