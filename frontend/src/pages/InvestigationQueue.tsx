import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, ApiError, AlertSummary } from '../lib/api';
import { PageFrame } from '../layouts/PageFrame';
import { SystemState } from '../components/ui/SystemState';
import { EpistemicBoundary } from '../components/ui/EpistemicBoundary';
import { useRunContext } from '../contexts/RunContext';

export function InvestigationQueue() {
  const { runId } = useParams<{ runId: string }>();
  
  // States
  const [loadingRun, setLoadingRun] = useState(true);
  const [runErrorState, setRunErrorState] = useState<'NONE' | 'RUN_UNAVAILABLE' | 'ERROR'>('NONE');
  
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [totalAlerts, setTotalAlerts] = useState<number>(0);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [alertsError, setAlertsError] = useState(false);
  
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  const { setRun } = useRunContext();

  // Load run context
  useEffect(() => {
    async function loadRun() {
      if (!runId) return;
      setLoadingRun(true);
      setRunErrorState('NONE');
      try {
        const runData = await apiClient.getRun(runId);
        setRun({
          id: runData.run_id,
          status: runData.status
        });
      } catch (err: unknown) {
        console.error(err);
        setRun(undefined);
        if (err instanceof ApiError && err.status === 404) {
          setRunErrorState('RUN_UNAVAILABLE');
        } else {
          setRunErrorState('ERROR');
        }
      } finally {
        setLoadingRun(false);
      }
    }
    loadRun();
    return () => setRun(undefined);
  }, [runId, setRun]);

  // Load alerts
  useEffect(() => {
    async function loadAlerts() {
      if (!runId || runErrorState !== 'NONE') return;
      setAlertsLoading(true);
      setAlertsError(false);
      try {
        const alertsData = await apiClient.getAlerts(runId, limit, offset);
        setAlerts(alertsData.data || []);
        setTotalAlerts(alertsData.total || 0);
      } catch (err) {
        console.error(err);
        setAlertsError(true);
      } finally {
        setAlertsLoading(false);
      }
    }
    loadAlerts();
  }, [runId, limit, offset, runErrorState]);

  if (loadingRun) return <PageFrame><SystemState type="LOADING" /></PageFrame>;
  if (runErrorState !== 'NONE') {
    return <PageFrame><SystemState type={runErrorState === 'NONE' ? 'ERROR' : runErrorState} /></PageFrame>;
  }

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(totalAlerts / limit) || 1;

  const handleNextPage = () => {
    if (currentPage < totalPages) setOffset(offset + limit);
  };
  const handlePrevPage = () => {
    if (currentPage > 1) setOffset(offset - limit);
  };
  const handlePageClick = (page: number) => {
    setOffset((page - 1) * limit);
  };

  return (
    <PageFrame>
      <main className="w-full flex-1 max-w-[1440px] mx-auto flex flex-col gap-8">
        
        {/* EDITORIAL TITLE BLOCK */}
        <section className="border border-structural-border bg-neutral p-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-structural-border pb-6">
            <div>
              <div className="font-mono text-xs font-bold text-secondary uppercase tracking-widest mb-2 flex items-center gap-2">
                <span className="w-2 h-2 bg-secondary inline-block"></span>
                ACTIVE QUEUE
              </div>
              <h1 className="font-display text-5xl md:text-[5rem] md:leading-[5rem] text-secondary tracking-tight uppercase font-bold">
                INVESTIGATION<br />QUEUE
              </h1>
            </div>
            <div className="max-w-md">
              <p className="font-body text-[0.9375rem] text-secondary leading-relaxed border-l-2 border-primary pl-4">
                Prioritized queue of structurally anomalous transactions flagged for manual review by the active analytical model.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 border-t-0 border border-structural-border mt-6">
            <div className="p-5 border-r border-b sm:border-b-0 border-structural-border bg-primary text-secondary">
              <div className="font-mono text-xs font-bold uppercase mb-1">ANOMALY ALERTS</div>
              <div className="font-display text-[2.75rem] leading-[2.75rem] font-bold mb-1">
                {alertsError ? 'ERROR' : totalAlerts.toLocaleString()}
              </div>
              <div className="font-mono text-[0.6875rem] uppercase tracking-wide">SURFACED IN ACTIVE QUEUE</div>
            </div>
            <div className="p-5 border-r border-b sm:border-b-0 border-structural-border bg-surface-accent">
              <div className="font-mono text-xs font-bold uppercase mb-1 text-secondary">TRANSACTIONS ANALYZED</div>
              <div className="font-display text-[2.75rem] leading-[2.75rem] font-bold text-secondary mb-1">DYNAMIC</div>
              <div className="font-mono text-[0.6875rem] uppercase text-muted-ink tracking-wide">SOURCE RANGE COVERAGE</div>
            </div>
            <div className="p-5 border-r border-b sm:border-b-0 border-structural-border bg-surface-accent">
              <div className="font-mono text-xs font-bold uppercase mb-1 text-secondary">ANOMALY RATE</div>
              <div className="font-display text-[2.75rem] leading-[2.75rem] font-bold text-secondary mb-1">DYNAMIC</div>
              <div className="font-mono text-[0.6875rem] uppercase text-muted-ink tracking-wide">ANOMALY RATE IN ACTIVE RUN</div>
            </div>
            <div className="p-5 flex flex-col justify-between bg-surface-accent">
              <div>
                <div className="font-mono text-xs font-bold uppercase mb-1 text-secondary">ANOMALY MODEL</div>
                <div className="font-display text-2xl leading-tight uppercase font-bold text-secondary">[DYNAMIC MODEL]</div>
              </div>
              <div className="font-mono text-[0.6875rem] text-muted-ink uppercase tracking-tight mt-2">
                Note: Structural rarity vs reference baseline.
              </div>
            </div>
          </div>
        </section>

        {/* WORKFLOW NAVIGATION STEPPER */}
        <div className="w-full border border-structural-border bg-neutral px-4 py-2.5 mb-6 overflow-x-auto">
          <div className="flex items-center gap-2 font-mono text-[0.6875rem] font-bold uppercase tracking-wider text-muted-ink whitespace-nowrap">
            <span className="bg-secondary text-neutral px-2 py-0.5">1. ALERT QUEUE</span>
            <span>→</span>
            <span className="cursor-not-allowed">2. ALERT INVESTIGATION</span>
            <span>→</span>
            <span className="cursor-not-allowed">3. TRANSACTION INVESTIGATION</span>
            <span>→</span>
            <span className="cursor-not-allowed">4. NETWORK GRAPH</span>
            <span>→</span>
            <span className="cursor-not-allowed">5. EVIDENCE & PROVENANCE</span>
          </div>
        </div>

        {/* MAIN EDITORIAL ASYMMETRIC GRID (9:3 Desktop Split) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* LEFT PRIMARY DATA CANVAS (Col 9) */}
          <div className="lg:col-span-9 flex flex-col">
            
            {/* FILTER & CONTROLS TOOLBAR */}
            <div className="border border-structural-border bg-neutral p-4 mb-0 border-b-0">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center flex-1 min-w-[280px]">
                  <div className="relative w-full">
                    <input 
                      className="w-full bg-surface-accent border border-structural-border px-3 py-2 font-mono text-[0.6875rem] font-bold placeholder:text-muted-ink text-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary uppercase cursor-not-allowed opacity-50" 
                      placeholder="ENTER TXID (UNAVAILABLE)" 
                      type="text" 
                      disabled
                    />
                  </div>
                  <button disabled className="bg-secondary text-neutral font-mono text-[0.6875rem] font-bold px-4 py-2 border border-structural-border border-l-0 whitespace-nowrap cursor-not-allowed opacity-50">
                    SEARCH ↗
                  </button>
                </div>
                
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center border border-structural-border bg-surface-accent px-2 py-1 opacity-50 cursor-not-allowed">
                    <span className="font-mono text-[0.6875rem] text-muted-ink mr-2 uppercase">TIER:</span>
                    <select disabled className="bg-transparent font-mono text-[0.6875rem] font-bold uppercase focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary border-0 p-0 text-secondary pr-4 cursor-not-allowed">
                      <option>ALL (UNAVAILABLE)</option>
                    </select>
                  </div>
                  <div className="flex items-center border border-structural-border bg-surface-accent px-3 py-1 gap-2 opacity-50 cursor-not-allowed">
                    <span className="font-mono text-[0.6875rem] text-muted-ink uppercase">ANOMALY STRENGTH:</span>
                    <span className="font-mono text-[0.6875rem] text-muted-ink">0 ───────── 100</span>
                  </div>
                  <div className="flex items-center border border-structural-border bg-surface-accent px-2 py-1 opacity-50 cursor-not-allowed">
                    <span className="font-mono text-[0.6875rem] text-muted-ink mr-2 uppercase">NETWORK TIMING:</span>
                    <select disabled className="bg-transparent font-mono text-[0.6875rem] font-bold uppercase focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary border-0 p-0 text-secondary pr-4 cursor-not-allowed">
                      <option>ALL</option>
                    </select>
                  </div>
                  <button disabled className="border border-transparent px-3 py-1 font-mono text-[0.6875rem] font-bold text-muted-ink cursor-not-allowed">
                    CLEAR FILTERS
                  </button>
                </div>
              </div>
              
              <div className="mt-3 pt-3 border-t border-structural-border flex flex-wrap items-center justify-between font-mono text-[0.6875rem] text-muted-ink gap-2">
                <div>
                  QUEUE: <strong className="text-secondary">{alertsError ? 'ERROR' : `${totalAlerts.toLocaleString()} ALERTS`}</strong> | ACTIVE RUN: <strong className="text-secondary">{runId}</strong> | DATA: <strong className="text-secondary">[DYNAMIC SOURCE]</strong> | MODEL: <strong className="text-secondary">[DYNAMIC MODEL]</strong>
                </div>
                <div className="font-mono text-[0.625rem] font-bold text-primary tracking-wider uppercase">
                  DYNAMIC BACKEND DATA — POPULATED VIA DUCKDB / API
                </div>
              </div>
            </div>

            {/* HIGH-DENSITY EDITORIAL DATA TABLE */}
            <div className="w-full overflow-x-auto border border-structural-border bg-neutral">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-accent border-b-2 border-structural-border font-mono text-[0.6875rem] font-bold text-secondary uppercase">
                    <th className="py-3 px-3 border-r border-structural-border w-12 text-center">#</th>
                    <th className="py-3 px-4 border-r border-structural-border w-44">TXID</th>
                    <th className="py-3 px-3 border-r border-structural-border w-36">
                      ANOMALY STRENGTH
                      <span className="block font-mono text-[0.625rem] text-muted-ink font-normal tracking-tight">STRUCTURAL RARITY</span>
                    </th>
                    <th className="py-3 px-3 border-r border-structural-border w-32">EVIDENCE TIER</th>
                    <th className="py-3 px-3 border-r border-structural-border w-36">NETWORK TIMING</th>
                    <th className="py-3 px-4 border-r border-structural-border">TOP STRUCTURAL REASON</th>
                    <th className="py-3 px-3 text-right w-24">ACTION</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-[0.6875rem] divide-y divide-structural-border">
                  {alertsLoading ? (
                    <tr><td colSpan={7} className="p-8"><SystemState type="LOADING" /></td></tr>
                  ) : alertsError ? (
                    <tr><td colSpan={7} className="p-8"><SystemState type="ERROR" /></td></tr>
                  ) : alerts.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8">
                        <div className="flex flex-col items-center justify-center text-center">
                          <h2 className="font-display text-2xl font-bold text-secondary uppercase mb-2">NO ALERTS IN ACTIVE RUN</h2>
                          <p className="font-body text-sm text-muted-ink max-w-md">No anomaly alert records are currently available for this run.</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    alerts.map((alert, idx) => (
                      <tr key={alert.alert_id} className="hover:bg-surface-accent transition-none">
                        <td className="py-2.5 px-3 border-r border-structural-border text-center font-bold text-muted-ink">
                          {(alert.operational_queue_rank ?? (offset + idx + 1)).toString().padStart(4, '0')}
                        </td>
                        <td className="py-2.5 px-4 border-r border-structural-border font-bold text-secondary">
                          <span className="bg-surface-accent px-1 py-0.5 truncate inline-block w-40">{alert.txid}</span>
                        </td>
                        <td className="py-2.5 px-3 border-r border-structural-border">
                          <div className="flex items-center gap-1.5 font-bold text-secondary">
                            <span className="inline-block w-2 h-2 bg-primary"></span>
                            <span>{alert.anomaly_strength.toFixed(1)}</span>
                          </div>
                        </td>
                        <td className="py-2.5 px-3 border-r border-structural-border">
                          <span className="border border-structural-border px-1.5 py-0.5 bg-neutral text-[0.625rem] font-bold uppercase">
                            {alert.evidential_strength_tier}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 border-r border-structural-border text-muted-ink">
                          [DYNAMIC]
                        </td>
                        <td className="py-2.5 px-4 border-r border-structural-border font-body text-[0.8125rem] text-secondary">
                          [DYNAMIC BACKEND EVIDENCE]
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <Link to={`/runs/${runId}/alerts/${alert.alert_id}`} className="border border-structural-border px-2 py-1 font-bold text-[0.6875rem] bg-secondary text-neutral hover:bg-primary hover:text-secondary transition-none whitespace-nowrap inline-block">
                            INSPECT ↗
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* PAGINATION & QUEUE STATUS FOOTER */}
            <div className="border border-t-0 border-structural-border bg-surface-accent p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="font-mono text-[0.6875rem] text-muted-ink uppercase">
                SHOWING <strong className="text-secondary">{alertsError ? 0 : alerts.length}</strong> OF {alertsError ? 'ERROR' : totalAlerts.toLocaleString()} ALERTS (PAGE {alertsError ? 0 : currentPage})
              </div>
              <div className="flex items-center gap-1 font-mono text-xs font-bold">
                <button 
                  onClick={handlePrevPage}
                  disabled={currentPage <= 1 || alertsError}
                  className={`border border-structural-border px-3 py-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center ${currentPage <= 1 || alertsError ? 'bg-neutral text-muted-ink cursor-not-allowed opacity-50' : 'bg-neutral text-secondary hover:bg-surface-accent'}`}
                >
                  PREVIOUS
                </button>
                <button className="border border-structural-border px-3 py-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center bg-secondary text-neutral">
                  {alertsError ? 0 : currentPage}
                </button>
                {totalPages > currentPage && (
                  <button onClick={() => handlePageClick(currentPage + 1)} className="border border-structural-border px-3 py-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center bg-neutral hover:bg-surface-accent text-secondary">
                    {currentPage + 1}
                  </button>
                )}
                {totalPages > currentPage + 1 && (
                  <button onClick={() => handlePageClick(currentPage + 2)} className="border border-structural-border px-3 py-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center bg-neutral hover:bg-surface-accent text-secondary">
                    {currentPage + 2}
                  </button>
                )}
                {totalPages > currentPage + 2 && (
                  <span className="px-2 font-mono text-secondary">...</span>
                )}
                {totalPages > currentPage + 2 && (
                  <button onClick={() => handlePageClick(totalPages)} className="border border-structural-border px-3 py-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center bg-neutral hover:bg-surface-accent text-secondary">
                    {totalPages}
                  </button>
                )}
                <button 
                  onClick={handleNextPage}
                  disabled={currentPage >= totalPages || alertsError}
                  className={`border border-structural-border px-3 py-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center transition-none ${currentPage >= totalPages || alertsError ? 'bg-neutral text-muted-ink cursor-not-allowed opacity-50' : 'bg-neutral text-secondary hover:bg-primary hover:text-secondary'}`}
                >
                  NEXT
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT SIDE CONTEXT STRIP & EVIDENCE LEGEND (Col 3) */}
          <aside className="lg:col-span-3 space-y-6">
            
            {/* CARD: WHAT IS AN ALERT */}
            <div className="border border-structural-border bg-neutral">
              <div className="bg-surface-accent px-4 py-2 border-b border-structural-border font-mono text-[0.6875rem] font-bold uppercase flex items-center justify-between text-secondary">
                <span>METHODOLOGICAL SCOPE</span>
                <span className="font-bold">?</span>
              </div>
              <div className="p-4 space-y-4">
                <div>
                  <div className="font-display text-lg uppercase font-bold text-secondary mb-1">WHAT IS AN ALERT?</div>
                  <p className="font-body text-[0.8125rem] text-muted-ink leading-relaxed">
                    An alert identifies a transaction whose structural feature profile was flagged as anomalous by the active Isolation Forest model.
                  </p>
                </div>
                <div className="border-t border-structural-border pt-3">
                  <div className="font-display text-lg uppercase font-bold text-secondary mb-1">WHAT IT DOES NOT MEAN</div>
                  <p className="font-body text-[0.8125rem] text-muted-ink leading-relaxed">
                    Anomaly does not establish identity, ownership, criminal intent, or criminal activity.
                  </p>
                </div>
              </div>
            </div>

            {/* CARD: EVIDENCE TIER HIERARCHY */}
            <div className="border border-structural-border bg-neutral">
              <div className="bg-surface-accent px-4 py-2 border-b border-structural-border font-mono text-[0.6875rem] font-bold uppercase flex items-center justify-between text-secondary">
                <span>EVIDENCE TIER HIERARCHY</span>
              </div>
              <div className="p-4 space-y-3 font-mono text-[0.6875rem]">
                <div className="border-b border-dashed border-structural-border pb-2">
                  <div className="font-bold text-secondary">1. OBSERVED</div>
                  <p className="text-muted-ink text-[0.6875rem] mt-0.5 leading-tight">Directly recorded source observations.</p>
                </div>
                <div className="border-b border-dashed border-structural-border pb-2">
                  <div className="font-bold text-secondary">2. DERIVED</div>
                  <p className="text-muted-ink text-[0.6875rem] mt-0.5 leading-tight">Features calculated from source records.</p>
                </div>
                <div className="border-b border-dashed border-structural-border pb-2">
                  <div className="font-bold text-secondary">3. HEURISTIC</div>
                  <p className="text-muted-ink text-[0.6875rem] mt-0.5 leading-tight">Deterministic analytical rules.</p>
                </div>
                <div className="border-b border-dashed border-structural-border pb-2">
                  <div className="font-bold text-secondary">4. ML_DERIVED</div>
                  <p className="text-muted-ink text-[0.6875rem] mt-0.5 leading-tight">Outputs derived from the analytical model.</p>
                </div>
                <div>
                  <div className="font-bold text-secondary">5. ENRICHED</div>
                  <p className="text-muted-ink text-[0.6875rem] mt-0.5 leading-tight">Additional contextual metadata.</p>
                </div>
              </div>
            </div>

            {/* ENGINE SPECIFICATION BRIEF */}
            <div className="border border-structural-border bg-surface-accent p-4 font-mono text-[0.6875rem]">
              <div className="font-bold uppercase text-secondary mb-2">ACTIVE RUN SPECIFICATION</div>
              <table className="w-full text-muted-ink text-[0.6875rem]">
                <tbody>
                  <tr className="border-b border-structural-border/50 py-1">
                    <td className="py-1">DATASET:</td>
                    <td className="py-1 text-right text-secondary font-bold truncate">[DYNAMIC SOURCE]</td>
                  </tr>
                  <tr className="border-b border-structural-border/50 py-1">
                    <td className="py-1">MODEL:</td>
                    <td className="py-1 text-right text-secondary font-bold truncate">[DYNAMIC MODEL]</td>
                  </tr>
                  <tr className="border-b border-structural-border/50 py-1">
                    <td className="py-1">DATABASE:</td>
                    <td className="py-1 text-right text-secondary font-bold">DUCKDB</td>
                  </tr>
                  <tr className="border-b border-structural-border/50 py-1">
                    <td className="py-1">FEATURES:</td>
                    <td className="py-1 text-right text-secondary font-bold">DYNAMIC</td>
                  </tr>
                  <tr>
                    <td className="py-1">GEOIP:</td>
                    <td className="py-1 text-right text-secondary font-bold">{run?.geoip_status || 'PENDING'}</td>
                  </tr>
                </tbody>
              </table>
            </div>

          </aside>
        </div>

        <EpistemicBoundary />
      </main>
    </PageFrame>
  );
}
