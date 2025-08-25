import React, { useEffect, useMemo, useState } from "react";
import "./styles.css";

const API_BASE = "";

export default function GenAIPage() {
  useEffect(() => {
    document.title =
      "Hierarchical Aggregation and Drilldown of Data Quality Scores Using Knowledge Graphs";
  }, []);

  const [question, setQuestion] = useState("");
  const [sparql, setSparql] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [showQuery, setShowQuery] = useState(true);

  async function translate() {
    setErr(null); setRows([]);
    if (!question.trim()) { setErr("Please type a question."); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/nl2sparql/translate`,{
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({question})
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Translate failed");
      setSparql(data.query || "");
      setShowQuery(true);
    } catch(e){ setErr(String(e)); }
    finally{ setLoading(false); }
  }

  async function runGenerated(){
    setErr(null); setRows([]);
    if (!sparql.trim()) { setErr("No SPARQL to run."); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/queries/run-raw`,{
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({query:sparql})
      });
      const data = await res.json();
      if (!res.ok){
        const detail = data.details ? ` — ${String(data.details).slice(0,500)}` : "";
        throw new Error((data.error||"Run failed")+detail);
      }
      setRows(Array.isArray(data.rows) ? data.rows : []);
    } catch(e){ setErr(String(e)); }
    finally{ setLoading(false); }
  }

  const columns = useMemo(()=>{
    const set = new Set(); rows.forEach(r=>Object.keys(r||{}).forEach(k=>set.add(k)));
    return Array.from(set);
  },[rows]);

  return (
    <div className="container">

      <div className="header">
        <div className="row" style={{justifyContent:"space-between"}}>
          <div>
            <h1 className="title" style={{marginBottom:6}}>More options with GenAI</h1>
            <p className="subtitle" style={{marginTop:0}}>
              Ask in natural language. We’ll generate SPARQL with OpenAI and you can run it on GraphDB.
            </p>
          </div>
          <div style={{alignSelf:"center"}}>
            <a className="link" href="/">← Back to Dashboard</a>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{marginTop:0}}>Ask a question</h3>
        <textarea
          value={question}
          onChange={e=>setQuestion(e.target.value)}
          placeholder="e.g., Which database has the highest average score?"
          rows={6}
          style={{
            width:"100%", background:"#0f1530", color:"var(--text)",
            border:"1px solid var(--border)", borderRadius:12, padding:12, outline:"none"
          }}
        />
        <div className="row" style={{marginTop:12}}>
          <button className="btn" onClick={translate} disabled={loading}>Translate to SPARQL</button>
          <button className="btn btn-primary" onClick={runGenerated} disabled={loading || !sparql}>
            Run generated query
          </button>
          <label style={{display:"inline-flex",alignItems:"center",gap:6, marginLeft:4}}>
            <input type="checkbox" checked={showQuery} onChange={e=>setShowQuery(e.target.checked)}/>
            Show generated SPARQL
          </label>
        </div>

        {err && <div className="alert" style={{marginTop:12}}>Error: {err}</div>}

        {showQuery && sparql && (
          <pre className="code" style={{marginTop:12}}>{sparql}</pre>
        )}

        {rows.length>0 && (
          <div style={{marginTop:12}}>
            <DataTable rows={rows} columns={columns}/>
          </div>
        )}
      </div>
    </div>
  );
}

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
