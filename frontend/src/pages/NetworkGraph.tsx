import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient, ApiError, GraphResponse } from '../lib/api';
import { PageFrame } from '../layouts/PageFrame';
import { SystemState } from '../components/ui/SystemState';
import { EpistemicBoundary } from '../components/ui/EpistemicBoundary';
import { useRunContext } from '../contexts/RunContext';
import { GraphCanvas } from '../components/ui/GraphCanvas';

export function NetworkGraph() {
  const { runId, txid } = useParams<{ runId: string; txid: string }>();
  
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState<'NONE' | 'RUN_UNAVAILABLE' | 'TRANSACTION_UNAVAILABLE' | 'ERROR'>('NONE');
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(txid || null);
  const [graphDepth, setGraphDepth] = useState<number>(1);

  // Filters
  const [filterNodes, setFilterNodes] = useState({ peer: true, tx: true, address: true });
  const [filterEdges, setFilterEdges] = useState({ input: true, output: true, propagated: true });

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
        const gData = await apiClient.getGraphNeighbors(runId, txid, graphDepth);
        setGraphData(gData);
        // Only set selected node if it's the initial load or node is available
        const hasTxNode = gData.nodes.some(n => n.id === txid);
        if (hasTxNode) {
          setSelectedNodeId(prev => prev ? prev : txid);
        }
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
  }, [runId, txid, setRun, graphDepth]);

  const filteredNodes = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes.filter(n => {
      if (n.node_type === 'Transaction') return filterNodes.tx;
      if (n.node_type === 'Address') return filterNodes.address;
      if (n.node_type === 'IP') return filterNodes.peer;
      return true;
    });
  }, [graphData, filterNodes]);

  const filteredEdges = useMemo(() => {
    if (!graphData) return [];
    return graphData.edges.filter(e => {
      // Must connect two visible nodes
      const sourceVisible = filteredNodes.some(n => n.id === e.source);
      const targetVisible = filteredNodes.some(n => n.id === e.target);
      if (!sourceVisible || !targetVisible) return false;

      if (e.edge_type === 'INPUT') return filterEdges.input;
      if (e.edge_type === 'OUTPUT') return filterEdges.output;
      if (e.edge_type === 'PROPAGATED') return filterEdges.propagated;
      return true;
    });
  }, [graphData, filterEdges, filteredNodes]);

  const selectedNode = useMemo(() => {
    if (!graphData || !selectedNodeId) return null;
    return graphData.nodes.find(n => n.id === selectedNodeId) || null;
  }, [graphData, selectedNodeId]);

  if (loading) return <PageFrame><SystemState type="LOADING" /></PageFrame>;
  
  if (errorState !== 'NONE') {
    return <PageFrame><SystemState type={errorState} /></PageFrame>;
  }

  if (!graphData || graphData.nodes.length === 0) {
    return <PageFrame><SystemState type="EMPTY" /></PageFrame>;
  }

  if (filteredNodes.length === 0) {
    return (
      <PageFrame>
        {/* We still render the shell but with NO_RESULTS state */}
        <SystemState type="NO_RESULTS" />
      </PageFrame>
    );
  }

  return (
    <PageFrame>
      {/* 3. WORKFLOW STEPPER */}
      <section className="w-full bg-neutral border-b border-structural-border px-6 py-2 flex flex-wrap items-center justify-between font-mono font-bold text-[0.6875rem]">
        <div className="flex items-center flex-wrap gap-2 uppercase tracking-wide text-muted-ink">
          <Link to={`/runs/${runId}/alerts`} className="hover:text-secondary cursor-pointer">1 ALERT QUEUE</Link>
          <span>→</span>
          {/* We don't have the specific alert ID here, so we skip exact active linking or just use plain text */}
          <span className="hover:text-secondary cursor-pointer">2 ALERT INVESTIGATION</span>
          <span>→</span>
          <Link to={`/runs/${runId}/transactions/${txid}`} className="hover:text-secondary cursor-pointer">3 TX INVESTIGATION</Link>
          <span>→</span>
          <span className="bg-secondary text-neutral px-2 py-0.5 border border-structural-border">4 NETWORK GRAPH (ACTIVE)</span>
          <span>→</span>
          <span className="hover:text-secondary cursor-pointer opacity-50 cursor-not-allowed">5 PROVENANCE</span>
        </div>
        <div className="hidden md:flex items-center text-muted-ink">
          ACTIVE RUN: <span className="text-secondary font-bold ml-1.5">{runId}</span>
        </div>
      </section>

      {/* 4. PAGE HEADLINE & METADATA SECTION */}
      <section className="w-full bg-surface-accent border-b border-structural-border px-6 py-4 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div>
          <div className="font-mono text-[0.6875rem] font-bold text-primary uppercase tracking-widest mb-0.5">
            NETWORK RELATIONSHIP ANALYSIS
          </div>
          <h1 className="font-display text-4xl font-bold text-secondary uppercase tracking-tight">
            NETWORK / TRANSACTION GRAPH
          </h1>
          <p className="font-body text-[0.9375rem] text-muted-ink mt-1 max-w-3xl">
            Explore structural relationships across observed peers, Bitcoin transactions, and Bitcoin addresses within the active analytical run.
          </p>
        </div>
        <div className="border border-structural-border bg-neutral p-3 min-w-[340px] flex flex-col gap-1 font-mono font-bold text-[0.6875rem]">
          <div className="flex justify-between border-b border-structural-border pb-1 text-muted-ink uppercase">
            <span>WORKBENCH STATE</span>
            <span className="text-primary bg-secondary px-1 text-[0.625rem]">ACTIVE GRAPH</span>
          </div>
          <div className="flex justify-between pt-1">
            <span className="text-muted-ink">RUN:</span>
            <span className="text-secondary">{runId}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-ink">SELECTED TX:</span>
            <span className="text-secondary font-bold">{txid}</span>
          </div>
        </div>
      </section>

      {/* 5. DOMINANT GRAPH WORKSPACE (ASYMMETRIC 8:4 EDITORIAL MATRIX) */}
      <main className="w-full grid grid-cols-1 lg:grid-cols-12 border-b border-structural-border bg-secondary">
        
        {/* 8-COLUMN GRAPH CANVAS */}
        <div className="lg:col-span-8 bg-surface-accent flex flex-col relative border-b lg:border-b-0 lg:border-r border-structural-border">
          
          {/* Graph Canvas Controls Header */}
          <div className="w-full border-b border-structural-border bg-neutral px-4 py-2 flex flex-wrap items-center justify-between gap-2 z-10">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-[0.6875rem] uppercase text-secondary flex items-center gap-1">
                TOPOLOGICAL CANVAS
              </span>
              <span className="text-muted-ink font-mono text-[0.6875rem]">| LAYOUT: D3 FORCE-DIRECTED</span>
            </div>
            {/* The canvas component brings its own zoom controls */}
          </div>

          {/* Graph Filters Bar */}
          <div className="w-full border-b border-structural-border bg-neutral px-4 py-1.5 flex flex-wrap items-center justify-between gap-3 font-mono font-bold text-[0.6875rem]">
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-muted-ink uppercase">FILTER NODES:</span>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={filterNodes.peer} onChange={e => setFilterNodes({...filterNodes, peer: e.target.checked})} className="w-3.5 h-3.5 rounded-none border border-structural-border bg-neutral accent-secondary text-secondary" />
                <span className="text-secondary">OBSERVED PEER</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={filterNodes.tx} onChange={e => setFilterNodes({...filterNodes, tx: e.target.checked})} className="w-3.5 h-3.5 rounded-none border border-structural-border bg-neutral accent-secondary text-secondary" />
                <span className="text-secondary">TRANSACTION</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={filterNodes.address} onChange={e => setFilterNodes({...filterNodes, address: e.target.checked})} className="w-3.5 h-3.5 rounded-none border border-structural-border bg-neutral accent-secondary text-secondary" />
                <span className="text-secondary">ADDRESS</span>
              </label>
            </div>
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-muted-ink uppercase">FILTER EDGES:</span>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={filterEdges.input} onChange={e => setFilterEdges({...filterEdges, input: e.target.checked})} className="w-3.5 h-3.5 rounded-none border border-structural-border bg-neutral accent-secondary text-secondary" />
                <span className="text-secondary">INPUT</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={filterEdges.output} onChange={e => setFilterEdges({...filterEdges, output: e.target.checked})} className="w-3.5 h-3.5 rounded-none border border-structural-border bg-neutral accent-secondary text-secondary" />
                <span className="text-secondary">OUTPUT</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={filterEdges.propagated} onChange={e => setFilterEdges({...filterEdges, propagated: e.target.checked})} className="w-3.5 h-3.5 rounded-none border border-structural-border bg-neutral accent-secondary text-secondary" />
                <span className="text-secondary">PROPAGATED</span>
              </label>
            </div>
          </div>

          {/* Graph Canvas Interior */}
          <div className="w-full h-[580px] relative overflow-hidden flex items-center justify-center bg-neutral">
            <GraphCanvas 
              nodes={filteredNodes} 
              edges={filteredEdges} 
              selectedNodeId={selectedNodeId}
              onNodeSelect={(id) => setSelectedNodeId(id)}
            />
            
            <div className="absolute top-3 left-4 font-mono text-[0.6875rem] text-muted-ink pointer-events-none select-none">
              CANVAS_ORIGIN (0, 0) // GRAPH VIEWPORT // INTERACTIVE
            </div>
            <div className="absolute bottom-3 right-4 font-mono text-[0.6875rem] text-muted-ink pointer-events-none select-none">
              SUB-COMPONENT ID: {runId.substring(0,8)} // DIRECTED GRAPH VIEW
            </div>
          </div>
        </div>

        {/* 4-COLUMN ANALYST / INSPECTOR RAIL */}
        <div className="lg:col-span-4 bg-neutral flex flex-col h-[580px] lg:h-auto overflow-y-auto">
          
          <div className="w-full border-b border-structural-border bg-secondary px-4 py-2 flex items-center justify-between z-10 sticky top-0">
            <span className="font-mono font-bold text-[0.6875rem] text-neutral uppercase tracking-wider">
              INSPECTOR RAIL
            </span>
            <span className="text-primary font-mono font-bold text-[0.6875rem]">STATE: ACTIVE</span>
          </div>

          {selectedNode ? (
            <div className="p-4 flex flex-col gap-6">
              
              {/* NODE IDENTITY CARD */}
              <div className="border border-structural-border bg-surface-accent p-3">
                <div className="font-mono text-[0.6875rem] text-muted-ink uppercase mb-1">SELECTED NODE IDENTIFIER</div>
                <div className="font-mono text-[1.125rem] font-bold text-secondary break-all bg-neutral p-3 border border-structural-border select-all">
                  {selectedNode.id}
                </div>
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-structural-border font-mono text-[0.6875rem]">
                  <span className="text-muted-ink uppercase">NODE TYPE:</span>
                  <span className="bg-secondary text-neutral px-2 py-0.5 font-bold uppercase">{selectedNode.node_type}</span>
                </div>
              </div>

              {/* NODE METADATA */}
              <div className="border border-structural-border bg-neutral">
                <div className="p-2.5 bg-surface-accent border-b border-structural-border font-mono text-[0.6875rem] font-bold text-secondary uppercase">
                  NODE METADATA
                </div>
                <div className="divide-y divide-structural-border font-mono text-[0.6875rem]">
                  {Object.entries(selectedNode.metadata || {}).map(([k, v]) => (
                    <div key={k} className="p-3 hover:bg-surface-accent flex justify-between gap-4">
                      <span className="text-muted-ink uppercase">{k.replace(/_/g, ' ')}</span>
                      <span className="font-bold text-secondary break-all text-right">{String(v)}</span>
                    </div>
                  ))}
                  {(!selectedNode.metadata || Object.keys(selectedNode.metadata).length === 0) && (
                    <div className="p-3 hover:bg-surface-accent flex justify-between gap-4">
                      <span className="text-muted-ink uppercase">ADDITIONAL METADATA</span>
                      <span className="font-bold text-secondary">[DYNAMIC / NOT AVAILABLE]</span>
                    </div>
                  )}
                </div>
              </div>

              {/* RELATIONSHIP CONTEXT */}
              <div className="border border-structural-border bg-neutral">
                <div className="p-2.5 bg-surface-accent border-b border-structural-border font-mono text-[0.6875rem] font-bold text-secondary uppercase">
                  RELATIONSHIP CONTEXT
                </div>
                <div className="divide-y divide-structural-border font-mono text-[0.6875rem]">
                  <div className="p-3 hover:bg-surface-accent flex justify-between">
                    <span className="text-muted-ink uppercase">CONNECTED EDGES:</span>
                    <span className="font-bold text-secondary">
                      {graphData.edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id).length}
                    </span>
                  </div>
                  <div className="p-3 hover:bg-surface-accent">
                    <span className="text-muted-ink block uppercase">ENTITY CLUSTER:</span>
                    <span className="font-bold text-secondary mt-1 block">
                      {selectedNode.metadata?.entity_cluster ? String(selectedNode.metadata.entity_cluster) : '[DYNAMIC / NOT AVAILABLE]'}
                    </span>
                    <span className="text-muted-ink block mt-2 uppercase">INTERPRETATION:</span>
                    <span className="font-bold text-secondary mt-1 block">COMMON-CONTROL HYPOTHESIS</span>
                  </div>
                </div>
              </div>

              {/* GRAPH STATISTICS SUMMARY */}
              <div className="border border-structural-border bg-neutral">
                <div className="p-2.5 bg-surface-accent border-b border-structural-border font-mono text-[0.6875rem] font-bold text-secondary uppercase">
                  ACTIVE GRAPH STATISTICS
                </div>
                <div className="divide-y divide-structural-border font-mono text-[0.6875rem]">
                  <div className="p-3 flex justify-between">
                    <span className="text-muted-ink uppercase">TOTAL NODES:</span>
                    <span className="font-bold text-secondary">{graphData.nodes.length}</span>
                  </div>
                  <div className="p-3 flex justify-between">
                    <span className="text-muted-ink uppercase">TOTAL EDGES:</span>
                    <span className="font-bold text-secondary">{graphData.edges.length}</span>
                  </div>
                  <div className="p-3 flex justify-between">
                    <span className="text-muted-ink uppercase">TRAVERSAL DEPTH:</span>
                    <span className="font-bold text-secondary">{graphData.depth}</span>
                  </div>
                </div>
              </div>

              {/* GRAPH DEPTH TRAVERSAL CONTROL */}
              <div className="border border-structural-border bg-neutral p-4 space-y-2">
                <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase tracking-wider">
                  GRAPH DEPTH: {graphDepth}
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => setGraphDepth(1)}
                    className={`flex-1 p-2 border border-structural-border font-mono text-[0.6875rem] font-bold uppercase transition-none ${graphDepth === 1 ? 'bg-secondary text-neutral' : 'bg-surface-accent text-secondary hover:bg-neutral'}`}
                  >
                    DEPTH 1
                  </button>
                  <button 
                    onClick={() => setGraphDepth(2)}
                    className={`flex-1 p-2 border border-structural-border font-mono text-[0.6875rem] font-bold uppercase transition-none ${graphDepth === 2 ? 'bg-secondary text-neutral' : 'bg-surface-accent text-secondary hover:bg-neutral'}`}
                  >
                    DEPTH 2
                  </button>
                </div>
              </div>

            </div>
          ) : (
            <div className="p-6 flex flex-col items-center justify-center h-full text-center space-y-2">
              <span className="material-symbols-outlined text-4xl text-muted-ink">touch_app</span>
              <div className="font-mono text-[0.6875rem] font-bold text-secondary uppercase tracking-widest">
                NO NODE SELECTED
              </div>
              <div className="font-body text-[0.8125rem] text-muted-ink max-w-[200px]">
                Select a node on the canvas to inspect its metadata and relationships.
              </div>
            </div>
          )}
        </div>
      </main>

      <div className="mt-4">
        <EpistemicBoundary />
      </div>

    </PageFrame>
  );
}
