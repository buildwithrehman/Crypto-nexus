import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, ApiError, AlertDetail } from '../lib/api';
import { PageFrame } from '../layouts/PageFrame';
import { SystemState } from '../components/ui/SystemState';
import { EpistemicBoundary } from '../components/ui/EpistemicBoundary';
import { useRunContext } from '../contexts/RunContext';

export function AlertInvestigation() {
  const { runId, alertId } = useParams<{ runId: string; alertId: string }>();
  
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState<'NONE' | 'RUN_UNAVAILABLE' | 'ALERT_UNAVAILABLE' | 'ERROR'>('NONE');
  const [alert, setAlert] = useState<AlertDetail | null>(null);

  const { setRun } = useRunContext();

  useEffect(() => {
    async function loadData() {
      if (!runId || !alertId) return;
      setLoading(true);
      setErrorState('NONE');
      
      try {
        // 1. Resolve run context
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
        return; // Stop execution, run is unavailable
      }

      try {
        // 2. Resolve alert details
        const alertData = await apiClient.getAlert(runId, alertId);
        setAlert(alertData);
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

  if (loading) return <PageFrame><SystemState type="LOADING" /></PageFrame>;
  
  if (errorState !== 'NONE' || !alert) {
    if (errorState === 'RUN_UNAVAILABLE') {
      return <PageFrame><SystemState type="RUN_UNAVAILABLE" /></PageFrame>;
    }
    return (
      <PageFrame>
        <SystemState type={errorState === 'ALERT_UNAVAILABLE' ? 'ERROR' : 'ERROR'} />
      </PageFrame>
    );
  }

  const maxAbsShap = alert.key_drivers?.length 
    ? Math.max(...alert.key_drivers.map(d => Math.abs(d.shap_value))) 
    : 0;

  const hasMLDerived = alert.evidence?.some(e => e.evidence_category === 'ML_DERIVED' || e.provenance_type === 'ML_DERIVED') 
    ? 'PRESENT' 
    : '[DYNAMIC]';

  return (
    <PageFrame>
      {/* 3. INVESTIGATION BREADCRUMB / STEPPER */}
      <div className="w-full bg-surface-accent border-b border-structural-border px-6 py-2.5 flex items-center justify-between">
        <div className="flex flex-wrap items-center space-x-2 font-mono text-[0.6875rem] font-bold">
          <span className="text-muted-ink">INVESTIGATIONS</span>
          <span className="text-muted-ink">→</span>
          <Link className="text-muted-ink hover:text-secondary" to={`/runs/${runId}/alerts`}>ALERT QUEUE</Link>
          <span className="text-muted-ink">→</span>
          <span className="text-secondary bg-neutral border border-structural-border px-2 py-0.5 border-b-2 border-b-primary">ALERT INVESTIGATION</span>
        </div>
        <div className="hidden sm:block font-mono text-[0.6875rem] text-muted-ink">ACTIVE RUN: {runId}</div>
      </div>

      <main className="w-full max-w-[1440px] mx-auto px-6 py-6 flex-grow space-y-6">
        
        {/* 4. PAGE IDENTITY */}
        <div className="flex flex-col md:flex-row md:items-end justify-between pb-4 border-b border-structural-border gap-4">
          <div>
            <div className="font-mono text-[0.6875rem] font-bold uppercase tracking-widest text-primary mb-1">
              STRUCTURAL ANOMALY REVIEW
            </div>
            <h1 className="font-display text-4xl text-secondary tracking-tight uppercase font-bold">
              ALERT INVESTIGATION
            </h1>
            <p className="font-body text-[0.9375rem] text-muted-ink mt-1 max-w-xl">
              Inspect the structural evidence and model-derived drivers associated with the selected alert.
            </p>
          </div>
          <div className="flex items-center self-start md:self-end">
            <div className="bg-surface-accent border border-structural-border px-3 py-2 font-mono text-[0.6875rem] font-bold text-secondary text-right">
              <div className="text-muted-ink">ACTIVE INVESTIGATION RECORD</div>
              <div>ALERT ID: <span className="text-primary">{alert.alert_id}</span> &nbsp;|&nbsp; ACTIVE RUN: {runId}</div>
            </div>
          </div>
        </div>

        {/* 5. PRIMARY ALERT HEADER & EPISTEMIC MICRO-NOTICE */}
        <div className="border border-structural-border bg-neutral">
          <div className="grid grid-cols-1 lg:grid-cols-12 border-b border-structural-border">
            <div className="lg:col-span-8 p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="bg-secondary text-neutral font-mono text-[0.6875rem] font-bold px-2 py-0.5 uppercase">
                    SELECTED ALERT
                  </span>
                </div>
                <div className="font-display text-2xl uppercase text-secondary tracking-tight mt-1 font-bold">
                  TXID: <span className="font-mono text-[0.9375rem] text-secondary break-all">{alert.txid}</span>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 pt-3 border-t border-dashed border-structural-border">
                <div className="font-mono text-[0.6875rem]">
                  <span className="text-muted-ink block">NETWORK TIMING:</span>
                  <span className="font-bold text-secondary">[DYNAMIC]</span>
                </div>
                <div className="font-mono text-[0.6875rem]">
                  <span className="text-muted-ink block">EVIDENCE TIER:</span>
                  <span className="font-bold text-secondary">{alert.evidential_strength_tier}</span>
                </div>
              </div>
            </div>
            <div className="lg:col-span-4 bg-primary text-secondary p-5 border-t lg:border-t-0 lg:border-l border-structural-border flex flex-col justify-between">
              <div>
                <div className="font-mono text-[0.6875rem] font-bold tracking-wider uppercase">
                  STRUCTURAL RARITY
                </div>
                <div className="font-display text-[2.75rem] leading-[2.75rem] font-bold text-secondary my-1">
                  {alert.anomaly_strength.toFixed(1)}
                </div>
              </div>
              <div className="font-mono text-[0.6875rem] pt-2 border-t border-structural-border/50">
                ANOMALY STRENGTH INDEX. Structural rarity relative to the model reference population.
              </div>
            </div>
          </div>
          <div className="bg-surface-accent px-4 py-2 flex items-start sm:items-center gap-3">
            <span className="bg-secondary text-neutral font-mono text-[0.6875rem] font-bold px-1.5 py-0.5 mt-0.5 sm:mt-0">NOTICE</span>
            <p className="font-mono text-[0.6875rem] font-bold text-secondary">
              STRUCTURAL ANOMALY ≠ CRIMINAL ACTIVITY — CryptoNexus surfaces patterns for human investigation. It does not determine identity, ownership or criminal intent.
            </p>
          </div>
        </div>

        {/* 6. MAIN INVESTIGATION GRID (8:4 ASYMMETRIC SPLIT) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* LEFT COLUMN (~8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* 6.A: SHAP DRIVERS */}
            <div className="border border-structural-border bg-neutral">
              <div className="bg-surface-accent px-4 py-3 border-b border-structural-border flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 bg-primary inline-block"></span>
                  <h2 className="font-display text-lg font-bold text-secondary uppercase">
                    WHY THIS ALERT WAS SURFACED // SHAP DRIVERS
                  </h2>
                </div>
                <span className="font-mono text-[0.6875rem] font-bold text-muted-ink">
                  CANONICAL FEATURE CONTRIBUTION
                </span>
              </div>
              <div className="p-4 border-b border-dashed border-structural-border bg-surface-accent">
                <p className="font-body text-[0.8125rem] text-muted-ink">Model-derived structural drivers associated with this alert.</p>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-accent font-mono text-[0.6875rem] font-bold text-secondary border-b-2 border-structural-border">
                      <th className="p-3">FEATURE</th>
                      <th className="p-3">DIR</th>
                      <th className="p-3 w-48">SHAP CONTRIBUTION</th>
                      <th className="p-3">SEMANTIC INTERPRETATION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y border-structural-border font-body text-[0.8125rem]">
                    {alert.key_drivers && alert.key_drivers.length > 0 ? (
                      alert.key_drivers.map((driver, idx) => {
                        const isPositive = driver.shap_value > 0;
                        const w = maxAbsShap > 0 ? (Math.abs(driver.shap_value) / maxAbsShap) * 100 : 0;
                        return (
                          <tr key={idx} className="hover:bg-surface-accent">
                            <td className="p-3 font-mono text-[0.6875rem] font-bold text-secondary break-all">{driver.feature}</td>
                            <td className="p-3 font-mono font-bold text-secondary">{driver.direction === 'positive' ? 'POS' : 'NEG'}</td>
                            <td className="p-3">
                              <div className="flex items-center gap-2">
                                <div className="w-24 bg-structural-border h-3 relative">
                                  <div className={`h-3 ${isPositive ? 'bg-primary' : 'bg-muted-ink'}`} style={{ width: `${w}%` }}></div>
                                </div>
                                <span className="font-mono text-[0.6875rem]">{driver.shap_value.toFixed(4)}</span>
                              </div>
                            </td>
                            <td className="p-3 text-muted-ink">{driver.meaning}</td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={4} className="p-3 font-mono text-[0.6875rem] text-muted-ink text-center">
                          DYNAMIC / NOT AVAILABLE
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 6.B: EVIDENCE AGGREGATION MATRIX */}
            <div className="border border-structural-border bg-neutral">
              <div className="bg-surface-accent px-4 py-3 border-b border-structural-border flex items-center justify-between">
                <h2 className="font-display text-lg font-bold text-secondary uppercase">
                  EVIDENCE AGGREGATION MATRIX
                </h2>
                <span className="font-mono text-[0.6875rem] text-muted-ink">
                  MULTI-VECTOR EVIDENCE AUDIT
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-accent font-mono text-[0.6875rem] font-bold text-secondary border-b border-structural-border">
                      <th className="p-3">EVIDENCE CATEGORY</th>
                      <th className="p-3">TYPE</th>
                      <th className="p-3">STATUS</th>
                      <th className="p-3">SOURCE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y border-dashed border-structural-border font-body text-[0.8125rem]">
                    {alert.evidence && alert.evidence.length > 0 ? (
                      alert.evidence.map((ev, idx) => (
                        <tr key={idx} className="hover:bg-surface-accent">
                          <td className="p-3 font-bold text-secondary">{ev.evidence_category}</td>
                          <td className="p-3">
                            <span className="border border-structural-border px-1.5 py-0.5 font-mono text-[0.6875rem]">
                              {ev.provenance_type}
                            </span>
                          </td>
                          <td className="p-3 font-mono text-[0.6875rem] font-bold text-secondary break-all">
                            {ev.derived_value || ev.original_value || ev.uncertainty_semantics || '[DYNAMIC]'}
                          </td>
                          <td className="p-3 font-mono text-[0.6875rem] text-muted-ink max-w-[12rem] truncate">
                            {ev.source_file ? `${ev.source_file}:${ev.source_row || '?'}` : ev.underlying_evidence_references?.join(', ') || '[DYNAMIC PROVENANCE]'}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="p-3 font-mono text-[0.6875rem] text-muted-ink text-center">
                          DYNAMIC / NOT AVAILABLE
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 6.C: ANALYTICAL INTERPRETATION & INVESTIGATIVE LEAD */}
            <div className="space-y-4">
              <div className="border border-structural-border bg-neutral p-4">
                <div className="flex items-center justify-between pb-2 border-b border-structural-border mb-3">
                  <span className="font-mono text-[0.6875rem] font-bold uppercase tracking-wider text-secondary">
                    ANALYTICAL INTERPRETATION
                  </span>
                  <span className="font-mono text-[0.6875rem] text-muted-ink">
                    EVIDENCE INTERPRETATION
                  </span>
                </div>
                <p className="font-body text-[0.9375rem] text-secondary leading-relaxed font-bold">
                  {alert.summary || '[DYNAMIC INTERPRETATION]'}
                </p>
                <div className="mt-4 pt-3 border-t border-dashed border-structural-border font-mono text-[0.6875rem] text-muted-ink">
                  INTERPRETATION BASIS: <span className="text-secondary font-bold">[DYNAMIC]</span>
                </div>
              </div>

              <div className="border border-structural-border bg-surface-accent p-4">
                <div className="flex items-center justify-between pb-2 border-b border-structural-border mb-3">
                  <span className="font-mono text-[0.6875rem] font-bold uppercase tracking-wider text-primary">
                    INVESTIGATIVE LEAD
                  </span>
                  <span className="bg-secondary text-neutral font-mono text-[0.6875rem] font-bold px-2 py-0.5">
                    LEAD STATUS: REQUIRES HUMAN REVIEW
                  </span>
                </div>
                <p className="font-body text-[0.9375rem] text-secondary font-medium">
                  {alert.human_readable_lead || '[DYNAMIC HUMAN-READABLE LEAD]'}
                </p>
              </div>
            </div>

            {/* 6.D: CAVEATS & LIMITATIONS */}
            <div className="border border-structural-border bg-neutral p-4">
              <div className="flex items-center gap-2 pb-2 border-b border-structural-border mb-3">
                <span className="font-mono text-secondary font-bold">!</span>
                <span className="font-mono text-[0.6875rem] font-bold uppercase tracking-wider text-secondary">
                  CAVEATS & STRUCTURAL LIMITATIONS
                </span>
              </div>
              <div className="font-body text-[0.8125rem] text-muted-ink space-y-2">
                {alert.investigation_caveats && alert.investigation_caveats.length > 0 ? (
                  <ul className="list-disc pl-4 space-y-1">
                    {alert.investigation_caveats.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                ) : (
                  <p>[DYNAMIC CAVEATS]</p>
                )}
                <div className="p-3 bg-surface-accent border border-dashed border-structural-border font-mono text-[0.6875rem] text-secondary leading-normal mt-3">
                  <strong>CONCEPTUAL BOUNDARIES:</strong> Bitcoin addresses are pseudonymous identifiers. Address ≠ wallet ≠ entity. IP association ≠ ownership. GeoIP is enrichment, not identity. Network observation time is sensor observation time. Anomaly ≠ crime.
                </div>
              </div>
            </div>

          </div>

          {/* RIGHT COLUMN (~4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* ALERT RECORD CARD */}
            <div className="border border-structural-border bg-neutral">
              <div className="bg-secondary text-neutral px-4 py-2.5 flex items-center justify-between">
                <span className="font-mono text-[0.6875rem] font-bold uppercase tracking-wider">INVESTIGATIVE RECORD</span>
                <span className="font-mono text-[0.6875rem]">{alert.alert_id.substring(0,8)}</span>
              </div>
              <div className="p-4 space-y-3 font-mono text-[0.6875rem]">
                <div className="pb-2 border-b border-dashed border-structural-border flex justify-between">
                  <span className="text-muted-ink">ALERT ID:</span>
                  <span className="font-bold text-secondary max-w-[12rem] truncate">{alert.alert_id}</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border">
                  <span className="text-muted-ink block mb-0.5">TXID:</span>
                  <span className="font-bold text-secondary break-all">{alert.txid}</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border flex justify-between items-center">
                  <span className="text-muted-ink">ANOMALY STRENGTH:</span>
                  <span className="bg-primary text-secondary font-bold px-1.5 py-0.5">{alert.anomaly_strength.toFixed(1)}</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border flex justify-between">
                  <span className="text-muted-ink">EVIDENCE TIER:</span>
                  <span className="font-bold text-secondary">{alert.evidential_strength_tier}</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border flex justify-between">
                  <span className="text-muted-ink">NETWORK TIMING:</span>
                  <span className="font-bold text-secondary">[DYNAMIC]</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border flex justify-between">
                  <span className="text-muted-ink">ACTIVE RUN:</span>
                  <span className="font-bold text-secondary max-w-[12rem] truncate">{runId}</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border flex justify-between">
                  <span className="text-muted-ink">MODEL:</span>
                  <span className="font-bold text-secondary">{alert.model_version || '[DYNAMIC / NOT AVAILABLE]'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-ink">DATASET:</span>
                  <span className="font-bold text-secondary">[DYNAMIC SOURCE]</span>
                </div>
              </div>
            </div>

            {/* PROVENANCE & AUDIT TRACEABILITY */}
            <div className="border border-structural-border bg-neutral">
              <div className="bg-surface-accent px-4 py-2.5 border-b border-structural-border flex items-center justify-between">
                <span className="font-mono text-[0.6875rem] font-bold uppercase tracking-wider text-secondary">
                  AUDIT TRACEABILITY
                </span>
                <span className="text-muted-ink font-mono text-[0.6875rem]">LOCAL DUCKDB</span>
              </div>
              <div className="p-4 space-y-3 font-mono text-[0.6875rem]">
                <div className="pb-2 border-b border-dashed border-structural-border">
                  <span className="text-muted-ink block">SOURCE RECORDS:</span>
                  <span className="font-bold text-secondary">[DYNAMIC COUNT]</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border">
                  <span className="text-muted-ink block">PRIMARY / REPRESENTATIVE SOURCE FILE:</span>
                  <span className="font-bold text-secondary break-all">{alert.evidence?.[0]?.source_file || '[DYNAMIC]'}</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border">
                  <span className="text-muted-ink block">PRIMARY / REPRESENTATIVE SOURCE RECORD:</span>
                  <span className="font-bold text-secondary">{alert.evidence?.[0]?.source_row || '[DYNAMIC]'}</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border">
                  <span className="text-muted-ink block">RUN ID:</span>
                  <span className="font-bold text-secondary truncate block">{runId}</span>
                </div>
                <div className="pb-2 border-b border-dashed border-structural-border">
                  <span className="text-muted-ink block">EVIDENCE ARTIFACTS:</span>
                  <span className="font-bold text-secondary">{alert.evidence?.length || 0} RECORDS</span>
                </div>
                <div>
                  <span className="text-muted-ink block">MODEL-DERIVED EVIDENCE:</span>
                  <span className="font-bold text-secondary">{hasMLDerived}</span>
                </div>
              </div>
            </div>

            {/* CONTINUE INVESTIGATION */}
            <div className="border border-structural-border bg-neutral p-4 space-y-3">
              <div className="font-mono text-[0.6875rem] font-bold uppercase tracking-wider text-secondary pb-2 border-b border-structural-border">
                CONTINUE INVESTIGATION
              </div>
              <p className="font-body text-[0.8125rem] text-muted-ink">
                Continue investigation using transaction structure, network relationships, and evidence provenance.
              </p>
              <div className="space-y-2 pt-2">
                <Link className="w-full flex items-center justify-between p-3 bg-secondary text-neutral font-mono text-[0.6875rem] font-bold hover:bg-primary hover:text-secondary border border-structural-border" to={`/runs/${runId}/transactions/${alert.txid}`}>
                  <span>TRANSACTION INVESTIGATION</span>
                  <span>↗</span>
                </Link>
                <Link className="w-full flex items-center justify-between p-3 bg-neutral text-secondary font-mono text-[0.6875rem] font-bold hover:bg-surface-accent border border-structural-border" to={`/runs/${runId}/transactions/${alert.txid}/graph`}>
                  <span>NETWORK GRAPH</span>
                  <span>↗</span>
                </Link>
                <Link className="w-full flex items-center justify-between p-3 bg-neutral text-secondary font-mono text-[0.6875rem] font-bold hover:bg-surface-accent border border-structural-border" to={`/runs/${runId}/alerts/${alertId}/provenance`}>
                  <span>EVIDENCE & PROVENANCE</span>
                  <span>↗</span>
                </Link>
              </div>
            </div>

          </div>
        </div>

        {/* 7. INVESTIGATION FLOW WORKFLOW STRIP */}
        <div className="border border-structural-border bg-neutral p-4 mt-6">
          <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase tracking-wider mb-3">
            SYSTEM WORKFLOW PROGRESSION
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2 font-mono text-[0.6875rem] font-bold">
            <Link to={`/runs/${runId}/alerts`} className="p-2.5 border border-structural-border bg-surface-accent text-muted-ink flex items-center gap-2 hover:bg-neutral">
              <span className="w-4 h-4 bg-structural-border flex items-center justify-center text-secondary">1</span>
              <span>ALERT QUEUE</span>
            </Link>
            <div className="p-2.5 border border-structural-border bg-primary text-secondary flex items-center gap-2">
              <span className="w-4 h-4 bg-secondary flex items-center justify-center text-neutral">2</span>
              <span>ALERT INVESTIGATION</span>
            </div>
            <Link to={`/runs/${runId}/transactions/${alert.txid}`} className="p-2.5 border border-structural-border bg-neutral text-secondary flex items-center gap-2 hover:bg-surface-accent">
              <span className="w-4 h-4 bg-surface-accent flex items-center justify-center">3</span>
              <span>TX INVESTIGATION</span>
            </Link>
            <div className="p-2.5 border border-structural-border bg-neutral text-muted-ink flex items-center gap-2 opacity-50 cursor-not-allowed">
              <span className="w-4 h-4 bg-surface-accent flex items-center justify-center">4</span>
              <span>NETWORK GRAPH</span>
            </div>
            <div className="p-2.5 border border-structural-border bg-neutral text-muted-ink flex items-center gap-2 opacity-50 cursor-not-allowed">
              <span className="w-4 h-4 bg-surface-accent flex items-center justify-center">5</span>
              <span>PROVENANCE</span>
            </div>
          </div>
        </div>

        <EpistemicBoundary />

      </main>
    </PageFrame>
  );
}
