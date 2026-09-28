import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, ApiError, AlertDetail, AlertEvidenceResponse } from '../lib/api';
import { PageFrame } from '../layouts/PageFrame';
import { SystemState } from '../components/ui/SystemState';
import { useRunContext } from '../contexts/RunContext';

export function EvidenceProvenance() {
  const { runId, alertId } = useParams<{ runId: string; alertId: string }>();
  
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState<'NONE' | 'RUN_UNAVAILABLE' | 'ALERT_UNAVAILABLE' | 'ERROR'>('NONE');
  const [alertData, setAlertData] = useState<AlertDetail | null>(null);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);

  const { setRun } = useRunContext();

  useEffect(() => {
    async function loadData() {
      if (!runId || !alertId) return;
      setLoading(true);
      setErrorState('NONE');
      
      try {
        const runData = await apiClient.getRun(runId);
        setRun({ id: runData.run_id, status: runData.status });
      } catch (err: unknown) {
        console.error(err);
        setRun(undefined);
        if (err instanceof ApiError && err.status === 404) {
          setErrorState('RUN_UNAVAILABLE');
        } else {
          setErrorState('ERROR');
        }
        setLoading(false);
        return;
      }

      try {
        const aData = await apiClient.getAlert(runId, alertId);
        setAlertData(aData);
        if (aData.evidence && aData.evidence.length > 0) {
          setSelectedEvidenceId(aData.evidence[0].evidence_id);
        }
      } catch (err: unknown) {
        console.error(err);
        if (err instanceof ApiError && err.status === 404) {
          setErrorState('ALERT_UNAVAILABLE');
        } else {
          setErrorState('ERROR');
        }
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, [runId, alertId, setRun]);

  const selectedEvidence = useMemo(() => {
    if (!alertData || !selectedEvidenceId) return null;
    return alertData.evidence.find((e: AlertEvidenceResponse) => e.evidence_id === selectedEvidenceId) || null;
  }, [alertData, selectedEvidenceId]);

  if (loading) return <PageFrame><SystemState type="LOADING" /></PageFrame>;
  if (errorState !== 'NONE') return <PageFrame><SystemState type={errorState} /></PageFrame>;
  if (!alertData) return <PageFrame><SystemState type="ERROR" /></PageFrame>;
  
  const evidenceList = alertData.evidence || [];
  if (evidenceList.length === 0) return <PageFrame><SystemState type="EMPTY" /></PageFrame>;

  return (
    <PageFrame>
      {/* WORKFLOW STEPPER */}
      <section className="w-full bg-neutral border-b border-structural-border px-6 py-2 flex flex-wrap items-center justify-between font-mono font-bold text-[0.6875rem]">
        <div className="flex items-center flex-wrap gap-2 uppercase tracking-wide text-muted-ink">
          <Link to={`/runs/${runId}/alerts`} className="hover:text-secondary cursor-pointer">1 ALERT QUEUE</Link>
          <span>→</span>
          <Link to={`/runs/${runId}/alerts/${alertId}`} className="hover:text-secondary cursor-pointer">2 ALERT INVESTIGATION</Link>
          <span>→</span>
          <Link to={`/runs/${runId}/transactions/${alertData.txid}`} className="hover:text-secondary cursor-pointer">3 TX INVESTIGATION</Link>
          <span>→</span>
          <Link to={`/runs/${runId}/transactions/${alertData.txid}/graph`} className="hover:text-secondary cursor-pointer">4 NETWORK GRAPH</Link>
          <span>→</span>
          <span className="bg-secondary text-neutral px-2 py-0.5 border border-structural-border">5 PROVENANCE (ACTIVE)</span>
        </div>
        <div className="hidden md:flex items-center text-muted-ink">
          ACTIVE RUN: <span className="text-secondary font-bold ml-1.5">{runId}</span>
        </div>
      </section>

      {/* PAGE HEADER & METADATA BLOCK */}
      <div className="w-full border-b border-structural-border bg-surface-accent px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-8">
          <div className="font-mono text-[0.6875rem] font-bold text-primary mb-1 uppercase tracking-widest flex items-center gap-2">
            <span className="w-2 h-2 bg-secondary"></span>
            <span>EVIDENCE TRACEABILITY</span>
          </div>
          <h1 className="font-display text-4xl font-bold text-secondary uppercase tracking-tight leading-none mb-3">
            EVIDENCE & PROVENANCE
          </h1>
          <p className="font-body text-[0.9375rem] text-muted-ink max-w-4xl leading-snug">
            Trace analytical findings back to source records, derived artifacts, model outputs, and enrichment without asserting identity or intent.
          </p>
        </div>
        <div className="lg:col-span-4 border border-structural-border bg-neutral p-4">
          <div className="font-mono text-[0.6875rem] font-bold uppercase border-b border-structural-border pb-1 mb-2 text-secondary flex justify-between items-center">
            <span>WORKBENCH STATE</span>
            <span className="px-1.5 py-0.5 bg-primary text-secondary">ACTIVE</span>
          </div>
          <div className="space-y-1 font-mono text-[0.6875rem]">
            <div className="flex justify-between">
              <span className="text-muted-ink">STATE:</span>
              <span className="font-bold text-secondary">PROVENANCE ACTIVE</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-ink">RUN:</span>
              <span className="text-secondary font-bold">{runId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-ink">SELECTED RECORD:</span>
              <span className="text-secondary font-bold">{selectedEvidenceId || '[DYNAMIC / NOT AVAILABLE]'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* PRIMARY 8:4 ANALYTICAL WORKSPACE */}
      <main className="w-full flex-grow grid grid-cols-1 lg:grid-cols-12 border-b border-structural-border">
        
        {/* LEFT COLUMN (~8 cols / ~66%) */}
        <div className="lg:col-span-8 border-r border-structural-border flex flex-col divide-y divide-structural-border">
          
          {/* SEC 01 EVIDENCE LINEAGE */}
          <section className="bg-surface-accent p-6">
            <div className="flex flex-col md:flex-row md:items-baseline justify-between border-b border-structural-border pb-3 mb-6 gap-2">
              <div>
                <h2 className="font-display text-xl uppercase tracking-tight text-secondary flex items-center gap-2">
                  <span className="font-mono text-[0.6875rem] font-bold bg-secondary text-neutral px-1.5 py-0.5">SEC 01</span>
                  <span>EVIDENCE LINEAGE</span>
                </h2>
                <p className="font-body text-sm text-muted-ink mt-1">Traceable analytical path across available source references, derived evidence, and interpretation.</p>
              </div>
              <span className="font-mono text-[0.6875rem] text-muted-ink border border-structural-border px-2 py-1 bg-neutral self-start font-bold">5-STAGE PROVENANCE PATH</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 border border-structural-border divide-y md:divide-y-0 md:divide-x divide-structural-border bg-neutral">
              
              {/* Stage 1 */}
              <div className="p-3 flex flex-col justify-between relative bg-neutral">
                <div>
                  <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase mb-1 border-b border-structural-border/40 pb-1">STAGE 1</div>
                  <div className="font-display text-sm font-bold uppercase text-secondary mb-2">SOURCE RECORD</div>
                  <div className="font-mono text-[0.6875rem] space-y-1.5 text-secondary">
                    <div><span className="text-muted-ink block">SOURCE:</span> <span className="break-all font-bold">{selectedEvidence?.source_file || '[DYNAMIC / NOT AVAILABLE]'}</span></div>
                    <div><span className="text-muted-ink block">ROW:</span> <span>{selectedEvidence?.source_row || '[DYNAMIC / NOT AVAILABLE]'}</span></div>
                  </div>
                </div>
                <div className="mt-4 pt-2 border-t border-dashed border-muted-ink/40 font-mono text-[0.6875rem] flex items-center justify-between text-muted-ink">
                  <span>INPUT</span>
                  <span className="font-bold text-secondary">→</span>
                </div>
              </div>

              {/* Stage 2 */}
              <div className="p-3 flex flex-col justify-between relative bg-surface-accent">
                <div>
                  <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase mb-1 border-b border-structural-border/40 pb-1">STAGE 2</div>
                  <div className="font-display text-sm font-bold uppercase text-secondary mb-2">NORMALIZED RECORD</div>
                  <div className="font-mono text-[0.6875rem] space-y-1.5 text-secondary">
                    <div><span className="text-muted-ink block">RECORD ID:</span> <span className="font-bold">{selectedEvidence?.evidence_id?.substring(0,8) || '[DYNAMIC / NOT AVAILABLE]'}</span></div>
                    <div><span className="text-muted-ink block">SCHEMA:</span> <span>{selectedEvidence?.schema_version || '[DYNAMIC / NOT AVAILABLE]'}</span></div>
                  </div>
                </div>
                <div className="mt-4 pt-2 border-t border-dashed border-muted-ink/40 font-mono text-[0.6875rem] flex items-center justify-between text-muted-ink">
                  <span>CANONICAL</span>
                  <span className="font-bold text-secondary">→</span>
                </div>
              </div>

              {/* Stage 3 */}
              <div className="p-3 flex flex-col justify-between relative bg-neutral">
                <div>
                  <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase mb-1 border-b border-structural-border/40 pb-1">STAGE 3</div>
                  <div className="font-display text-sm font-bold uppercase text-secondary mb-2">DERIVED ARTIFACT</div>
                  <div className="font-mono text-[0.6875rem] space-y-1.5 text-secondary">
                    <div><span className="text-muted-ink block">FEATURE:</span> <span>{selectedEvidence?.feature_name || '[DYNAMIC / NOT AVAILABLE]'}</span></div>
                    <div><span className="text-muted-ink block">TIER:</span> <span className="font-bold">{selectedEvidence?.provenance_type || '[DYNAMIC / NOT AVAILABLE]'}</span></div>
                  </div>
                </div>
                <div className="mt-4 pt-2 border-t border-dashed border-muted-ink/40 font-mono text-[0.6875rem] flex items-center justify-between text-muted-ink">
                  <span>COMPUTED</span>
                  <span className="font-bold text-secondary">→</span>
                </div>
              </div>

              {/* Stage 4 */}
              <div className="p-3 flex flex-col justify-between relative bg-surface-accent">
                <div>
                  <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase mb-1 border-b border-structural-border/40 pb-1">STAGE 4</div>
                  <div className="font-display text-sm font-bold uppercase text-secondary mb-2">MODEL OUTPUT</div>
                  <div className="font-mono text-[0.6875rem] space-y-1.5 text-secondary">
                    {selectedEvidence?.provenance_type === 'ML_DERIVED' ? (
                      <>
                        <div><span className="text-muted-ink block">MODEL:</span> <span className="font-bold">[DYNAMIC / NOT AVAILABLE]</span></div>
                        <div><span className="text-muted-ink block">VERSION:</span> <span>{selectedEvidence?.model_version || '[DYNAMIC / NOT AVAILABLE]'}</span></div>
                      </>
                    ) : (
                      <div className="text-muted-ink font-bold pt-2">NOT APPLICABLE</div>
                    )}
                  </div>
                </div>
                <div className="mt-4 pt-2 border-t border-dashed border-muted-ink/40 font-mono text-[0.6875rem] flex items-center justify-between text-muted-ink">
                  <span>INFERENCE</span>
                  <span className="font-bold text-secondary">→</span>
                </div>
              </div>

              {/* Stage 5 */}
              <div className="p-3 flex flex-col justify-between relative bg-neutral border-l-2 border-l-structural-border md:border-l-0">
                <div>
                  <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase mb-1 border-b border-structural-border/40 pb-1">STAGE 5</div>
                  <div className="font-display text-sm font-bold uppercase text-secondary mb-2">INTERPRETATION</div>
                  <div className="font-mono text-[0.6875rem] space-y-1.5 text-secondary">
                    <div><span className="text-muted-ink block">SYNTHESIS:</span> <span className="font-bold">{alertData.human_readable_lead || '[DYNAMIC / NOT AVAILABLE]'}</span></div>
                  </div>
                </div>
                <div className="mt-4 pt-2 border-t border-dashed border-muted-ink/40 font-mono text-[0.6875rem] flex items-center justify-between text-muted-ink">
                  <span>INTERPRETATION</span>
                  <span className="font-bold text-primary">●</span>
                </div>
              </div>
            </div>
            
            <div className="mt-3 flex items-center justify-between font-mono text-[0.6875rem] text-muted-ink">
              <span>NOTE: Traceability describes available analytical lineage; it does not establish causal certainty.</span>
              <span className="hidden md:inline font-bold text-secondary">TRACEABILITY: SOURCE → DERIVATION → INTERPRETATION</span>
            </div>
          </section>

          {/* SEC 02 SOURCE RECORD INSPECTION TABLE */}
          <section className="bg-surface-accent p-6">
            <div className="flex items-center justify-between border-b border-structural-border pb-3 mb-4">
              <div>
                <h2 className="font-display text-xl uppercase tracking-tight text-secondary flex items-center gap-2">
                  <span className="font-mono text-[0.6875rem] font-bold bg-secondary text-neutral px-1.5 py-0.5">SEC 02</span>
                  <span>SOURCE RECORD INSPECTION</span>
                </h2>
                <p className="font-body text-sm text-muted-ink">Source record and schema provenance from ingestion records.</p>
              </div>
            </div>
            <div className="border border-structural-border overflow-x-auto">
              <table className="w-full text-left border-collapse font-mono text-[0.6875rem]">
                <tbody className="divide-y divide-structural-border">
                  <tr className="bg-neutral">
                    <th className="py-2 px-4 uppercase font-bold text-muted-ink border-r border-structural-border w-1/3">SOURCE FILE</th>
                    <td className="py-2 px-4 font-bold text-secondary">{selectedEvidence?.source_file || '[DYNAMIC / NOT AVAILABLE]'}</td>
                  </tr>
                  <tr className="bg-surface-accent">
                    <th className="py-2 px-4 uppercase font-bold text-muted-ink border-r border-structural-border">ROW / RECORD</th>
                    <td className="py-2 px-4 text-secondary">{selectedEvidence?.source_row || '[DYNAMIC / NOT AVAILABLE]'}</td>
                  </tr>
                  <tr className="bg-neutral">
                    <th className="py-2 px-4 uppercase font-bold text-muted-ink border-r border-structural-border">RECORD ID</th>
                    <td className="py-2 px-4 font-bold text-secondary">{selectedEvidence?.evidence_id || '[DYNAMIC / NOT AVAILABLE]'}</td>
                  </tr>
                  <tr className="bg-surface-accent">
                    <th className="py-2 px-4 uppercase font-bold text-muted-ink border-r border-structural-border">INGESTION RUN</th>
                    <td className="py-2 px-4 text-secondary">{runId}</td>
                  </tr>
                  <tr className="bg-neutral">
                    <th className="py-2 px-4 uppercase font-bold text-muted-ink border-r border-structural-border">STATUS</th>
                    <td className="py-2 px-4 font-bold text-primary">[DYNAMIC / NOT AVAILABLE]</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* SEC 03 AUDIT TRACE LOG */}
          <section className="bg-surface-accent p-6">
            <div className="flex items-center justify-between border-b border-structural-border pb-3 mb-4">
              <div>
                <h2 className="font-display text-xl uppercase tracking-tight text-secondary flex items-center gap-2">
                  <span className="font-mono text-[0.6875rem] font-bold bg-secondary text-neutral px-1.5 py-0.5">SEC 03</span>
                  <span>AUDIT TRACE LOG</span>
                </h2>
                <p className="font-body text-sm text-muted-ink">Chronological sequence of available pipeline and derivation events.</p>
              </div>
              <span className="font-mono text-[0.6875rem] text-muted-ink font-bold">EVENT COUNT: {evidenceList.length}</span>
            </div>
            <div className="border border-structural-border overflow-x-auto max-h-64 overflow-y-auto">
              <table className="w-full text-left border-collapse font-mono text-[0.6875rem]">
                <thead className="sticky top-0 bg-secondary text-neutral border-b-2 border-structural-border">
                  <tr>
                    <th className="py-2.5 px-4 uppercase border-r border-neutral/20">EVENT / CATEGORY</th>
                    <th className="py-2.5 px-4 uppercase border-r border-neutral/20">RECORD ID</th>
                    <th className="py-2.5 px-4 uppercase border-r border-neutral/20">SOURCE / TIER</th>
                    <th className="py-2.5 px-4 uppercase">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-structural-border">
                  {evidenceList.map((ev, idx) => (
                    <tr 
                      key={ev.evidence_id}
                      onClick={() => setSelectedEvidenceId(ev.evidence_id)}
                      className={`cursor-pointer transition-none ${selectedEvidenceId === ev.evidence_id ? 'bg-primary/10' : idx % 2 === 0 ? 'bg-surface-accent hover:bg-neutral' : 'bg-neutral hover:bg-surface-accent'}`}
                    >
                      <td className="py-2 px-4 border-r border-structural-border">{ev.evidence_category}</td>
                      <td className="py-2 px-4 border-r border-structural-border font-bold">{ev.evidence_id.substring(0,8)}...</td>
                      <td className="py-2 px-4 border-r border-structural-border">{ev.provenance_type}</td>
                      <td className="py-2 px-4 font-bold text-secondary">[DYNAMIC]</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* SEC 04 MODEL-DERIVED EVIDENCE & ANALYTICAL DERIVATION */}
          <section className="bg-surface-accent p-6">
            <div className="border-b border-structural-border pb-3 mb-4">
              <h2 className="font-display text-xl uppercase tracking-tight text-secondary flex items-center gap-2">
                <span className="font-mono text-[0.6875rem] font-bold bg-secondary text-neutral px-1.5 py-0.5">SEC 04</span>
                <span>MODEL-DERIVED EVIDENCE & ANALYTICAL DERIVATION</span>
              </h2>
              <p className="font-body text-sm text-muted-ink">Mathematical derivation of features and model explanations.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Panel A: Model-Derived Evidence */}
              <div className="border border-structural-border flex flex-col justify-between bg-neutral">
                <div>
                  <div className="border-b border-structural-border p-3 bg-surface-accent flex justify-between items-center">
                    <span className="font-display text-sm font-bold uppercase text-secondary">MODEL-DERIVED EVIDENCE</span>
                    <span className="font-mono text-[0.6875rem] font-bold text-primary">ML_DERIVED</span>
                  </div>
                  <div className="p-4 space-y-2.5 font-mono text-[0.6875rem]">
                    {selectedEvidence?.provenance_type === 'ML_DERIVED' ? (
                      <>
                        <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                          <span className="text-muted-ink">MODEL:</span>
                          <span className="font-bold text-secondary">[DYNAMIC / NOT AVAILABLE]</span>
                        </div>
                        <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                          <span className="text-muted-ink">MODEL VERSION:</span>
                          <span className="text-secondary">{selectedEvidence.model_version || '[DYNAMIC / NOT AVAILABLE]'}</span>
                        </div>
                        <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                          <span className="text-muted-ink">FEATURE IMPACT:</span>
                          <span className="text-secondary font-bold">{selectedEvidence.feature_name || '[DYNAMIC / NOT AVAILABLE]'}</span>
                        </div>
                        <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                          <span className="text-muted-ink">UNCERTAINTY:</span>
                          <span className="text-secondary">{selectedEvidence.uncertainty_semantics || '[DYNAMIC / NOT AVAILABLE]'}</span>
                        </div>
                        <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                          <span className="text-muted-ink">SHAP CONTRIBUTION:</span>
                          <span className="text-secondary font-bold">[DYNAMIC / NOT AVAILABLE]</span>
                        </div>
                      </>
                    ) : (
                      <div className="flex justify-center p-4">
                        <span className="text-muted-ink font-bold uppercase tracking-wider">NOT APPLICABLE</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="p-3 bg-surface-accent border-t border-structural-border font-mono text-[0.6875rem] text-muted-ink">
                  Note: Model-derived evidence describes structural model output and does not establish criminal intent or identity.
                </div>
              </div>

              {/* Panel B: Analytical Derivation */}
              <div className="border border-structural-border flex flex-col justify-between bg-neutral">
                <div>
                  <div className="border-b border-structural-border p-3 bg-surface-accent flex justify-between items-center">
                    <span className="font-display text-sm font-bold uppercase text-secondary">ANALYTICAL DERIVATION</span>
                    <span className="font-mono text-[0.6875rem] font-bold text-secondary">STEP-WISE</span>
                  </div>
                  <div className="p-4">
                    <div className="p-2 border border-structural-border bg-surface-accent font-mono text-[0.6875rem] text-secondary mb-4 leading-relaxed">
                      SOURCE OBSERVATIONS → NORMALIZATION → FEATURE EXTRACTION → GRAPH / STRUCTURAL ANALYSIS → MODEL OUTPUT → EVIDENCE INTERPRETATION
                    </div>
                    <div className="space-y-2.5 font-mono text-[0.6875rem]">
                      <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                        <span className="text-muted-ink">FEATURE:</span>
                        <span className="font-bold text-secondary">{selectedEvidence?.feature_name || '[DYNAMIC / NOT AVAILABLE]'}</span>
                      </div>
                      <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                        <span className="text-muted-ink">ORIGINAL VALUE:</span>
                        <span className="text-secondary font-bold">{selectedEvidence?.original_value || '[DYNAMIC / NOT AVAILABLE]'}</span>
                      </div>
                      <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                        <span className="text-muted-ink">DERIVED VALUE:</span>
                        <span className="text-secondary font-bold">{selectedEvidence?.derived_value || '[DYNAMIC / NOT AVAILABLE]'}</span>
                      </div>
                      <div className="flex justify-between border-b border-dashed border-structural-border/20 pb-1">
                        <span className="text-muted-ink">EVIDENCE TIER:</span>
                        <span className="font-bold text-primary">{selectedEvidence?.provenance_type || '[DYNAMIC / NOT AVAILABLE]'}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-3 bg-surface-accent border-t border-structural-border font-mono text-[0.6875rem] text-muted-ink">
                  Lineage references are resolved from the active local analytical run.
                </div>
              </div>

            </div>
          </section>

          {/* SEC 05 PROVENANCE INTERPRETATION BOUNDARIES */}
          <section className="bg-neutral p-6">
            <div className="border-2 border-structural-border p-4 bg-surface-accent">
              <div className="font-mono text-[0.6875rem] font-bold text-primary uppercase tracking-widest mb-1 flex items-center gap-2">
                <span>PROVENANCE INTERPRETATION BOUNDARIES</span>
              </div>
              <p className="font-body text-sm text-secondary leading-relaxed">
                Provenance establishes traceability between analytical records and their available source references. It does not establish identity, ownership, intent, or criminal activity. Observed data, deterministic derivations, heuristics, model-derived outputs, and local enrichment must remain distinguishable.
              </p>
            </div>
          </section>
        </div>

        {/* RIGHT COLUMN (~4 cols) */}
        <div className="lg:col-span-4 border-l border-structural-border flex flex-col bg-surface-accent">
          
          <div className="p-6">
            <div className="grid grid-cols-1 gap-2">
              <Link to={`/runs/${runId}/transactions/${alertData.txid}`} className="w-full py-2.5 px-3 bg-secondary text-neutral font-mono text-[0.6875rem] font-bold uppercase hover:bg-primary hover:text-secondary transition-none flex items-center justify-between">
                <span>OPEN TRANSACTION</span>
                <span>↗</span>
              </Link>
              <Link to={`/runs/${runId}/transactions/${alertData.txid}/graph`} className="w-full py-2 px-3 border border-structural-border bg-neutral text-secondary font-mono text-[0.6875rem] font-bold uppercase hover:bg-surface-accent transition-none flex items-center justify-between">
                <span>OPEN GRAPH</span>
                <span>↗</span>
              </Link>
            </div>
          </div>

          <div className="p-6">
            <div className="border-b border-structural-border pb-3 mb-4">
              <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">ATTRIBUTION LEDGER</div>
              <h2 className="font-display text-xl uppercase tracking-tight text-secondary">PROVENANCE METADATA</h2>
            </div>
            <div className="space-y-2 font-mono text-[0.6875rem] border border-structural-border p-3 bg-neutral">
              <div className="flex justify-between border-b border-dashed border-structural-border/30 pb-1">
                <span className="text-muted-ink">SOURCE:</span>
                <span className="font-bold text-secondary">{selectedEvidence?.source_file || '[DYNAMIC / NOT AVAILABLE]'}</span>
              </div>
              <div className="flex justify-between border-b border-dashed border-structural-border/30 pb-1">
                <span className="text-muted-ink">SOURCE ROW:</span>
                <span className="text-secondary">{selectedEvidence?.source_row || '[DYNAMIC / NOT AVAILABLE]'}</span>
              </div>
              <div className="flex justify-between border-b border-dashed border-structural-border/30 pb-1">
                <span className="text-muted-ink">INGESTION RUN:</span>
                <span className="text-secondary font-bold">{runId}</span>
              </div>
              <div className="flex justify-between border-b border-dashed border-structural-border/30 pb-1">
                <span className="text-muted-ink">CATEGORY:</span>
                <span className="text-secondary font-bold">{selectedEvidence?.evidence_category || '[DYNAMIC / NOT AVAILABLE]'}</span>
              </div>
              <div className="flex justify-between border-b border-dashed border-structural-border/30 pb-1">
                <span className="text-muted-ink">MODEL VERSION:</span>
                <span className="text-secondary">{selectedEvidence?.model_version || '[DYNAMIC / NOT AVAILABLE]'}</span>
              </div>
              <div className="flex justify-between border-b border-dashed border-structural-border/30 pb-1">
                <span className="text-muted-ink">SCHEMA VERSION:</span>
                <span className="text-secondary">{selectedEvidence?.schema_version || '[DYNAMIC / NOT AVAILABLE]'}</span>
              </div>
            </div>
          </div>

          <div className="p-6">
            <div className="border-b border-structural-border pb-3 mb-4">
              <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">INTEGRITY REFERENCES</div>
              <h2 className="font-display text-xl uppercase tracking-tight text-secondary">INTEGRITY REFERENCES</h2>
            </div>
            <div className="mb-4 p-3 bg-neutral border border-structural-border flex items-center justify-between">
              <span className="font-mono text-[0.6875rem] font-bold uppercase text-secondary">PROVENANCE STATUS:</span>
              <span className="px-2 py-1 bg-secondary text-neutral font-mono text-[0.6875rem] font-bold">[DYNAMIC]</span>
            </div>
            <div className="text-xs font-mono text-[0.6875rem] text-muted-ink mb-3">
              Status Domain: COMPLETE / PARTIAL / NOT AVAILABLE / PENDING
            </div>
            <div className="border border-structural-border divide-y divide-structural-border font-mono text-[0.6875rem] bg-surface-accent">
              <div className="p-2.5">
                <span className="text-muted-ink block mb-1">RECORD ID:</span>
                <span className="font-bold text-secondary break-all">{selectedEvidence?.evidence_id || '[DYNAMIC / NOT AVAILABLE]'}</span>
              </div>
              <div className="p-2.5">
                <span className="text-muted-ink block mb-1">RUN REFERENCE:</span>
                <span className="font-bold text-secondary break-all">{runId}</span>
              </div>
            </div>
          </div>

          <div className="p-6 bg-neutral mt-auto">
            <div className="border border-structural-border p-3 bg-surface-accent text-center">
              <div className="flex items-center justify-center gap-1.5 font-mono text-[0.6875rem] font-bold text-secondary uppercase mb-1">
                <span className="w-2 h-2 bg-primary"></span>
                <span>LOCAL EXECUTION</span>
              </div>
              <div className="font-mono text-[0.6875rem] text-muted-ink tracking-tight">
                DUCKDB REPOSITORY // LOCAL STORAGE // OFFLINE RUNTIME
              </div>
            </div>
          </div>
        </div>

      </main>

      {/* FULL-WIDTH BOTTOM SECTIONS */}
      {/* 1. EVIDENCE TIER CLASSIFICATION (5 Columns) */}
      <section className="w-full border-b border-structural-border bg-surface-accent">
        <div className="px-6 py-3 border-b border-structural-border bg-neutral flex justify-between items-center">
          <div className="font-mono text-[0.6875rem] font-bold uppercase tracking-wider text-secondary">
            TAXONOMY: 5-TIER EVIDENCE CLASSIFICATION FRAMEWORK
          </div>
          <span className="font-mono text-[0.6875rem] text-muted-ink">EVIDENCE TIER DEFINITIONS</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 divide-y md:divide-y-0 md:divide-x divide-structural-border">
          {/* Tier 1 */}
          <div className="p-4 bg-surface-accent flex flex-col justify-between">
            <div>
              <div className="font-mono text-[0.6875rem] font-bold text-secondary mb-1 flex items-center justify-between">TIER 1</div>
              <div className="font-display text-sm font-bold uppercase text-secondary mb-2">1. OBSERVED</div>
              <p className="font-body text-[0.8125rem] text-muted-ink">Directly recorded source observation.</p>
            </div>
          </div>
          {/* Tier 2 */}
          <div className="p-4 bg-neutral flex flex-col justify-between">
            <div>
              <div className="font-mono text-[0.6875rem] font-bold text-secondary mb-1 flex items-center justify-between">TIER 2</div>
              <div className="font-display text-sm font-bold uppercase text-secondary mb-2">2. DERIVED</div>
              <p className="font-body text-[0.8125rem] text-muted-ink">Deterministically computed from source records.</p>
            </div>
          </div>
          {/* Tier 3 */}
          <div className="p-4 bg-surface-accent flex flex-col justify-between">
            <div>
              <div className="font-mono text-[0.6875rem] font-bold text-secondary mb-1 flex items-center justify-between">TIER 3</div>
              <div className="font-display text-sm font-bold uppercase text-secondary mb-2">3. HEURISTIC</div>
              <p className="font-body text-[0.8125rem] text-muted-ink">Rule-based analytical inference.</p>
            </div>
          </div>
          {/* Tier 4 */}
          <div className="p-4 bg-neutral flex flex-col justify-between">
            <div>
              <div className="font-mono text-[0.6875rem] font-bold text-secondary mb-1 flex items-center justify-between">TIER 4</div>
              <div className="font-display text-sm font-bold uppercase text-secondary mb-2">4. ML_DERIVED</div>
              <p className="font-body text-[0.8125rem] text-muted-ink">Produced by the trained analytical model.</p>
            </div>
          </div>
          {/* Tier 5 */}
          <div className="p-4 bg-surface-accent flex flex-col justify-between">
            <div>
              <div className="font-mono text-[0.6875rem] font-bold text-secondary mb-1 flex items-center justify-between">TIER 5</div>
              <div className="font-display text-sm font-bold uppercase text-secondary mb-2">5. ENRICHED</div>
              <p className="font-body text-[0.8125rem] text-muted-ink">Local enrichment applied to source records.</p>
            </div>
          </div>
        </div>
      </section>

      {/* 2. EPISTEMIC BOUNDARY & LEGAL SAFEGUARD STATEMENT */}
      <section className="w-full bg-secondary text-neutral border-b border-structural-border p-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-[0.6875rem] font-bold text-primary uppercase tracking-widest">
              <span>EPISTEMIC BOUNDARY & LEGAL SAFEGUARD</span>
            </div>
            <p className="font-display text-xl tracking-tight text-neutral">
              "Structural anomaly does not mean criminal activity. CryptoNexus surfaces patterns for human investigation. It does not determine identity, ownership or criminal intent."
            </p>
            <p className="font-body text-sm text-neutral/70 max-w-5xl">
              Bitcoin addresses are pseudonymous identifiers. Address ≠ wallet ≠ entity. IP association ≠ ownership. GeoIP is enrichment, not identity. Network observation time is sensor observation time.
            </p>
          </div>
          <div className="shrink-0 border border-neutral/40 p-3 text-center bg-secondary/80">
            <div className="font-mono text-[0.6875rem] font-bold text-primary uppercase">STRICT NON-ASSERTION</div>
            <div className="font-mono text-[0.6875rem] text-neutral/70">ZERO SPECULATION POLICY</div>
          </div>
        </div>
      </section>
      
    </PageFrame>
  );
}
