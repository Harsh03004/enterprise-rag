import { useEffect, useState } from "react";
import {
  getEvaluationRun,
  getEvaluationRuns,
  type EvaluationRun,
  type EvaluationRunSummary,
} from "../api/admin";
import AdminNav from "../components/AdminNav";

// Higher is better for every metric except false_refusal_rate.
const METRICS = [
  "pass_rate",
  "answer_accuracy",
  "fact_recall",
  "refusal_accuracy",
  "false_refusal_rate",
  "retrieval_hit_rate",
  "passage_recall",
  "mrr",
  "citation_precision",
  "citation_recall",
];
const TREND_METRICS = ["pass_rate", "answer_accuracy", "refusal_accuracy", "retrieval_hit_rate", "citation_precision"];

function formatMetric(value: unknown, digits = 1) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export default function Evaluations() {
  const [runs, setRuns] = useState<EvaluationRunSummary[]>([]);
  const [selected, setSelected] = useState<EvaluationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getEvaluationRuns()
      .then(async (items) => {
        setRuns(items);
        if (items[0]) setSelected(await getEvaluationRun(items[0].id));
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load evaluation history."))
      .finally(() => setLoading(false));
  }, []);

  async function selectRun(run: EvaluationRunSummary) {
    setError("");
    try { setSelected(await getEvaluationRun(run.id)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load evaluation run."); }
  }

  const failures = selected?.results.filter((result) => result.passed === false) ?? [];
  const caseErrors = selected?.case_errors ?? [];
  const trendRuns = runs.filter((run) => run.status === "completed");
  const failedCases: Array<Record<string, unknown>> = [
    ...failures.map((item) => ({ ...item, evaluation_error: null })),
    ...caseErrors.map((item) => ({ ...item, evaluation_error: item.error })),
  ];

  return (
    <main className="admin-page dashboard-page">
      <header className="chat-header dashboard-header">
        <div className="chat-header-info"><h1>RAG evaluations</h1><p>Benchmark history, metric changes, and case failures</p></div>
        <AdminNav active="/admin/evaluations" />
      </header>
      {error && <div className="chat-error" role="alert">{error}</div>}
      {loading && <p className="dashboard-empty">Loading evaluation history…</p>}
      {!loading && !runs.length && <section className="dashboard-panel"><h2>No evaluation runs yet</h2><p>Run the evaluation CLI with a baseline to store benchmark history and regression results here.</p></section>}

      {runs.length > 0 && (
        <div className="evaluation-layout">
          <aside className="dashboard-panel evaluation-history"><h2>Benchmark history</h2>
            {runs.map((run) => (
              <button className={`evaluation-run ${selected?.id === run.id ? "selected" : ""}`} key={run.id} onClick={() => void selectRun(run)}>
                <strong>{new Date(run.created_at).toLocaleString()}</strong><span>{run.dataset_name} · {run.provider}/{run.model}</span>
                {run.status === "incomplete" ? <em>{run.case_errors.length} case errors · score unavailable</em> : <span>{String(run.summary.passed ?? 0)}/{String(run.summary.total ?? 0)} passed</span>}
                {run.status === "completed" && run.regression_failures.length > 0 && <em>Regression detected</em>}
              </button>
            ))}
          </aside>

          {selected && <section className="evaluation-detail">
            <div className="dashboard-panel">
              <div className="dashboard-panel-heading"><div><h2>Run #{selected.id}</h2><span>{selected.dataset_name} · {selected.provider}/{selected.model}</span></div><span>{new Date(selected.created_at).toLocaleString()}</span></div>
              {selected.status === "incomplete" ? <div className="evaluation-alert"><h3>Incomplete benchmark</h3><p>Operational errors prevented a valid score. This run is excluded from metric trends and regression comparisons.</p></div> : <>
                <div className="evaluation-metrics">
                  {METRICS.map((metric) => (
                    <article key={metric}><span>{metric.replaceAll("_", " ")}</span><strong>{formatMetric(selected.summary[metric])}</strong></article>
                  ))}
                </div>
                {selected.summary.categories && <div className="evaluation-trend-table"><h3>By category</h3><div className="admin-row evaluation-trend-heading"><span>Category</span><span>Passed</span><span>Pass rate</span></div>
                  {Object.entries(selected.summary.categories).map(([category, stats]) => <div className="admin-row" key={category}><span>{category}</span><span>{stats.passed}/{stats.total}</span><span>{formatMetric(stats.pass_rate, 0)}</span></div>)}
                </div>}
                <div className="evaluation-trend-table"><h3>Metric trend</h3><div className="admin-row evaluation-trend-heading"><span>Run date</span>{TREND_METRICS.map((metric) => <span key={metric}>{metric.replaceAll("_", " ")}</span>)}</div>
                  {trendRuns.slice().reverse().map((run) => <div className="admin-row" key={run.id}><span>{new Date(run.created_at).toLocaleDateString()}</span>{TREND_METRICS.map((metric) => <span key={metric}>{formatMetric(run.summary[metric], 0)}</span>)}</div>)}
                </div>
                {selected.regression_failures.length > 0 && <div className="evaluation-alert"><h3>Regression checks failed</h3>{selected.regression_failures.map((item) => <p key={item}>{item}</p>)}</div>}
              </>}
            </div>
            <div className="dashboard-panel"><h2>Failed cases ({failures.length + caseErrors.length})</h2>
              {failedCases.map((item, index) => (
                <article className="failed-case" key={`${String(item.case_id ?? index)}-${index}`}>
                  <div><strong>{String(item.case_id ?? "Case")}</strong><span>{String(item.category ?? "")}</span></div>
                  <p><b>Question:</b> {String(item.question ?? "")}</p>
                  {typeof item.evaluation_error === "string" ? <p className="failed-case-error">{item.evaluation_error}</p> : <>
                    <p><b>Returned answer:</b> {String(item.answer ?? "")}</p>
                    {typeof item.draft_answer === "string" && item.draft_answer !== item.answer && <p><b>Model draft:</b> {String(item.draft_answer) || "No draft (retrieval confidence gate)"}</p>}
                    <p><b>Expected outcome:</b> {item.should_fallback ? "Refusal" : "Grounded answer"}{typeof item.status === "string" && <> · <b>Pipeline status:</b> {item.status.replaceAll("_", " ")}</>}</p>
                    {Array.isArray(item.failure_reasons) && item.failure_reasons.length > 0 && <p className="failed-case-error"><b>Failed checks:</b> {item.failure_reasons.map(String).join(", ")}</p>}
                  </>}
                </article>
              ))}
              {!failures.length && !caseErrors.length && <p className="dashboard-empty">All evaluated cases passed.</p>}
            </div>
          </section>}
        </div>
      )}
    </main>
  );
}
