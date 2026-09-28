import { useEffect, useState } from 'react';

import { apiClient, RunResponse } from '../lib/api';
import { useRunContext } from '../contexts/RunContext';
import { RunManager } from '../components/ui/RunManager';

export function Landing() {
  const { setRun } = useRunContext();
  const [activeRunId, setActiveRunId] = useState<string | undefined>(undefined);
  const [activeRunData, setActiveRunData] = useState<any | undefined>(undefined);
  const [allRuns, setAllRuns] = useState<RunResponse[]>([]);

  useEffect(() => {
    async function fetchRun() {
      try {
        const res = await apiClient.getRuns(100, 0);
        if (res.data) {
          setAllRuns(res.data);
        }
        if (res.data && res.data.length > 0) {
          // Explicitly prioritize the canonical DEMO_V1 case regardless of insertion order
          const targetRun = res.data.find((r: any) => r.is_demo || r.case_id === 'DEMO_V1') || res.data[0];
          setActiveRunId(targetRun.run_id);
          setActiveRunData(targetRun);
          setRun({ id: targetRun.run_id, status: targetRun.status });
        }
      } catch (err) {
        console.error('Failed to fetch active run', err);
      }
    }
    fetchRun();
  }, [setRun]);


  return (
    <div className="w-full">
      {/* 2. MONUMENTAL ASYMMETRIC HERO SECTION (60/40 Split) */}
      <section className="border-b border-structural-border grid grid-cols-1 lg:grid-cols-12 bg-neutral">
        {/* Left Column */}
        <div className="lg:col-span-7 p-6 sm:p-10 lg:p-14 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-structural-border bg-neutral">
          <div>
            <div className="inline-flex items-center border border-structural-border px-2.5 py-1 mb-8 bg-surface-accent">
              <span className="w-1.5 h-1.5 bg-primary mr-2"></span>
              <span className="font-mono text-[0.6875rem] font-bold uppercase text-secondary tracking-widest">BITCOIN TRANSACTION INTELLIGENCE</span>
            </div>
            
            <h1 className="font-display text-5xl md:text-6xl uppercase tracking-tight text-secondary mb-8 leading-none">
              LOCAL TRANSACTION TRAFFIC ANALYSIS FOR STRUCTURAL INVESTIGATION
            </h1>
            
            <p className="font-body text-lg text-muted-ink max-w-2xl mb-10 leading-relaxed">
              Analyze Bitcoin transaction structure, network observations, graph relationships, and structural anomalies locally. Built for analysts who need evidence-traceable investigation workflows with explainable model outputs.
            </p>
            
            <div className="flex flex-wrap items-center gap-4 mb-14"><RunManager demoRunId={activeRunId} /></div>
          </div>
          
          <div className="border-t border-structural-border pt-6 grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-[0.6875rem]">
            {activeRunData?.is_demo ? (
              <div className="sm:col-span-3 pb-6 mb-6 border-b border-structural-border">
                <div className="text-muted-ink font-bold mb-2">ACTIVE DATASET MODE: DEMO CASE</div>
                <div className="text-secondary uppercase font-bold text-xs p-3 bg-surface-accent border border-structural-border">
                  {activeRunData.data_mode || "PUBLIC-DERIVED BLOCKCHAIN + SYNTHETIC NETWORK + LOCAL GEOIP"}
                </div>
              </div>
            ) : null}
            <div>
              <div className="text-muted-ink font-bold">ENGINE ARCHITECTURE</div>
              <div className="text-secondary uppercase font-bold mt-1">DUCKDB + NETWORKX</div>
            </div>
            <div className="sm:border-l sm:border-structural-border sm:pl-4">
              <div className="text-muted-ink font-bold">RUNTIME</div>
              <div className="text-secondary uppercase font-bold mt-1">LOCAL / OFFLINE</div>
            </div>
            <div className="sm:border-l sm:border-structural-border sm:pl-4">
              <div className="text-muted-ink font-bold">ANALYTICAL FEATURES</div>
              <div className="text-secondary uppercase font-bold mt-1">17 CANONICAL FEATURES</div>
            </div>
          </div>
        </div>
        
        {/* Right Column Abstract Editorial Network Diagram */}
        <div className="lg:col-span-5 bg-surface-accent p-6 sm:p-10 flex flex-col justify-between relative overflow-hidden">
          <div className="flex items-center justify-between border-b border-structural-border pb-3 mb-6">
            <span className="font-mono text-[0.6875rem] font-bold text-secondary uppercase tracking-widest">TOPOLOGICAL GRAPH REPRESENTATION</span>
            <span className="font-mono text-[0.6875rem] text-primary uppercase font-bold tracking-widest">ABSTRACT RELATIONSHIP VIEW</span>
          </div>
          
          <div className="my-auto py-8 flex items-center justify-center">
            <svg className="w-full max-w-md h-auto" fill="none" viewBox="0 0 460 420" xmlns="http://www.w3.org/2000/svg">
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="20" x2="440" y1="20" y2="20"></line>
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="20" x2="440" y1="120" y2="120"></line>
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="20" x2="440" y1="220" y2="220"></line>
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="20" x2="440" y1="320" y2="320"></line>
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="20" x2="440" y1="400" y2="400"></line>
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="60" x2="60" y1="10" y2="410"></line>
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="180" x2="180" y1="10" y2="410"></line>
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="300" x2="300" y1="10" y2="410"></line>
              <line stroke="#1b1c19" strokeDasharray="2 4" strokeWidth="0.75" x1="400" x2="400" y1="10" y2="410"></line>
              <circle cx="230" cy="210" r="140" stroke="#1b1c19" strokeWidth="1"></circle>
              <circle cx="230" cy="210" r="85" stroke="#f7931a" strokeDasharray="4 2" strokeWidth="1.5"></circle>
              <path d="M70 120 L230 210 L370 100" stroke="#1b1c19" strokeWidth="1.25"></path>
              <path d="M230 210 L150 330 L290 320 L230 210" stroke="#1b1c19" strokeWidth="1.25"></path>
              <path d="M370 100 L390 260 L290 320" stroke="#1b1c19" strokeWidth="1"></path>
              <path d="M70 120 L150 330" stroke="#1b1c19" strokeWidth="1"></path>
              <line stroke="#f7931a" strokeWidth="2.5" x1="230" x2="320" y1="210" y2="150"></line>
              <rect fill="#1b1c19" height="28" stroke="#f7931a" strokeWidth="2" width="28" x="216" y="196"></rect>
              <text fill="#faf9f4" fontFamily="monospace" fontSize="11" fontWeight="700" textAnchor="middle" x="230" y="214">TX</text>
              <circle cx="70" cy="120" fill="#faf9f4" r="14" stroke="#1b1c19" strokeWidth="2"></circle>
              <text fill="#1b1c19" fontFamily="monospace" fontSize="9" fontWeight="700" textAnchor="middle" x="70" y="124">IN.1</text>
              <rect fill="#f7931a" height="24" stroke="#1b1c19" strokeWidth="1.5" width="24" x="358" y="88"></rect>
              <text fill="#1b1c19" fontFamily="monospace" fontSize="9" fontWeight="700" textAnchor="middle" x="370" y="104">OUT.8</text>
              <circle cx="150" cy="330" fill="#1b1c19" r="16" stroke="#1b1c19"></circle>
              <text fill="#faf9f4" fontFamily="monospace" fontSize="9" fontWeight="700" textAnchor="middle" x="150" y="334">PEER</text>
              <circle cx="290" cy="320" fill="#faf9f4" r="12" stroke="#1b1c19" strokeWidth="1.5"></circle>
              <text fill="#1b1c19" fontFamily="monospace" fontSize="8" textAnchor="middle" x="290" y="323">IN.2</text>
              <circle cx="390" cy="260" fill="#faf9f4" r="10" stroke="#1b1c19" strokeWidth="1.5"></circle>
            </svg>
          </div>
          
          <div className="border-t border-structural-border pt-4 flex items-center justify-between font-mono text-[0.6875rem]">
            <div className="flex items-center space-x-3">
              <span className="inline-block w-3 h-3 bg-secondary"></span>
              <span className="text-secondary tracking-widest">OBSERVED PEERS</span>
            </div>
            <div className="flex items-center space-x-3">
              <span className="inline-block w-3 h-3 bg-primary"></span>
              <span className="text-secondary tracking-widest">ANALYTICAL RELATIONSHIPS</span>
            </div>
            <div className="flex items-center space-x-3">
              <span className="inline-block w-3 h-3 border border-structural-border bg-neutral"></span>
              <span className="text-secondary tracking-widest">TX / ADDRESS RELATIONSHIPS</span>
            </div>
          </div>
        </div>
      </section>

      {/* 3. MANDATORY PROMINENT PRODUCT BOUNDARY STATEMENT */}
      <section className="w-full bg-secondary text-neutral border-b border-structural-border px-6 py-10 md:px-12 md:py-14 relative">
        <div className="max-w-6xl mx-auto border-l-4 border-primary pl-6 md:pl-10">
          <div className="font-mono text-[0.6875rem] font-bold text-primary uppercase tracking-widest mb-3">
            ANALYTICAL BOUNDARY
          </div>
          <blockquote className="font-display text-2xl md:text-3xl uppercase text-neutral leading-snug tracking-tight">
            “Structural anomaly does not mean criminal activity. CryptoNexus surfaces patterns for human investigation. It does not determine identity, ownership or criminal intent.”
          </blockquote>
        </div>
      </section>

      {/* 4. DEMONSTRATION DATA LEDGER */}
      <section className="w-full border-b border-structural-border bg-neutral" id="overview">
        <div className="border-b border-structural-border px-6 py-3 bg-surface-accent flex items-center justify-between">
          <span className="font-display text-sm uppercase text-secondary font-semibold tracking-widest">DEMO DATASET // DEMO_V1</span>
          <span className="font-mono text-[0.6875rem] font-bold uppercase text-muted-ink">SOURCE BLOCKS: 700000 → 700022</span>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 divide-y sm:divide-y-0 sm:divide-x divide-structural-border">
          <div className="p-6 md:p-8 bg-neutral flex flex-col justify-between transition-none">
            <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase tracking-wider mb-4">TRANSACTIONS</div>
            <div className="font-display text-4xl text-secondary tracking-tight leading-none mb-2">25,649</div>
          </div>
          <div className="p-6 md:p-8 bg-surface-accent flex flex-col justify-between transition-none">
            <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase tracking-wider mb-4">NETWORK OBSERVATIONS</div>
            <div className="font-display text-4xl text-secondary tracking-tight leading-none mb-2">60,355</div>
          </div>
          <div className="p-6 md:p-8 bg-primary text-secondary flex flex-col justify-between">
            <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase tracking-wider mb-4 flex items-center justify-between">
              <span>STRUCTURAL ANOMALIES</span>
              <span className="w-2.5 h-2.5 bg-secondary"></span>
            </div>
            <div>
              <div className="font-display text-4xl text-secondary tracking-tight leading-none mb-2">1,283</div>
              <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase">[ STRUCTURAL ANOMALY ALERTS ]</div>
            </div>
          </div>
          <div className="p-6 md:p-8 bg-neutral flex flex-col justify-between transition-none">
            <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase tracking-wider mb-4">OBSERVED PEERS</div>
            <div className="font-display text-4xl text-secondary tracking-tight leading-none mb-2">7,468</div>
          </div>
          <div className="p-6 md:p-8 bg-surface-accent flex flex-col justify-between transition-none">
            <div className="font-mono text-[0.6875rem] font-bold text-muted-ink uppercase tracking-wider mb-4">CONNECTED COMPONENTS</div>
            <div className="font-display text-4xl text-secondary tracking-tight leading-none mb-2">3</div>
          </div>
        </div>
      </section>

      {/* 5. WORKFLOW & METHODOLOGY LEDGER */}
      <section className="w-full border-b border-structural-border bg-neutral">
        <div className="p-6 bg-surface-accent flex flex-col sm:flex-row justify-between gap-4 border-b border-structural-border">
          <div>
            <div className="font-mono text-[0.6875rem] font-bold text-primary uppercase mb-1">// METHODOLOGICAL PIPELINE</div>
            <h2 className="font-display text-2xl uppercase text-secondary tracking-tight leading-none">ANALYTICAL WORKFLOW</h2>
          </div>
          <div className="font-mono text-[0.6875rem] text-muted-ink">
            EXECUTION STACK: DUCKDB • NETWORKX • SCIKIT-LEARN • HDBSCAN • SHAP
          </div>
        </div>
        
        {/* Horizontal Architectural Timeline: 9 stages */}
        <div className="overflow-x-auto">
          <div className="min-w-[1080px] grid grid-cols-9 divide-x divide-structural-border border-b border-structural-border bg-neutral text-center">
            {[
              { num: '01', title: 'INGEST', desc: 'Transaction and network-observation records' },
              { num: '02', title: 'CORRELATE', desc: 'Peer timing and transaction relationships' },
              { num: '03', title: 'CIH', desc: 'Common-input-hypothesis clustering' },
              { num: '04', title: 'GRAPH', desc: 'Transaction, address, and peer relationships' },
              { num: '05', title: 'GRAPH ANALYSIS', desc: 'Topology and connected components' },
              { num: '06', title: 'FEATURES', desc: '17 canonical analytical features' },
              { num: '07', title: 'ML SCORING', desc: 'Isolation Forest and HDBSCAN' },
              { num: '08', title: 'ALERTS', desc: 'Structural anomaly signals' }
            ].map(stage => (
              <div key={stage.num} className="p-4 flex flex-col justify-between hover:bg-surface-accent transition-none">
                <span className="font-mono text-[0.6875rem] text-muted-ink mb-2">{stage.num}</span>
                <span className="font-display text-sm uppercase text-secondary font-bold">{stage.title}</span>
                <span className="font-mono text-[0.6875rem] text-muted-ink mt-2">{stage.desc}</span>
              </div>
            ))}
            <div className="p-4 flex flex-col justify-between bg-secondary text-neutral">
              <span className="font-mono text-[0.6875rem] text-neutral mb-2 font-bold">09</span>
              <span className="font-display text-sm uppercase font-bold text-neutral">FINALIZE</span>
              <span className="font-mono text-[0.6875rem] font-bold text-neutral mt-2">Persist run outputs and evidence</span>
            </div>
          </div>
        </div>

        {/* Validated Analytical Engine Stack Details */}
        <div className="grid grid-cols-1 md:grid-cols-5 divide-y md:divide-y-0 md:divide-x divide-structural-border p-0 bg-neutral">
          <div className="p-6">
            <div className="font-mono text-[0.6875rem] font-bold uppercase text-primary mb-1">DUCKDB</div>
            <div className="font-mono text-[0.6875rem] text-muted-ink">High-performance in-process SQL OLAP engine executing queries locally over dataset records.</div>
          </div>
          <div className="p-6">
            <div className="font-mono text-[0.6875rem] font-bold uppercase text-primary mb-1">NETWORKX</div>
            <div className="font-mono text-[0.6875rem] text-muted-ink">Graph modeling and analysis across transaction, address, and observed-peer relationships.</div>
          </div>
          <div className="p-6">
            <div className="font-mono text-[0.6875rem] font-bold uppercase text-primary mb-1">ISOLATION FOREST</div>
            <div className="font-mono text-[0.6875rem] text-muted-ink">Unsupervised ensemble anomaly detection isolating rare multi-feature transaction outliers.</div>
          </div>
          <div className="p-6">
            <div className="font-mono text-[0.6875rem] font-bold uppercase text-primary mb-1">HDBSCAN</div>
            <div className="font-mono text-[0.6875rem] text-muted-ink">Density-based spatial clustering identifying structural clusters and noise candidates.</div>
          </div>
          <div className="p-6">
            <div className="font-mono text-[0.6875rem] font-bold uppercase text-primary mb-1">SHAP ATTRIBUTION</div>
            <div className="font-mono text-[0.6875rem] text-muted-ink">SHAP explanations expose feature contributions associated with model-derived anomaly signals.</div>
          </div>
        </div>
      </section>

      
      {/* 6. RUN HISTORY (NEW) */}
      <section className="bg-surface-accent p-8 sm:p-14 border-t border-structural-border">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-display text-2xl uppercase text-secondary tracking-tight leading-none mb-6">
            RECENT INVESTIGATIONS
          </h2>
          <div className="flex flex-col gap-2">
            {allRuns.length === 0 && <div className="font-mono text-xs text-muted-ink">No runs found.</div>}
            {allRuns.map(run => (
              <a key={run.run_id} href={`/runs/${run.run_id}`} className="block border border-structural-border bg-neutral p-4 hover:bg-surface-accent transition-none">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-mono text-xs font-bold text-primary mb-1">{run.run_id === 'DEMO_V1' ? '[ DEMO DATASET ]' : '[ NEW RUN ]'}</div>
                    <div className="font-display text-lg text-secondary truncate">{run.run_id}</div>
                  </div>
                  <div className={`px-2 py-1 font-mono text-[0.6875rem] font-bold uppercase border border-structural-border ${
                    run.status === 'FAILED' ? 'bg-red-950/50 text-red-500 border-red-900' : 
                    run.status === 'COMPLETED' ? 'bg-primary text-secondary' : 
                    'bg-secondary text-neutral'
                  }`}>
                    {run.status}
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION: CALL TO VERIFICATION / DOWNLOAD LOCAL RUNTIME */}
      <section className="bg-neutral p-8 sm:p-14 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="inline-block border border-structural-border px-3 py-1 font-mono text-[0.6875rem] font-bold uppercase mb-6 bg-surface-accent text-secondary">LOCAL INVESTIGATION WORKSPACE</div>
          <h2 className="font-display text-4xl uppercase text-secondary tracking-tight leading-none mb-6">
            START AN INVESTIGATION
          </h2>
          <p className="font-body text-lg text-muted-ink mb-8">
            Load a local dataset and begin an evidence-traceable structural analysis.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4"><RunManager demoRunId={activeRunId} /></div>
        </div>
      </section>

    </div>
  );
}
