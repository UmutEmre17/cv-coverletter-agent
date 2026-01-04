import { useMemo, useState } from "react";

type AgentResponse = {
  final?: {
    cover_letter?: string;
    issues?: string[];
    improvements?: string[];
    evidence_map?: { claim: string; evidence_chunk_ids: string[] }[];
  };
  fit?: {
    fit_score?: number;
    matched?: string[];
    missing?: string[];
    notes?: string[];
  };
  requirements?: {
    title?: string;
    company?: string;
    location_type?: string;
    seniority?: string;
  };
};

export default function App() {
  const [jobText, setJobText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResponse | null>(null);

  const [cvFile, setCvFile] = useState<File | null>(null);
  const [cvStatus, setCvStatus] = useState<string>("");

  const coverLetter = result?.final?.cover_letter || "";
  const fitScore = result?.fit?.fit_score ?? null;

  const fitLabel = useMemo(() => {
    if (fitScore === null) return "";
    if (fitScore >= 75) return "Strong fit";
    if (fitScore >= 50) return "Medium fit";
    return "Low fit";
  }, [fitScore]);

  async function handleUploadCV() {
    if (!cvFile) return;

    setCvStatus("Uploading...");
    try {
      const form = new FormData();
      form.append("file", cvFile);

      const res = await fetch("http://127.0.0.1:8000/ingest-cv", {
        method: "POST",
        body: form,
      });

      const data = await res.json();

      if (!res.ok) {
        setCvStatus(`Upload failed: ${data?.detail || "unknown error"}`);
        return;
      }

      setCvStatus(`✅ CV indexed: ${data.chunks} chunks • ${data.chars} chars`);
    } catch (e) {
      console.error(e);
      setCvStatus("Upload failed: backend not reachable");
    }
  }

  async function handleGenerate() {
    if (!jobText.trim()) return;

    // CV upload edilmeden generate edilmesin
    if (!cvStatus.startsWith("✅")) {
      alert("Önce CV upload edip indexle kanka 🙂");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/generate-from-job-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_text: jobText }),
      });

      const data = await res.json();
      if (!res.ok) {
        alert(data?.detail || "Backend error");
        return;
      }
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Backend not reachable");
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (!coverLetter) return;
    await navigator.clipboard.writeText(coverLetter);
    alert("Copied ✅");
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">CV Cover Letter Agent</h1>
            <p className="text-zinc-400 mt-1">
              Upload CV → paste job → generate tailored cover letter + fit insights.
            </p>
          </div>

          {fitScore !== null && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3 min-w-[220px]">
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-400">Fit score</span>
                <span className="text-sm font-semibold">{fitLabel}</span>
              </div>
              <div className="mt-2 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-2 bg-emerald-500"
                  style={{ width: `${Math.max(0, Math.min(100, fitScore))}%` }}
                />
              </div>
              <div className="mt-2 text-2xl font-bold">{fitScore}%</div>
            </div>
          )}
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* LEFT: inputs */}
          <div className="space-y-6">
            {/* CV Upload */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
              <h2 className="text-lg font-semibold mb-3">1) Upload CV (PDF)</h2>

              <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-zinc-200
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-xl file:border-0
                    file:text-sm file:font-semibold
                    file:bg-zinc-800 file:text-white
                    hover:file:bg-zinc-700"
                />

                <button
                  onClick={handleUploadCV}
                  disabled={!cvFile}
                  className="w-full sm:w-auto px-4 py-2 rounded-xl font-semibold
                    bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50"
                >
                  Upload & Index
                </button>
              </div>

              {cvStatus && (
                <p className="mt-3 text-sm text-zinc-300">
                  {cvStatus}
                </p>
              )}
            </div>

            {/* Job Text */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold">2) Job Description</h2>
                <span className="text-xs text-zinc-400">
                  {jobText.length} chars
                </span>
              </div>

              <textarea
                className="w-full h-[320px] p-3 rounded-xl bg-zinc-950 text-white
                  border border-zinc-800 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                placeholder="Paste job description here..."
                value={jobText}
                onChange={(e) => setJobText(e.target.value)}
              />

              <button
                onClick={handleGenerate}
                disabled={loading}
                className="mt-4 w-full py-2 rounded-xl font-semibold
                  bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
              >
                {loading ? "Generating..." : "Generate Cover Letter"}
              </button>

              <p className="mt-3 text-xs text-zinc-400">
                Tip: Çok uzun metinlerde JSON error alırsan, düz metin gibi gönder; UI otomatik string olarak yolluyor.
              </p>
            </div>
          </div>

          {/* RIGHT: output */}
          <div className="space-y-6">
            {/* Cover letter */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
              <div className="flex items-center justify-between gap-3 mb-3">
                <h2 className="text-lg font-semibold">Output</h2>
                <div className="flex gap-2">
                  <button
                    onClick={handleCopy}
                    disabled={!coverLetter}
                    className="px-3 py-2 rounded-xl text-sm font-semibold
                      bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50"
                  >
                    Copy
                  </button>
                </div>
              </div>

              {!result && (
                <p className="text-zinc-400">
                  Output burada görünecek. (Önce CV upload + index)
                </p>
              )}

              {coverLetter && (
                <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4">
                  <pre className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-100">
                    {coverLetter}
                  </pre>
                </div>
              )}
            </div>

            {/* Issues & Improvements */}
            {result?.final && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
                  <h3 className="font-semibold mb-2">Issues</h3>
                  <ul className="text-sm text-zinc-300 space-y-2 list-disc list-inside">
                    {(result.final.issues || []).slice(0, 6).map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                    {(result.final.issues || []).length === 0 && (
                      <li className="text-zinc-500 list-none">No issues reported.</li>
                    )}
                  </ul>
                </div>

                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
                  <h3 className="font-semibold mb-2">Improvements</h3>
                  <ul className="text-sm text-zinc-300 space-y-2 list-disc list-inside">
                    {(result.final.improvements || []).slice(0, 6).map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                    {(result.final.improvements || []).length === 0 && (
                      <li className="text-zinc-500 list-none">No improvements suggested.</li>
                    )}
                  </ul>
                </div>
              </div>
            )}

            {/* Matched / Missing */}
            {result?.fit && (
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
                <h3 className="font-semibold mb-3">Fit breakdown</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-zinc-400 mb-2">Matched</p>
                    <div className="flex flex-wrap gap-2">
                      {(result.fit.matched || []).slice(0, 12).map((t, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-1 rounded-full bg-emerald-900/40 border border-emerald-800 text-emerald-200"
                        >
                          {t}
                        </span>
                      ))}
                      {(result.fit.matched || []).length === 0 && (
                        <span className="text-xs text-zinc-500">—</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-zinc-400 mb-2">Missing</p>
                    <div className="flex flex-wrap gap-2">
                      {(result.fit.missing || []).slice(0, 12).map((t, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-1 rounded-full bg-rose-900/30 border border-rose-800 text-rose-200"
                        >
                          {t}
                        </span>
                      ))}
                      {(result.fit.missing || []).length === 0 && (
                        <span className="text-xs text-zinc-500">—</span>
                      )}
                    </div>
                  </div>
                </div>

                {(result.fit.notes || []).length > 0 && (
                  <div className="mt-4 text-sm text-zinc-300">
                    <p className="text-zinc-400 mb-1">Notes</p>
                    <ul className="space-y-2 list-disc list-inside">
                      {result.fit.notes!.slice(0, 5).map((n, i) => (
                        <li key={i}>{n}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-10 text-xs text-zinc-500">
          Local dev: React @ 5173 • FastAPI @ 8000
        </div>
      </div>
    </div>
  );
}
