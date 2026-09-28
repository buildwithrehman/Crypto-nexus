import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, ApiError, RunResponse, AlertSummary } from '../lib/api';
import { PageFrame } from '../layouts/PageFrame';
import { SystemState } from '../components/ui/SystemState';
import { EpistemicBoundary } from '../components/ui/EpistemicBoundary';
import { useRunContext } from '../contexts/RunContext';
import { RunProgress } from '../components/ui/RunProgress';
import { useRef } from 'react';

export function CommandCenter() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setLocalRun] = useState<RunResponse | null>(null);
  
  // Alert queue states
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [stats, setStats] = useState<RunStats | null>(null);
  const [alertTotal, setAlertTotal] = useState<number | null>(null);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [alertsError, setAlertsError] = useState(false);

  // Run states
  const [loading, setLoading] = useState(true);
  const [runErrorState, setRunErrorState] = useState<'NONE' | 'RUN_UNAVAILABLE' | 'ERROR'>('NONE');
  
  const { setRun } = useRunContext();
  const pollTimerRef = useRef<number | null>(null);

  useEffect(() => {
    async function loadData() {
      if (!runId) return;
      
      setRunErrorState('NONE');
      setLoading(true);
      setAlertsError(false);
      setAlertsLoading(true);

      let runData;
      try {
        runData = await apiClient.getRun(runId);
        if (runData.status === 'COMPLETED') {
            try {
                const s = await apiClient.getRunStats(runId);
                setStats(s);
            } catch (e) {
                console.error(e);
            }
        }
        setLocalRun(runData);
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
        setLoading(false);
        return; // Abort
      }

      setLoading(false);

      if (runData.status === 'QUEUED' || runData.status === 'RUNNING') {
         pollTimerRef.current = window.setTimeout(loadData, 2000);
         return; // Do not load alerts yet
      }

      if (runData.status !== 'COMPLETED') {
         return;
      }

      // Load alerts independently so it doesn't fail the whole page
      try {
        const alertsData = await apiClient.getAlerts(runId, 5, 0);
        setAlerts(alertsData.data || []);
        setAlertTotal(alertsData.total ?? null);
      } catch (err) {
        console.error(err);
        setAlertsError(true);
      } finally {
        setAlertsLoading(false);
      }
    }
    loadData();
    if (run && run.status !== 'COMPLETED') {
    return (
      <PageFrame>
        <main className="w-full flex flex-col p-4 sm:p-8">
          <RunProgress run={run} />
        </main>
      </PageFrame>
    );
  }

  return () => setRun(undefined);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId, setRun]);

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, []);

  if (loading) return <PageFrame><SystemState type="LOADING" /></PageFrame>;
  if (runErrorState !== 'NONE' || !run) {
    return <PageFrame><SystemState type={runErrorState === 'NONE' ? 'ERROR' : runErrorState} /></PageFrame>;
  }

  const isComplete = run.status === 'COMPLETED';

  const pipelineStages = [
    "01 INGESTION",
    "02 NETWORK OBSERVATIONS",
    "03 CORRELATION",
    "04 ENTITY CLUSTERING",
    "05 GRAPH ANALYSIS",
    "06 FEATURE EXTRACTION",
    "07 ML ANALYSIS",
    "08 EVIDENCE INTERPRETATION",
    "09 RUN FINALIZED"
  ];

  return (
    <PageFrame>
      <main className="w-full flex-1 max-w-[1440px] mx-auto flex flex-col gap-8">
        
        {/* EDITORIAL TITLE BLOCK */}
        <section className="border border-structural-border bg-neutral p-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-structural-border pb-6">
            <div>
              <div className="font-mono text-xs font-bold text-secondary uppercase tracking-widest mb-2 flex items-center gap-2">
                <span className="w-2 h-2 bg-secondary inline-block"></span>
                INVESTIGATION WORKSPACE
              </div>
              <h1 className="font-display text-5xl md:text-[5rem] md:leading-[5rem] text-secondary tracking-tight uppercase font-bold">
                COMMAND<br />CENTER
              </h1>
            </div>
            <div className="max-w-md">
              <p className="font-body text-[0.9375rem] text-secondary leading-relaxed border-l-2 border-primary pl-4">
                Review the active analysis run, structural anomaly alerts, graph relationships, and evidence available for investigation.
              </p>
            </div>
          </div>

          {/* PRIMARY DATA OVERVIEW */}
          <div className="grid grid-cols-2 md:grid-cols-5 border-t-0 border border-structural-border mt-6">
            <div className="p-5 border-r border-b md:border-b-0 border-structural-border bg-surface-accent">
              <div className="font-mono text-xs font-bold text-secondary uppercase mb-2">TRANSACTIONS</div>
              <div className="font-display text-[2.75rem] leading-[2.75rem] text-secondary font-bold tracking-tight">DYNAMIC</div>
              <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">BLOCKS [DYNAMIC]</div>
            </div>
            <div className="p-5 border-r border-b md:border-b-0 border-structural-border bg-surface-accent">
              <div className="font-mono text-xs font-bold text-secondary uppercase mb-2">NETWORK OBSERVATIONS</div>
              <div className="font-display text-[2.75rem] leading-[2.75rem] text-secondary font-bold tracking-tight">DYNAMIC</div>
              <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">NETWORK OBSERVATIONS</div>
            </div>
            <div className="col-span-2 md:col-span-1 p-5 border-r border-b md:border-b-0 border-structural-border bg-primary text-secondary relative flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold uppercase">ANOMALY ALERTS</span>
                  <span className="font-mono text-[0.6875rem] font-bold bg-secondary text-neutral px-1 py-0.5 uppercase">
                    [ PRIMARY QUEUE ]
                  </span>
                </div>
                <div className="font-display text-[2.75rem] leading-[2.75rem] font-bold tracking-tight">
                  {alertsError ? 'ERROR' : (alertTotal !== null ? alertTotal.toLocaleString() : 'DYNAMIC')}
                </div>
              </div>
              <div className="font-mono text-[0.6875rem] font-bold uppercase border-t border-secondary/30 pt-2 mt-2">
                MANUAL INVESTIGATION QUEUE
              </div>
            </div>
            <div className="p-5 border-r border-structural-border bg-surface-accent">
              <div className="font-mono text-xs font-bold text-secondary uppercase mb-2">OBSERVED PEERS</div>
              <div className="font-display text-[2.75rem] leading-[2.75rem] text-secondary font-bold tracking-tight">DYNAMIC</div>
              <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">UNIQUE OBSERVED PEER IPS</div>
            </div>
            <div className="p-5 bg-surface-accent">
              <div className="font-mono text-xs font-bold text-secondary uppercase mb-2">CONNECTED COMPONENTS</div>
              <div className="font-display text-[2.75rem] leading-[2.75rem] text-secondary font-bold tracking-tight">DYNAMIC</div>
              <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">TOPOLOGICAL SUBGRAPHS</div>
            </div>
          </div>
        </section>

        {/* PRIMARY INVESTIGATION AREA */}
        <section className="grid grid-cols-1 lg:grid-cols-12 border border-structural-border bg-neutral">
          {/* LEFT COLUMN */}
          <div className="lg:col-span-7 border-b lg:border-b-0 lg:border-r border-structural-border p-6 flex flex-col justify-between">
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-structural-border pb-4 mb-6">
                <div>
                  <div className="font-mono text-xs font-bold text-secondary uppercase">PRIMARY QUEUE</div>
                  <h2 className="font-display text-[2.25rem] leading-[2.5rem] font-semibold text-secondary uppercase tracking-tight">INVESTIGATION QUEUE</h2>
                  <p className="font-body text-[0.8125rem] text-muted-ink mt-1">
                    Structural outliers surfaced by the active analysis run for manual investigation.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Link to={`/runs/${runId}/alerts`} className="px-5 py-3 bg-secondary text-neutral hover:bg-primary hover:text-secondary font-mono text-xs font-bold uppercase transition-none border border-structural-border inline-block">
                    VIEW ALERT QUEUE ↗
                  </Link>
                </div>
              </div>

              <div className="flex items-center gap-4 bg-surface-accent border border-structural-border p-4 mb-6">
                <span className="text-primary text-3xl font-display font-bold">!</span>
                <div>
                  <div className="font-display text-lg text-secondary uppercase font-bold tracking-wide">
                    {alertsError ? 'ERROR: ' : (alertTotal !== null ? alertTotal.toLocaleString() + ' ' : 'DYNAMIC ')} Structural Anomaly Alerts
                  </div>
                  <div className="font-mono text-[0.6875rem] text-muted-ink">
                    Requires manual investigation. Filter by anomaly strength.
                  </div>
                </div>
              </div>
            </div>

            {/* MANUAL INVESTIGATION QUEUE PREVIEW TABLE */}
            <div className="border border-structural-border">
              <div className="grid grid-cols-12 bg-surface-accent border-b border-structural-border font-mono text-[0.6875rem] font-bold uppercase text-muted-ink p-2">
                <div className="col-span-2">RANK</div>
                <div className="col-span-6">TXID / ALERT ID</div>
                <div className="col-span-2">STRENGTH</div>
                <div className="col-span-2">EVIDENCE TIER</div>
              </div>

              {alertsLoading ? (
                <div className="p-8"><SystemState type="LOADING" /></div>
              ) : alertsError ? (
                <div className="p-8"><SystemState type="ERROR" /></div>
              ) : alerts.length === 0 ? (
                <div className="p-8"><SystemState type="NO_RESULTS" /></div>
              ) : (
                alerts.map((alert, idx) => (
                  <Link key={alert.alert_id} to={`/runs/${runId}/alerts/${alert.alert_id}`} className="grid grid-cols-12 border-b last:border-b-0 border-structural-border hover:bg-surface-accent transition-none cursor-pointer bg-neutral group">
                    <div className="col-span-2 p-3 flex flex-col justify-center">
                      <div className="font-display text-xl md:text-2xl font-bold text-secondary group-hover:text-primary">
                        {(alert.operational_queue_rank ?? (idx + 1)).toString().padStart(2, '0')}
                      </div>
                    </div>
                    <div className="col-span-6 p-3 flex flex-col justify-center gap-1 border-l border-structural-border">
                      <div className="font-mono text-xs font-bold text-primary truncate w-full pr-4">{alert.txid}</div>
                      <div className="font-mono text-[0.6875rem] text-muted-ink">{alert.alert_id}</div>
                    </div>
                    <div className="col-span-2 p-3 flex items-center justify-start border-l border-structural-border font-mono text-xs font-bold text-secondary">
                      {alert.anomaly_strength.toFixed(1)}
                    </div>
                    <div className="col-span-2 p-3 flex items-center justify-start border-l border-structural-border">
                      <span className="inline-block px-1.5 py-0.5 border border-structural-border bg-secondary text-neutral font-mono text-[0.6875rem] font-bold uppercase whitespace-nowrap">
                        {alert.evidential_strength_tier}
                      </span>
                    </div>
                  </Link>
                ))
              )}
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div className="lg:col-span-5 p-6 flex flex-col gap-6 bg-surface-accent">
            
            {/* CIH / ENTITY CLUSTERING SUMMARY */}
            <div className="border border-structural-border bg-neutral p-5">
              <div className="font-mono text-xs font-bold text-secondary uppercase mb-1">COMMON-CONTROL HYPOTHESIS</div>
              <h3 className="font-display text-[1.5rem] leading-[1.875rem] text-secondary uppercase mb-3 border-b border-structural-border pb-2">ENTITY CLUSTERS</h3>
              <div className="flex items-center gap-4 mb-3">
                <div className="font-display text-[2.75rem] leading-[2.75rem] font-bold text-secondary">DYNAMIC</div>
                <div className="font-mono text-[0.6875rem] text-muted-ink">
                  HEURISTIC CLUSTERS<br />IDENTIFIED
                </div>
              </div>
              <p className="font-body text-[0.8125rem] text-muted-ink">
                Graph-based structural relationships across observed peers, transaction records, and Bitcoin addresses.
              </p>
              <div className="mt-4 pt-3 border-t border-dashed border-structural-border/50 font-mono text-[0.6875rem] text-muted-ink uppercase">
                * Note: Bitcoin addresses are pseudonymous identifiers. Address ≠ wallet ≠ entity.
              </div>
            </div>

            {/* SYSTEM SPECIFICATIONS */}
            <div className="border border-structural-border bg-neutral flex flex-col">
              <div className="p-4 border-b border-structural-border bg-surface-accent">
                <div className="font-mono text-xs font-bold text-secondary uppercase">SYSTEM SPECIFICATION</div>
              </div>
              <div className="p-4 grid grid-cols-2 gap-y-3 font-mono text-[0.6875rem]">
                <div className="text-muted-ink uppercase">SOURCE</div>
                <div className="text-secondary font-bold truncate">{runId === 'DEMO_V1' ? 'DEMO DATASET' : 'LOCAL CSV UPLOAD'}</div>
                
                <div className="text-muted-ink uppercase">TRANSACTIONS</div>
                <div className="text-secondary font-bold">{stats ? stats.transactions.toLocaleString() : (isComplete ? '0' : 'PENDING')}</div>

                <div className="text-muted-ink uppercase">NETWORK OBS</div>
                <div className="text-secondary font-bold">{stats ? stats.network_obs.toLocaleString() : (isComplete ? '0' : 'PENDING')}</div>
                
                <div className="text-muted-ink uppercase">ALERTS</div>
                <div className="text-secondary font-bold">{stats ? stats.alerts.toLocaleString() : (isComplete ? '0' : 'PENDING')}</div>
                
                <div className="text-muted-ink uppercase">EVIDENCE</div>
                <div className="text-secondary font-bold">{stats ? stats.alert_evidence.toLocaleString() : (isComplete ? '0' : 'PENDING')}</div>


                
                <div className="text-muted-ink uppercase">MODEL</div>
                <div className="text-secondary font-bold">[DYNAMIC MODEL]</div>
                
                <div className="text-muted-ink uppercase">CLUSTERING</div>
                <div className="text-secondary font-bold">[DYNAMIC CLUSTERING]</div>

                <div className="text-muted-ink uppercase">DATABASE</div>
                <div className="text-secondary font-bold">DUCKDB</div>

                <div className="text-muted-ink uppercase">GEOIP</div>
                <div className="text-secondary font-bold">{run?.geoip_status || 'PENDING'}</div>
              </div>
            </div>

            {/* PIPELINE STATUS */}
            <div className="border border-structural-border bg-neutral">
              <div className="p-4 border-b border-structural-border bg-surface-accent">
                <div className="font-mono text-xs font-bold text-secondary uppercase flex justify-between items-center">
                  <span>PIPELINE STATUS</span>
                  <span className="bg-primary text-secondary px-1.5 py-0.5 text-[10px]">
                    {run.status}
                  </span>
                </div>
              </div>
              <div className="p-4 flex flex-col gap-2 font-mono text-[0.6875rem] uppercase text-muted-ink">
                {pipelineStages.map((stage, idx) => {
                  const isFinal = idx === pipelineStages.length - 1;
                  return (
                    <div key={stage} className={`flex justify-between items-center ${isFinal ? 'text-primary font-bold pt-2 border-t border-structural-border/30 mt-1' : ''}`}>
                      <span className={isComplete ? "text-secondary font-bold" : (isFinal ? "" : "text-secondary font-bold")}>{stage}</span> 
                      <span>{isComplete ? "✓" : "[DYNAMIC]"}</span>
                    </div>
                  );
                })}
              </div>
            </div>
            
          </div>
        </section>
        
        <EpistemicBoundary />
      </main>
    </PageFrame>
  );
}
