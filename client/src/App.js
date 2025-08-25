import React, { useEffect, useMemo, useState } from "react";
import "./styles.css";




const API_BASE = ""; // keep your CRA proxy setup

export default function App() {
  useEffect(() => {
    document.title =
      "Hierarchical Aggregation and Drilldown of Data Quality Scores Using Knowledge Graphs";
  }, []);

  // ===== pipeline state =====
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);

  // ===== query state =====
  const [queryNames, setQueryNames] = useState([]);
  const [loadingNames, setLoadingNames] = useState(false);
  const [namesError, setNamesError] = useState(null);

  const [activeQuery, setActiveQuery] = useState(null);
  const [queryRows, setQueryRows] = useState([]);
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [queryError, setQueryError] = useState(null);
  const [showQueryJson, setShowQueryJson] = useState(false);

  const onChooseFile = (e) => setFile(e.target.files?.[0] || null);

  async function run() {
    if (!file) { setResult({ error: "Please choose a JSON file first." }); return; }
    setRunning(true); setResult(null);
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch(`${API_BASE}/api/process-upload`, { method: "POST", body: fd });
      const data = await res.json(); setResult(data);
    } catch (e) { setResult({ error: String(e) }); }
    finally { setRunning(false); }
  }

  async function importToGraphDB() {
    try {
      const res = await fetch(`${API_BASE}/api/graphdb/import`, { method: "POST" });
      const data = await res.json();
      alert(data.ok ? "✅ Imported to GraphDB" : "❌ Import failed: " + (data.error || data.status));
    } catch (e) { alert("❌ Error: " + e); }
  }

  async function clearRepo() {
    if (!window.confirm("This will delete all triples in the repository. Continue?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/graphdb/clear`, { method: "POST" });
      const data = await res.json();
      alert(data.ok ? "🧹 Repository cleared" : "❌ Clear failed: " + (data.error || data.status));
    } catch (e) { alert("❌ Error: " + e); }
  }

  useEffect(() => {
    (async () => {
      setLoadingNames(true); setNamesError(null);
      try {
        const res = await fetch(`${API_BASE}/api/queries/list`);
        const data = await res.json();
        if (!res.ok) throw new Error(data?.error || "Failed to load queries");
        setQueryNames(Array.isArray(data) ? data : []);
      } catch (e) { setNamesError(String(e)); }
      finally { setLoadingNames(false); }
    })();
  }, []);

  async function runQuery(name) {
    setActiveQuery(name); setLoadingQuery(true);
    setQueryError(null); setQueryRows([]);
    try {
      const res = await fetch(`${API_BASE}/api/queries/run?name=${encodeURIComponent(name)}`);
      const data = await res.json();
      if (!res.ok) setQueryError(data?.error || "Unknown error");
      else setQueryRows(Array.isArray(data.rows) ? data.rows : []);
    } catch (e) { setQueryError(String(e)); }
    finally { setLoadingQuery(false); }
  }

  const columns = useMemo(() => {
    const set = new Set();
    queryRows.forEach(r => Object.keys(r || {}).forEach(k => set.add(k)));
    return Array.from(set);
  }, [queryRows]);

  return (
    <div className="container">

      {/* Header */}
      <div className="header">
        <h1 className="title">
          Hierarchical Aggregation and Drilldown of Data<br/>
          Quality Scores Using Knowledge Graphs
        </h1>
        <p className="subtitle">
          Upload JSON → generate <span className="kbd">data.json</span> → produce <span className="kbd">output.ttl</span>, import to GraphDB, then explore scores and drill down.
        </p>

        <div className="row" style={{marginTop:12}}>
          <a className="btn btn-primary" href="/genai">✨ Try GenAI Query Builder</a>
          <span className="badge">beta</span>
          
        </div>
        
      </div>

      




      {/* Pipeline Card */}
      <div className="card">
        <h3 style={{marginTop:0}}>Step 1 — Build RDF</h3>
        <div className="row">
          <label className="input">
            <input type="file" accept=".json,application/json" onChange={onChooseFile}/>
            {file ? <>📄 {file.name}</> : <>📂 Choose JSON file</>}
          </label>

          <button className="btn" onClick={run} disabled={running}>
            {running ? "Running…" : "Run pipeline"}
          </button>

          <button className="btn" onClick={importToGraphDB} disabled={running}>
            Import to GraphDB
          </button>

          <button className="btn btn-danger" onClick={clearRepo} disabled={running}>
            Clear repository
          </button>
        </div>

        <div style={{marginTop:12}}>
          <pre className="code">
            {result ? JSON.stringify(result, null, 2) : "(no result yet)"}
          </pre>
          {result?.ok && result.files?.output_ttl && (
            <div style={{marginTop:8}}>
              <a className="link" href={result.files.output_ttl} download>⬇ Download output.ttl</a>
            </div>
          )}
        </div>
      </div>

      {/* Queries Card */}
      <div className="card">
        <h3 style={{marginTop:0}}>Step 2 — Explore with Preset Queries</h3>
        <p className="subtitle" style={{marginTop:0}}>
          These run against your repository (e.g., <span className="kbd">bachelor2025</span>).
        </p>

        {loadingNames ? (
          <div className="badge">Loading query list…</div>
        ) : namesError ? (
          <div className="alert">Failed to load queries: {namesError}</div>
        ) : queryNames.length === 0 ? (
          <div className="badge">No queries found.</div>
        ) : (
          <div className="row" style={{marginBottom:10}}>
            {queryNames.map((n) => (
              <button
                key={n}
                className={"btn " + (activeQuery === n ? "btn-ghost" : "")}
                onClick={() => runQuery(n)}
              >
                {n}
              </button>
            ))}
          </div>
        )}

        <div className="row" style={{gap:10, alignItems:"center"}}>
          <h4 style={{margin:"8px 0"}}>Result {activeQuery ? `— ${activeQuery}` : ""}</h4>
          <label style={{display:"inline-flex",alignItems:"center",gap:6}}>
            <input type="checkbox"
              checked={showQueryJson}
              onChange={(e)=>setShowQueryJson(e.target.checked)}
            />
            Show raw JSON
          </label>
        </div>

        {loadingQuery && <div className="badge">Running…</div>}
        {queryError && <div className="alert">{String(queryError)}</div>}

        {!loadingQuery && !queryError && queryRows.length>0 && !showQueryJson && (
          <DataTable rows={queryRows} columns={columns}/>
        )}
        {!loadingQuery && !queryError && showQueryJson && (
          <pre className="code">{JSON.stringify(queryRows,null,2)}</pre>
        )}
      </div>
    </div>
  );
}

/* -------- small table renderer -------- */
function DataTable({ rows, columns }) {
  return (
    <div className="box">
      <table className="table">
        <thead>
          <tr>{columns.map(c => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r,i)=>(
            <tr key={i}>
              {columns.map(c=>(
                <td key={c}>{renderCell(r?.[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function renderCell(v){
  if (v==null) return "";
  if (typeof v==="string" && v.startsWith("http")){
    return <a className="link" href={v} target="_blank" rel="noreferrer">{v}</a>;
  }
  return String(v);
}
