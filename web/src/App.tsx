import { useState } from "react";

export default function App() {
  const [jobText, setJobText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [cvStatus, setCvStatus] = useState<string>("");

  async function handleGenerate() {
    if (!jobText.trim()) return;

    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/generate-from-job-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_text: jobText }),
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Backend error");
    } finally {
      setLoading(false);
    }
  }

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

    setCvStatus(`✅ CV ingested: ${data.chunks} chunks, ${data.chars} chars`);
  } catch (e) {
    console.error(e);
    setCvStatus("Upload failed: backend not reachable");
  }
}


  return (
    <div className="min-h-screen bg-zinc-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">
        CV Cover Letter Agent
      </h1>

    <div className="bg-zinc-800 p-4 rounded-xl mb-6">
      <h2 className="text-xl font-semibold mb-2">Upload CV (PDF)</h2>

      <div className="flex flex-col md:flex-row gap-3 items-start md:items-center">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setCvFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-zinc-200
            file:mr-4 file:py-2 file:px-4
            file:rounded file:border-0
            file:text-sm file:font-semibold
          file:bg-zinc-900 file:text-white
          hover:file:bg-zinc-700"
          />

          <button
            onClick={handleUploadCV}
            disabled={!cvFile}
            className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-4 py-2 rounded font-semibold w-full md:w-auto"
          >
            Upload & Index
          </button>
    </div>

  {cvStatus && <p className="mt-3 text-sm text-zinc-300">{cvStatus}</p>}
</div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* LEFT */}
        <div className="bg-zinc-800 p-4 rounded-xl">
          <h2 className="text-xl font-semibold mb-2">Job Description</h2>
          <textarea
            className="w-full h-[300px] p-3 rounded bg-zinc-900 text-white border border-zinc-700 focus:outline-none"
            placeholder="Paste job description here..."
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
          />

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="mt-4 w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-2 rounded font-semibold"
          >
            {loading ? "Generating..." : "Generate Cover Letter"}
          </button>
        </div>

        {/* RIGHT */}
        <div className="bg-zinc-800 p-4 rounded-xl overflow-auto">
          <h2 className="text-xl font-semibold mb-2">Result</h2>

          {!result && (
            <p className="text-zinc-400">
              Generated cover letter will appear here.
            </p>
          )}

          {result?.final?.cover_letter && (
            <pre className="whitespace-pre-wrap text-sm leading-relaxed">
              {result.final.cover_letter}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
