import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, ApiError, TransactionInvestigationResponse } from '../lib/api';
import { PageFrame } from '../layouts/PageFrame';
import { SystemState } from '../components/ui/SystemState';
import { EpistemicBoundary } from '../components/ui/EpistemicBoundary';
import { useRunContext } from '../contexts/RunContext';

export function TransactionInvestigation() {
  const { runId, txid } = useParams<{ runId: string; txid: string }>();
  
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState<'NONE' | 'RUN_UNAVAILABLE' | 'TRANSACTION_UNAVAILABLE' | 'ERROR'>('NONE');
  const [tx, setTx] = useState<TransactionInvestigationResponse | null>(null);

  const { setRun } = useRunContext();

  useEffect(() => {
    async function loadData() {
      if (!runId || !txid) return;
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
        const txData = await apiClient.getTransaction(runId, txid);
        setTx(txData);
      } catch (err: unknown) {
        console.error(err);
        if (err instanceof ApiError && err.status === 404) {
          setErrorState('TRANSACTION_UNAVAILABLE');
        } else {
          setErrorState('ERROR');
        }
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, [runId, txid, setRun]);

  if (loading) return <PageFrame><SystemState type="LOADING" /></PageFrame>;
  
  if (errorState !== 'NONE' || !tx) {
    if (errorState === 'RUN_UNAVAILABLE') {
      return <PageFrame><SystemState type="RUN_UNAVAILABLE" /></PageFrame>;
    }
    return (
      <PageFrame>
        <SystemState type={errorState === 'TRANSACTION_UNAVAILABLE' ? 'TRANSACTION_UNAVAILABLE' : 'ERROR'} />
      </PageFrame>
    );
  }

  const inputsCount = tx.inputs?.length || 0;
  const outputsCount = tx.outputs?.length || 0;
  const totalInputValue = tx.inputs?.reduce((acc, i) => acc + i.amount, 0) || 0;
  const totalOutputValue = tx.outputs?.reduce((acc, o) => acc + o.amount, 0) || 0;
  const obsCount = tx.observed_peers?.length || 0;
  const alertCount = tx.alerts?.length || 0;
  
  // Try to use the first alert context if present for Back button
  const firstAlertId = tx.alerts?.[0]?.alert_id;

  return (
    <PageFrame>
      {/* ==================== BREADCRUMB STRIP ==================== */}
      <div className="w-full bg-surface border-b border-structural-border px-6 py-2 flex flex-wrap items-center justify-between font-mono text-[0.6875rem] font-bold gap-3">
        <div className="flex items-center gap-2 text-secondary flex-wrap">
          <span className="text-muted-ink">INVESTIGATIONS</span>
          <span className="text-muted-ink">→</span>
          <Link className="text-muted-ink hover:text-secondary" to={`/runs/${runId}/alerts`}>ALERT QUEUE</Link>
          <span className="text-muted-ink">→</span>
          {firstAlertId ? (
            <Link className="text-muted-ink hover:text-secondary" to={`/runs/${runId}/alerts/${firstAlertId}`}>ALERT INVESTIGATION</Link>
          ) : (
            <span className="text-muted-ink">ALERT INVESTIGATION</span>
          )}
          <span className="text-muted-ink">→</span>
          <span className="bg-secondary text-neutral px-2 py-0.5 font-bold">TRANSACTION INVESTIGATION</span>
        </div>
        <div className="text-muted-ink">
          ACTIVE RUN: <span className="font-bold text-secondary">{runId}</span>
        </div>
      </div>

      <main className="flex-grow w-full max-w-[1440px] mx-auto p-6 flex flex-col gap-6">
        {/* PAGE TITLE & IDENTITY */}
        <div className="w-full border border-structural-border bg-neutral p-6 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div className="space-y-1">
            <div className="font-mono text-[0.6875rem] font-bold text-primary tracking-widest uppercase">
              STRUCTURAL FORENSIC AUDIT
            </div>
            <h1 className="font-display text-4xl tracking-tight uppercase text-secondary font-bold">
              TRANSACTION STRUCTURE REVIEW
            </h1>
            <p className="font-body text-[0.9375rem] text-muted-ink max-w-3xl mt-2">
              Inspect the selected Bitcoin transaction, its observable inputs and outputs, associated network observations, and graph relationships.
            </p>
          </div>
          <div className="border border-structural-border bg-surface-accent p-4 font-mono text-[0.6875rem] space-y-1.5 shrink-0 min-w-[280px]">
            <div className="font-bold text-secondary border-b border-structural-border pb-1 uppercase tracking-wider">
              ACTIVE TRANSACTION RECORD
            </div>
            <div className="text-muted-ink truncate pt-1">
              TXID: <span className="font-bold text-secondary">{tx.txid}</span>
            </div>
            <div className="text-muted-ink">
              ACTIVE RUN: <span className="font-bold text-secondary">{runId}</span>
            </div>
          </div>
        </div>

        {/* PRIMARY TRANSACTION HEADER CONTAINER */}
        <section className="w-full border border-structural-border bg-neutral">
          <div className="border-b border-structural-border px-4 py-2 bg-surface-accent flex items-center justify-between">
            <span className="font-mono text-[0.6875rem] font-bold text-secondary uppercase tracking-wider">
              SELECTED TRANSACTION
            </span>
          </div>
          <div className="p-4 bg-neutral border-b border-structural-border">
            <div className="font-mono text-[0.6875rem] text-muted-ink uppercase mb-1">PRIMARY IDENTIFIER</div>
            <div className="font-mono text-[1.125rem] font-bold text-secondary break-all bg-surface-accent p-3 border border-structural-border select-all">
              TXID: {tx.txid}
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 divide-y lg:divide-y-0 lg:divide-x divide-structural-border font-mono text-[0.6875rem]">
            <div className="p-3">
              <div className="text-muted-ink uppercase">FIRST OBSERVED</div>
              <div className="font-bold text-secondary mt-1">{tx.first_observed_network_timestamp || '[DYNAMIC / NOT AVAILABLE]'}</div>
            </div>
            <div className="p-3">
              <div className="text-muted-ink uppercase">LAST OBSERVED</div>
              <div className="font-bold text-secondary mt-1">{tx.last_observed_network_timestamp || '[DYNAMIC / NOT AVAILABLE]'}</div>
            </div>
            <div className="p-3">
              <div className="text-muted-ink uppercase">OBSERVATIONS</div>
              <div className="font-bold text-secondary mt-1">{obsCount}</div>
            </div>
            <div className="p-3">
              <div className="text-muted-ink uppercase">INPUT COUNT</div>
              <div className="font-bold text-secondary mt-1">{inputsCount}</div>
            </div>
            <div className="p-3">
              <div className="text-muted-ink uppercase">OUTPUT COUNT</div>
              <div className="font-bold text-secondary mt-1">{outputsCount}</div>
            </div>
            <div className="p-3">
              <div className="text-muted-ink uppercase">ACTIVE RUN</div>
              <div className="font-bold text-secondary mt-1 truncate max-w-[150px]">{runId}</div>
            </div>
          </div>
        </section>

        {/* ==================== MAIN 8:4 ASYMMETRIC EDITORIAL GRID ==================== */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* ==================== LEFT COLUMN (~8 COLUMNS) ==================== */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            
            {/* 1. TRANSACTION STRUCTURE SUMMARY METRICS */}
            <section className="w-full">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-0 border border-structural-border divide-x divide-y md:divide-y-0 divide-structural-border bg-neutral">
                <div className="p-4 bg-neutral">
                  <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">INPUTS</div>
                  <div className="font-display text-2xl font-bold text-secondary mt-1">{inputsCount}</div>
                  <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">INBOUND VECTOR</div>
                </div>
                <div className="p-4 bg-neutral">
                  <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">OUTPUTS</div>
                  <div className="font-display text-2xl font-bold text-secondary mt-1">{outputsCount}</div>
                  <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">OUTBOUND VECTOR</div>
                </div>
                <div className="p-4 bg-neutral">
                  <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">TOTAL INPUT VALUE</div>
                  <div className="font-display text-xl text-secondary mt-2 font-bold break-all">{totalInputValue.toFixed(8)}</div>
                  <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">BTC OBSERVED</div>
                </div>
                <div className="p-4 bg-neutral">
                  <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">TOTAL OUTPUT VALUE</div>
                  <div className="font-display text-xl text-secondary mt-2 font-bold break-all">{totalOutputValue.toFixed(8)}</div>
                  <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">BTC RECORDED</div>
                </div>
                <div className="p-4 bg-neutral col-span-2 sm:col-span-1">
                  <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">NETWORK FEE</div>
                  <div className="font-display text-xl text-secondary mt-2 font-bold break-all">{tx.fee !== undefined && tx.fee !== null ? tx.fee.toFixed(8) : '[DYNAMIC]'}</div>
                  <div className="font-mono text-[0.6875rem] text-muted-ink mt-1">OR NOT AVAILABLE</div>
                </div>
              </div>
            </section>

            {/* 2. INPUT / OUTPUT STRUCTURE */}
            <section className="w-full border border-structural-border bg-neutral">
              <div className="p-3 bg-surface-accent border-b border-structural-border flex justify-between items-center">
                <span className="font-display text-lg font-bold text-secondary uppercase">INPUT / OUTPUT STRUCTURE</span>
                <span className="font-mono text-[0.6875rem] text-muted-ink">STRUCTURAL BALANCE MAPPING</span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-structural-border">
                {/* Left: Inputs */}
                <div>
                  <div className="p-2.5 bg-surface-accent border-b border-structural-border font-mono text-[0.6875rem] font-bold text-secondary flex justify-between">
                    <span>TRANSACTION INPUTS</span>
                    <span>VECTOR: INBOUND</span>
                  </div>
                  <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                    <table className="w-full text-left border-collapse font-mono text-[0.6875rem]">
                      <thead>
                        <tr className="bg-neutral border-b border-structural-border text-muted-ink">
                          <th className="p-2 border-r border-structural-border">ADDRESS</th>
                          <th className="p-2">AMOUNT</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-structural-border">
                        {tx.inputs?.length ? tx.inputs.map((inp, idx) => (
                          <tr key={idx} className="hover:bg-surface-accent">
                            <td className="p-2 border-r border-structural-border break-all">{inp.address}</td>
                            <td className="p-2 font-bold">{inp.amount.toFixed(8)}</td>
                          </tr>
                        )) : (
                          <tr><td colSpan={2} className="p-2 text-center text-muted-ink">[DYNAMIC / NOT AVAILABLE]</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
                {/* Right: Outputs */}
                <div>
                  <div className="p-2.5 bg-surface-accent border-b border-structural-border font-mono text-[0.6875rem] font-bold text-secondary flex justify-between">
                    <span>TRANSACTION OUTPUTS</span>
                    <span>VECTOR: OUTBOUND</span>
                  </div>
                  <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                    <table className="w-full text-left border-collapse font-mono text-[0.6875rem]">
                      <thead>
                        <tr className="bg-neutral border-b border-structural-border text-muted-ink">
                          <th className="p-2 border-r border-structural-border">ADDRESS</th>
                          <th className="p-2">AMOUNT</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-structural-border">
                        {tx.outputs?.length ? tx.outputs.map((out, idx) => (
                          <tr key={idx} className="hover:bg-surface-accent">
                            <td className="p-2 border-r border-structural-border break-all">{out.address}</td>
                            <td className="p-2 font-bold">{out.amount.toFixed(8)}</td>
                          </tr>
                        )) : (
                          <tr><td colSpan={2} className="p-2 text-center text-muted-ink">[DYNAMIC / NOT AVAILABLE]</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
              <div className="p-2 bg-surface-accent font-mono text-[0.6875rem] text-center border-t border-structural-border text-muted-ink">
                FEE: <span className="font-bold text-secondary">{tx.fee !== undefined && tx.fee !== null ? tx.fee.toFixed(8) : '[DYNAMIC FEE]'}</span> (OR NOT AVAILABLE) | NO INFERRED SPEND-CHAIN LINEAGE FABRICATION
              </div>
            </section>

            {/* 4. NETWORK OBSERVATIONS TABLE */}
            <section className="w-full border border-structural-border bg-neutral">
              <div className="p-4 bg-surface-accent border-b border-structural-border">
                <h2 className="font-display text-lg font-bold text-secondary uppercase">NETWORK OBSERVATIONS</h2>
                <p className="font-body text-[0.8125rem] text-muted-ink mt-0.5">
                  Observed network-layer associations for the selected transaction. Data reflects sensor logging events without ownership assertions.
                </p>
              </div>
              <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
                <table className="w-full text-left border-collapse font-mono text-[0.6875rem]">
                  <thead>
                    <tr className="bg-neutral border-b border-structural-border text-muted-ink">
                      <th className="p-2.5 border-r border-structural-border">OBSERVED AT</th>
                      <th className="p-2.5 border-r border-structural-border">OBSERVED PEER IP</th>
                      <th className="p-2.5 border-r border-structural-border">DESTINATION IP</th>
                      <th className="p-2.5 border-r border-structural-border">SOURCE PORT</th>
                      <th className="p-2.5 border-r border-structural-border">DEST PORT</th>
                      <th className="p-2.5 border-r border-structural-border">GEO COUNTRY</th>
                      <th className="p-2.5">ASN</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-structural-border text-secondary">
                    {tx.observed_peers?.length ? tx.observed_peers.map((peer, idx) => (
                      <tr key={idx} className="hover:bg-surface-accent">
                        <td className="p-2.5 border-r border-structural-border text-muted-ink">[DYNAMIC]</td>
                        <td className="p-2.5 border-r border-structural-border font-mono">{peer.ip_address}</td>
                        <td className="p-2.5 border-r border-structural-border font-mono text-muted-ink">[DYNAMIC]</td>
                        <td className="p-2.5 border-r border-structural-border font-mono">{peer.port}</td>
                        <td className="p-2.5 border-r border-structural-border font-mono text-muted-ink">[DYNAMIC]</td>
                        <td className="p-2.5 border-r border-structural-border">{peer.geo_country || '[DYNAMIC]'}</td>
                        <td className="p-2.5">{peer.asn || '[DYNAMIC]'}</td>
                      </tr>
                    )) : (
                      <tr><td colSpan={7} className="p-2.5 text-center text-muted-ink">[DYNAMIC / NOT AVAILABLE]</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            {/* 5. ADDRESS RELATIONSHIPS */}
            <section className="w-full border border-structural-border bg-neutral">
              <div className="p-4 bg-surface-accent border-b border-structural-border">
                <h2 className="font-display text-lg font-bold text-secondary uppercase">ADDRESS RELATIONSHIPS</h2>
              </div>
              <div className="p-4 space-y-3 font-mono text-[0.6875rem]">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-3 bg-surface-accent border border-structural-border">
                    <span className="text-muted-ink block">INPUT ADDRESS REUSE:</span>
                    <span className="font-bold text-secondary text-sm mt-1 block">[DYNAMIC]</span>
                  </div>
                  <div className="p-3 bg-surface-accent border border-structural-border">
                    <span className="text-muted-ink block">OUTPUT ADDRESS REUSE:</span>
                    <span className="font-bold text-secondary text-sm mt-1 block">[DYNAMIC]</span>
                  </div>
                  <div className="p-3 bg-surface-accent border border-structural-border">
                    <span className="text-muted-ink block">ENTITY CLUSTER:</span>
                    <span className="font-bold text-secondary text-sm mt-1 block">
                      {tx.entity_clusters?.length ? tx.entity_clusters.join(', ') : '[DYNAMIC]'}
                    </span>
                    <span className="text-muted-ink block mt-2">INTERPRETATION:</span>
                    <span className="font-bold text-secondary text-sm mt-1 block">COMMON-CONTROL HYPOTHESIS</span>
                  </div>
                  <div className="p-3 bg-surface-accent border border-structural-border">
                    <span className="text-muted-ink block">CHANGE-ADDRESS INDICATOR:</span>
                    <span className="font-bold text-secondary text-sm mt-1 block">[DYNAMIC]</span>
                  </div>
                </div>
                <div className="p-3 bg-neutral border border-structural-border flex justify-between items-center">
                  <span className="text-muted-ink font-bold uppercase">RELATIONSHIP EVIDENCE:</span>
                  <span className="font-mono bg-surface-accent px-2 py-0.5 border border-structural-border font-bold text-secondary">
                    [DYNAMIC]
                  </span>
                </div>
                <div className="p-3 bg-surface-accent border border-structural-border text-secondary font-body text-[0.8125rem]">
                  <span className="font-bold">CAVEAT NOTE:</span> Address relationships are heuristic indicators and do not establish common ownership or identity. Co-spending heuristics remain subject to CoinJoin, multi-party computation, and custodial aggregation behaviors.
                </div>
              </div>
            </section>

            {/* 6. ALERT CONTEXT */}
            {tx.alerts && tx.alerts.length > 0 && (
              <section className="w-full border border-structural-border bg-neutral">
                <div className="p-4 bg-surface-accent border-b border-structural-border">
                  <h2 className="font-display text-lg font-bold text-secondary uppercase">ASSOCIATED STRUCTURAL ALERTS</h2>
                </div>
                <div className="p-4 space-y-3 font-mono text-[0.6875rem]">
                  {tx.alerts.map((a, idx) => (
                    <div key={idx} className="p-3 border border-structural-border bg-surface-accent flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                      <div>
                        <div className="text-muted-ink font-bold uppercase tracking-wider mb-1">ALERT ID: {a.alert_id}</div>
                        <div className="flex gap-2 items-center">
                          <span className="bg-primary text-secondary px-2 py-0.5 font-bold">STRENGTH: {a.anomaly_strength.toFixed(1)}</span>
                          <span className="bg-neutral border border-structural-border px-2 py-0.5 text-secondary">TIER: {a.evidential_strength_tier}</span>
                        </div>
                      </div>
                      <Link className="px-3 py-1 bg-secondary text-neutral font-bold hover:bg-primary hover:text-secondary border border-structural-border flex items-center gap-1" to={`/runs/${runId}/alerts/${a.alert_id}`}>
                        INSPECT ALERT <span>↗</span>
                      </Link>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 6. GRAPH RELATIONSHIP PREVIEW */}
            <section className="w-full border border-structural-border bg-neutral">
              <div className="p-4 bg-surface-accent border-b border-structural-border flex justify-between items-center">
                <h2 className="font-display text-lg font-bold text-secondary uppercase">GRAPH RELATIONSHIP PREVIEW</h2>
                <Link to={`/runs/${runId}/transactions/${txid}/graph`} className="px-4 py-1.5 bg-secondary text-neutral font-mono text-[0.6875rem] font-bold hover:bg-primary hover:text-secondary transition-none border border-structural-border uppercase flex items-center gap-1">
                  <span>OPEN NETWORK GRAPH</span>
                  <span>↗</span>
                </Link>
              </div>
              <div className="p-6 bg-surface-accent flex flex-col items-center justify-center min-h-[220px]">
                <div className="w-full max-w-lg flex flex-col md:flex-row items-center justify-between gap-6 relative">
                  
                  {/* Left Nodes */}
                  <div className="flex flex-col gap-4 w-full md:w-auto">
                    {tx.inputs && tx.inputs.length > 0 && (
                      <div className="p-2 bg-neutral border border-structural-border font-mono text-[0.6875rem] text-center">
                        <span className="text-muted-ink block font-bold">NODE: INPUT</span>
                        <span className="font-mono text-secondary">{tx.inputs[0].address.substring(0,8)}...</span>
                      </div>
                    )}
                    {tx.observed_peers && tx.observed_peers.length > 0 && (
                      <div className="p-2 bg-neutral border border-structural-border font-mono text-[0.6875rem] text-center">
                        <span className="text-muted-ink block font-bold">NODE: OBSERVED PEER</span>
                        <span className="font-mono text-secondary">{tx.observed_peers[0].ip_address}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Connecting Indicators Left */}
                  <div className="flex flex-col items-center gap-2 font-mono text-[0.6875rem] text-muted-ink">
                    {tx.inputs && tx.inputs.length > 0 && (
                      <>
                        <span className="bg-neutral px-2 py-0.5 border border-structural-border">EDGE: [INPUT]</span>
                        <span>⇄</span>
                      </>
                    )}
                    {tx.observed_peers && tx.observed_peers.length > 0 && (
                      <>
                        <span className="bg-neutral px-2 py-0.5 border border-structural-border">EDGE: [PROPAGATED]</span>
                      </>
                    )}
                  </div>
                  
                  {/* Center TX Node */}
                  <div className="p-4 bg-secondary text-neutral border border-structural-border text-center w-full md:w-auto">
                    <span className="text-primary block font-bold font-mono text-[0.6875rem]">CENTRAL TX NODE</span>
                    <span className="font-mono text-[0.6875rem] font-bold">{tx.txid.substring(0,8)}...</span>
                  </div>
                  
                  {/* Connecting Indicators Right */}
                  <div className="flex flex-col items-center gap-2 font-mono text-[0.6875rem] text-muted-ink">
                    {tx.outputs && tx.outputs.length > 0 && (
                      <>
                        <span className="bg-neutral px-2 py-0.5 border border-structural-border">EDGE: [OUTPUT]</span>
                        <span>⇄</span>
                      </>
                    )}
                  </div>
                  
                  {/* Right Nodes */}
                  <div className="flex flex-col gap-4 w-full md:w-auto">
                    {tx.outputs && tx.outputs.length > 0 && (
                      <div className="p-2 bg-neutral border border-structural-border font-mono text-[0.6875rem] text-center">
                        <span className="text-muted-ink block font-bold">NODE: OUTPUT</span>
                        <span className="font-mono text-secondary">{tx.outputs[0].address.substring(0,8)}...</span>
                      </div>
                    )}
                  </div>

                </div>
                <div className="mt-6 font-mono text-[0.6875rem] text-muted-ink text-center">
                  RELATIONSHIP PREVIEW • AVAILABLE EDGES RENDERED FROM BACKEND DATA
                </div>
              </div>
            </section>
            
            {/* 8. TRANSACTION ANALYTICAL INTERPRETATION */}
            {tx.explanation && (
              <section className="w-full border border-structural-border bg-neutral p-4 space-y-2">
                <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase tracking-wider">
                  ANALYTICAL INTERPRETATION
                </div>
                <div className="font-body text-[0.9375rem] text-secondary bg-surface-accent p-3 border border-structural-border">
                  {tx.explanation.summary}
                </div>
                <div className="font-mono text-[0.6875rem] text-muted-ink pt-1 flex items-center justify-between">
                  <span>INTERPRETATION BASIS:</span>
                  <span className="font-bold text-secondary">[DYNAMIC EVIDENCE BASIS]</span>
                </div>
              </section>
            )}

            {/* 9. INVESTIGATIVE LEAD */}
            {tx.explanation?.human_readable_lead && (
              <section className="w-full border border-structural-border bg-surface-accent p-4 border-l-4 border-l-primary">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-display text-lg font-bold text-secondary uppercase">INVESTIGATIVE LEAD</span>
                  <span className="bg-secondary text-primary font-mono text-[0.6875rem] font-bold px-2 py-0.5">
                    LEAD STATUS: REQUIRES HUMAN REVIEW
                  </span>
                </div>
                <p className="font-body text-[0.9375rem] text-secondary font-medium">
                  {tx.explanation.human_readable_lead}
                </p>
              </section>
            )}

            {/* CAVEATS */}
            <section className="w-full border border-structural-border bg-neutral p-4">
              <p className="font-body text-[0.8125rem] text-muted-ink leading-relaxed">
                <span className="font-bold text-secondary">CONCEPTUAL BOUNDARIES:</span> Bitcoin addresses are pseudonymous identifiers. Address ≠ wallet ≠ entity. IP association ≠ ownership. GeoIP is enrichment, not identity. Network observation time is sensor observation time. Anomaly ≠ crime.
              </p>
            </section>
          </div>

          {/* ==================== RIGHT COLUMN (~4 COLUMNS) ==================== */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            
            {/* 1. TRANSACTION RECORD LEDGER */}
            <section className="w-full border border-structural-border bg-neutral">
              <div className="p-3 bg-secondary text-neutral border-b border-structural-border flex justify-between items-center">
                <span className="font-display text-lg font-bold uppercase">TRANSACTION RECORD LEDGER</span>
                <span className="font-mono text-[0.6875rem] text-primary font-bold">STATE: RECORDED</span>
              </div>
              <div className="divide-y divide-structural-border font-mono text-[0.6875rem]">
                <div className="p-3 bg-neutral hover:bg-surface-accent">
                  <span className="text-muted-ink block">TXID</span>
                  <span className="font-bold text-secondary font-mono break-all">{tx.txid}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent">
                  <span className="text-muted-ink block">ACTIVE RUN</span>
                  <span className="font-bold text-secondary">{runId}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">OBSERVATIONS</span>
                  <span className="font-bold text-secondary">{obsCount}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">ALERT COUNT</span>
                  <span className="font-bold text-secondary">{alertCount}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">INPUTS</span>
                  <span className="font-bold text-secondary">{inputsCount}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">OUTPUTS</span>
                  <span className="font-bold text-secondary">{outputsCount}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">TOTAL INPUT VALUE</span>
                  <span className="font-bold text-secondary">{totalInputValue.toFixed(8)}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">TOTAL OUTPUT VALUE</span>
                  <span className="font-bold text-secondary">{totalOutputValue.toFixed(8)}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">FEE</span>
                  <span className="font-bold text-secondary">{tx.fee !== undefined && tx.fee !== null ? tx.fee.toFixed(8) : '[DYNAMIC]'}</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">MODEL</span>
                  <span className="font-bold text-secondary">[DYNAMIC / NOT AVAILABLE]</span>
                </div>
                <div className="p-3 bg-neutral hover:bg-surface-accent flex justify-between">
                  <span className="text-muted-ink">DATASET</span>
                  <span className="font-bold text-secondary">[DYNAMIC SOURCE]</span>
                </div>
              </div>
            </section>

            {/* 2. AUDIT TRACEABILITY */}
            <section className="w-full border border-structural-border bg-neutral">
              <div className="p-3 bg-surface-accent border-b border-structural-border flex justify-between items-center">
                <span className="font-display text-lg font-bold text-secondary uppercase">AUDIT TRACEABILITY</span>
                <span className="font-mono text-[0.6875rem] text-muted-ink font-bold">DATABASE: DUCKDB</span>
              </div>
              <div className="divide-y divide-structural-border font-mono text-[0.6875rem]">
                <div className="p-3 bg-neutral">
                  <span className="text-muted-ink block">SOURCE RECORDS:</span>
                  <span className="font-bold text-secondary mt-0.5 block">[DYNAMIC]</span>
                </div>
                <div className="p-3 bg-neutral">
                  <span className="text-muted-ink block">SOURCE FILE:</span>
                  <span className="font-mono text-secondary mt-0.5 block break-all">{tx.source_file || '[DYNAMIC]'}</span>
                </div>
                <div className="p-3 bg-neutral">
                  <span className="text-muted-ink block">SOURCE ROW / RECORD:</span>
                  <span className="font-mono text-secondary mt-0.5 block">{tx.source_row !== undefined && tx.source_row !== null ? tx.source_row : '[DYNAMIC]'}</span>
                </div>
                <div className="p-3 bg-neutral">
                  <span className="text-muted-ink block">RUN ID:</span>
                  <span className="font-bold text-secondary mt-0.5 block truncate">{runId}</span>
                </div>
                <div className="p-3 bg-neutral">
                  <span className="text-muted-ink block">EVIDENCE ARTIFACTS:</span>
                  <span className="font-bold text-secondary mt-0.5 block">[DYNAMIC]</span>
                </div>
                <div className="p-3 bg-neutral">
                  <span className="text-muted-ink block">MODEL-DERIVED EVIDENCE:</span>
                  <span className="font-bold text-secondary mt-0.5 block">[DYNAMIC]</span>
                </div>
              </div>
            </section>

            {/* 3. CONTINUE INVESTIGATION */}
            <section className="w-full border border-structural-border bg-neutral p-4 space-y-4">
              <div>
                <h3 className="font-display text-lg font-bold text-secondary uppercase">CONTINUE INVESTIGATION</h3>
                <p className="font-body text-[0.8125rem] text-muted-ink mt-1">
                  Advance inquiry into network relationships, evidence provenance, and related transaction structure.
                </p>
              </div>
              <div className="space-y-2 font-mono text-[0.6875rem] font-bold">
                <Link to={`/runs/${runId}/transactions/${txid}/graph`} className="w-full p-3 bg-secondary text-neutral hover:bg-primary hover:text-secondary border border-structural-border flex justify-between items-center transition-none uppercase">
                  <span>NETWORK GRAPH</span>
                  <span>↗</span>
                </Link>
                <button className="w-full p-3 bg-neutral text-secondary hover:bg-surface-accent border border-structural-border flex justify-between items-center transition-none uppercase cursor-not-allowed opacity-50">
                  <span>EVIDENCE & PROVENANCE</span>
                  <span>↗</span>
                </button>
                {firstAlertId && (
                  <Link className="w-full p-3 bg-neutral text-muted-ink hover:text-secondary hover:bg-surface-accent border border-structural-border flex justify-between items-center transition-none uppercase" to={`/runs/${runId}/alerts/${firstAlertId}`}>
                    <span>BACK TO ALERT</span>
                    <span>←</span>
                  </Link>
                )}
              </div>
            </section>
          </div>
        </div>

        {/* ==================== WORKFLOW PROGRESSION STRIP ==================== */}
        <section className="w-full border border-structural-border bg-neutral mt-4">
          <div className="p-2.5 bg-surface-accent border-b border-structural-border font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">
            SYSTEM WORKFLOW PROGRESSION
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 divide-y md:divide-y-0 md:divide-x divide-structural-border font-mono text-[0.6875rem] font-bold text-center">
            <Link className="p-3 bg-neutral hover:bg-surface-accent text-muted-ink flex items-center justify-center gap-1" to={`/runs/${runId}/alerts`}>
              <span className="bg-structural-border px-1">1</span>
              <span>ALERT QUEUE</span>
            </Link>
            {firstAlertId ? (
              <Link className="p-3 bg-neutral hover:bg-surface-accent text-muted-ink flex items-center justify-center gap-1" to={`/runs/${runId}/alerts/${firstAlertId}`}>
                <span className="bg-structural-border px-1">2</span>
                <span>ALERT INVESTIGATION</span>
              </Link>
            ) : (
              <div className="p-3 bg-neutral text-muted-ink flex items-center justify-center gap-1 opacity-50">
                <span className="bg-structural-border px-1">2</span>
                <span>ALERT INVESTIGATION</span>
              </div>
            )}
            <div className="p-3 bg-primary text-secondary font-bold flex items-center justify-center gap-1">
              <span className="bg-secondary text-neutral px-1">3</span>
              <span>TX INVESTIGATION</span>
              <span>✓</span>
            </div>
            <div className="p-3 bg-neutral text-muted-ink flex items-center justify-center gap-1 opacity-50 cursor-not-allowed">
              <span className="bg-structural-border px-1">4</span>
              <span>NETWORK GRAPH</span>
              <span>→</span>
            </div>
            <div className="p-3 bg-neutral text-muted-ink flex items-center justify-center gap-1 col-span-2 md:col-span-1 opacity-50 cursor-not-allowed">
              <span className="bg-structural-border px-1">5</span>
              <span>PROVENANCE</span>
            </div>
          </div>
        </section>

        <EpistemicBoundary />

      </main>
    </PageFrame>
  );
}
