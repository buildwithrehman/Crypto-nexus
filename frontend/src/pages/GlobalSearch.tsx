import { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient, SearchResult as ApiSearchResult } from '../lib/api';
import { PageFrame } from '../layouts/PageFrame';
import { SystemState } from '../components/ui/SystemState';
import { useRunContext } from '../contexts/RunContext';

type SearchFilter = 'ALL' | 'TRANSACTION' | 'ADDRESS' | 'NETWORK OBSERVATION' | 'ALERT' | 'RUN' | 'EVIDENCE' | 'SOURCE RECORD';

export function GlobalSearch() {
  const { currentRun } = useRunContext();
  
  const [query, setQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<SearchFilter>('ALL');
  const [searchStatus, setSearchStatus] = useState<'READY' | 'SEARCHING' | 'NO_RESULTS' | 'ERROR' | 'INVALID_QUERY'>('READY');
  
  const [results, setResults] = useState<ApiSearchResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<ApiSearchResult | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setSearchStatus('INVALID_QUERY');
      setResults([]);
      setSelectedResult(null);
      return;
    }

    setSearchStatus('SEARCHING');
    setSelectedResult(null);
    setResults([]);

    try {
      const activeRunScope = currentRun?.run_id;
      const apiCategory = activeFilter === 'ALL' ? 'ALL' : activeFilter;

      if (['ADDRESS', 'NETWORK OBSERVATION', 'EVIDENCE', 'SOURCE RECORD'].includes(apiCategory)) {
        // Explicitly disabled/unsupported natively
        setResults([]);
        setSearchStatus('NO_RESULTS');
        return;
      }

      const res = await apiClient.search(query.trim(), apiCategory, 100, activeRunScope);
      if (res.results.length === 0) {
        setSearchStatus('NO_RESULTS');
      } else {
        setResults(res.results);
        setSearchStatus('READY');
      }
    } catch (err) {
      console.error(err);
      setSearchStatus('ERROR');
    }
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setSelectedResult(null);
    setSearchStatus('READY');
  };

  const getNavigationPath = (res: ApiSearchResult) => {
    if (res.record_type === 'ALERT') return `/runs/${res.run_id}/alerts/${res.alert_id || res.primary_identifier}`;
    if (res.record_type === 'TRANSACTION') return `/runs/${res.run_id}/transactions/${res.txid || res.primary_identifier}`;
    if (res.record_type === 'RUN') return `/runs/${res.run_id}`;
    return null;
  };

  return (
    <PageFrame>
      <div className="border-b border-structural-border bg-surface-accent p-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="font-mono text-xs font-bold text-muted-ink tracking-wider uppercase mb-1">
            ANALYTICAL WORKSPACE
          </div>
          <h1 className="font-display text-4xl uppercase text-secondary m-0">GLOBAL SEARCH</h1>
          <div className="font-mono text-[0.6875rem] text-primary uppercase mt-2 tracking-wide font-bold">
            CROSS-WORKSPACE QUERY ENGINE
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="font-mono text-[0.6875rem] font-bold px-2 py-1 bg-neutral border border-structural-border text-secondary uppercase">
            SEARCH WORKSPACE: {searchStatus}
          </div>
        </div>
      </div>

      <section className="p-6 border-b border-structural-border bg-neutral">
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <div className="flex-1 relative">
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="ENTER TXID, ALERT_ID, OR RUN IDENTIFIER..."
              aria-label="Search Query"
              className="w-full bg-surface-accent border border-structural-border p-4 pr-12 font-mono text-sm text-secondary placeholder:text-muted-ink focus:outline-none focus:border-primary transition-none"
            />
            {query && (
              <button 
                onClick={clearSearch}
                className="absolute right-4 top-1/2 -translate-y-1/2 font-mono text-xs font-bold text-muted-ink hover:text-primary transition-none uppercase"
              >
                CLEAR
              </button>
            )}
          </div>
          <button 
            onClick={handleSearch}
            className="bg-secondary text-neutral hover:bg-primary hover:text-secondary px-8 py-4 font-mono text-sm font-bold uppercase transition-none border border-structural-border md:w-auto w-full flex items-center justify-center gap-2"
          >
            SEARCH ↗
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {['ALL', 'TRANSACTION', 'ADDRESS', 'NETWORK OBSERVATION', 'ALERT', 'RUN', 'EVIDENCE', 'SOURCE RECORD'].map((filter) => {
            const isSupported = ['ALL', 'TRANSACTION', 'ALERT', 'RUN'].includes(filter);
            return (
              <button
                key={filter}
                onClick={() => isSupported && setActiveFilter(filter as SearchFilter)}
                disabled={!isSupported}
                className={`px-3 py-1.5 font-mono text-[0.6875rem] font-bold uppercase border transition-none
                  ${!isSupported ? 'border-structural-border bg-neutral text-muted-ink opacity-40 cursor-not-allowed' :
                  activeFilter === filter ? 'border-primary bg-primary text-secondary' : 'border-structural-border bg-surface-accent text-secondary hover:bg-neutral'}`}
              >
                {filter} {!isSupported && '(UNSUPPORTED)'}
              </button>
            );
          })}
        </div>
      </section>

      <div className="flex flex-col lg:flex-row min-h-[500px]">
        <div className="flex-1 border-r border-structural-border bg-neutral flex flex-col">
          <div className="p-3 border-b border-structural-border bg-surface-accent font-mono text-[0.6875rem] font-bold text-muted-ink uppercase flex justify-between">
            <span>SEARCH RESULTS ({results.length})</span>
            <span>SCOPE: {currentRun ? currentRun.run_id : 'GLOBAL'}</span>
          </div>
          
          <div className="flex-1 overflow-auto">
            {searchStatus === 'SEARCHING' ? (
              <div className="p-8"><SystemState type="LOADING" /></div>
            ) : searchStatus === 'NO_RESULTS' ? (
              <div className="p-12 flex flex-col items-center text-center">
                <span className="font-display text-xl text-secondary mb-2 uppercase">NO RESULTS FOUND</span>
                <span className="font-mono text-[0.6875rem] text-muted-ink max-w-md">The search query did not return any exact or partial matches within the designated scope.</span>
              </div>
            ) : searchStatus === 'INVALID_QUERY' ? (
              <div className="p-12 flex flex-col items-center text-center">
                <span className="font-display text-xl text-secondary mb-2 uppercase">INVALID QUERY</span>
                <span className="font-mono text-[0.6875rem] text-muted-ink max-w-md">Please enter a valid identifier.</span>
              </div>
            ) : searchStatus === 'ERROR' ? (
              <div className="p-8"><SystemState type="ERROR" /></div>
            ) : results.length > 0 ? (
              <table className="w-full text-left border-collapse">
                <thead className="bg-surface-accent border-b border-structural-border">
                  <tr className="font-mono text-[0.625rem] text-muted-ink tracking-wider uppercase">
                    <th className="p-3 font-normal border-r border-structural-border w-24">TYPE</th>
                    <th className="p-3 font-normal border-r border-structural-border">IDENTIFIER</th>
                    <th className="p-3 font-normal w-24">ACTION</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-[0.6875rem] divide-y divide-structural-border">
                  {results.map((res, i) => (
                    <tr 
                      key={`${res.record_type}-${res.primary_identifier}-${i}`}
                      onClick={() => setSelectedResult(res)}
                      className={`cursor-pointer transition-none ${selectedResult === res ? 'bg-surface-accent text-secondary' : 'hover:bg-surface-accent text-muted-ink'}`}
                    >
                      <td className="p-3 border-r border-structural-border font-bold uppercase">
                        {res.record_type}
                      </td>
                      <td className="p-3 border-r border-structural-border truncate max-w-xs text-secondary">
                        {res.primary_identifier}
                      </td>
                      <td className="p-3 text-right">
                        <span className="text-secondary opacity-50 hover:opacity-100 font-bold">SELECT ↗</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-12 flex flex-col items-center text-center">
                <span className="font-display text-xl text-secondary mb-2 uppercase">AWAITING QUERY</span>
                <span className="font-mono text-[0.6875rem] text-muted-ink max-w-md">Enter an identifier in the search bar to query local analytical records.</span>
              </div>
            )}
          </div>
        </div>
        
        <aside className="w-full lg:w-96 bg-surface-accent flex flex-col">
          <div className="p-3 border-b border-structural-border bg-neutral font-mono text-[0.6875rem] font-bold text-muted-ink uppercase">
            RESULT INSPECTOR
          </div>
          
          <div className="flex-1 p-6">
            {!selectedResult ? (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
                <div className="w-12 h-12 border border-structural-border flex items-center justify-center mb-4">
                  <span className="font-mono text-xl text-muted-ink">?</span>
                </div>
                <span className="font-mono text-[0.6875rem] text-muted-ink">SELECT A RECORD TO INSPECT</span>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <div className="font-mono text-[0.625rem] font-bold text-primary uppercase mb-1">SELECTED ENTITY</div>
                  <div className="font-display text-2xl text-secondary break-all">{selectedResult.display_name}</div>
                </div>
                
                <div className="space-y-0 font-mono text-[0.6875rem] border-y border-structural-border divide-y divide-structural-border">
                  <div className="flex justify-between py-2">
                    <span className="text-muted-ink">RECORD TYPE:</span>
                    <span className="text-secondary font-bold uppercase">{selectedResult.record_type}</span>
                  </div>
                  <div className="flex flex-col py-2 gap-1">
                    <span className="text-muted-ink">IDENTIFIER:</span>
                    <span className="text-secondary font-bold break-all text-[0.625rem] leading-tight">{selectedResult.primary_identifier}</span>
                  </div>
                  {selectedResult.run_id && (
                    <div className="flex flex-col py-2 gap-1">
                      <span className="text-muted-ink">RUN CONTEXT:</span>
                      <span className="text-secondary font-bold break-all text-[0.625rem] leading-tight">{selectedResult.run_id}</span>
                    </div>
                  )}
                  {selectedResult.txid && (
                    <div className="flex flex-col py-2 gap-1">
                      <span className="text-muted-ink">TRANSACTION CONTEXT:</span>
                      <span className="text-secondary font-bold break-all text-[0.625rem] leading-tight">{selectedResult.txid}</span>
                    </div>
                  )}
                  <div className="flex justify-between py-2">
                    <span className="text-muted-ink">DATABASE:</span>
                    <span className="text-secondary font-bold">DUCKDB</span>
                  </div>
                </div>
                
                <div className="mt-4">
                  {getNavigationPath(selectedResult) ? (
                    <Link 
                      to={getNavigationPath(selectedResult)!}
                      className="w-full py-2.5 px-3 bg-secondary text-neutral hover:bg-primary hover:text-secondary transition-none font-mono text-[0.6875rem] font-bold flex items-center justify-between border border-structural-border"
                    >
                      <span>OPEN {selectedResult.record_type} WORKSPACE</span>
                      <span>↗</span>
                    </Link>
                  ) : (
                    <div className="w-full py-2.5 px-3 bg-neutral text-muted-ink font-mono text-[0.6875rem] font-bold flex items-center justify-between border border-structural-border cursor-not-allowed">
                      <span>NO DEDICATED INVESTIGATION VIEW</span>
                      <span>↗</span>
                    </div>
                  )}
                </div>
                
                <div className="p-3 bg-neutral border border-structural-border text-muted-ink font-mono text-[0.6875rem] leading-relaxed">
                  <div className="flex items-center gap-1.5 text-secondary font-bold uppercase mb-1">
                    <span className="w-1.5 h-1.5 bg-primary inline-block"></span>
                    LOCAL INTEGRITY NOTE: LOCAL SEARCH ONLY // NO CLOUD DEPENDENCY // RESOLVED AGAINST LOADED RUN ARTIFACTS
                  </div>
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>

      <section className="border-b border-structural-border bg-surface-accent p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 pb-2 border-b border-structural-border gap-2">
          <div className="flex items-center gap-2">
            <span className="font-display text-xl uppercase text-secondary">INVESTIGATION NAVIGATION // WORKSPACE DIRECTORY</span>
          </div>
          <span className="font-mono text-[0.6875rem] text-muted-ink">INVESTIGATION WORKFLOW</span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-5 border border-structural-border mb-6">
          {currentRun?.run_id ? (
            <Link to={`/runs/${currentRun.run_id}/alerts`} className="p-4 bg-surface-accent hover:bg-neutral transition-none border-r border-structural-border flex flex-col justify-between group">
              <div className="font-mono text-[0.6875rem] font-bold text-muted-ink group-hover:text-primary">01</div>
              <div className="mt-4">
                <span className="font-display text-sm font-bold uppercase text-secondary block">ALERT QUEUE</span>
                <span className="font-mono text-[0.6875rem] text-muted-ink">TRIAGE & ANOMALY RANK</span>
              </div>
            </Link>
          ) : (
            <div className="p-4 bg-surface-accent border-r border-structural-border flex flex-col justify-between opacity-50 cursor-not-allowed">
              <div className="font-mono text-[0.6875rem] font-bold text-muted-ink">01</div>
              <div className="mt-4">
                <span className="font-display text-sm font-bold uppercase text-secondary block">ALERT QUEUE</span>
                <span className="font-mono text-[0.6875rem] text-muted-ink">TRIAGE & ANOMALY RANK</span>
              </div>
            </div>
          )}
          <div className="p-4 bg-surface-accent border-r border-structural-border flex flex-col justify-between opacity-50 cursor-not-allowed">
            <div className="font-mono text-[0.6875rem] font-bold text-muted-ink">02</div>
            <div className="mt-4">
              <span className="font-display text-sm font-bold uppercase text-secondary block">ALERT INVESTIGATION</span>
              <span className="font-mono text-[0.6875rem] text-muted-ink">MODEL SIGNAL DRILLDOWN</span>
            </div>
          </div>
          <div className="p-4 bg-surface-accent border-r border-structural-border flex flex-col justify-between opacity-50 cursor-not-allowed">
            <div className="font-mono text-[0.6875rem] font-bold text-muted-ink">03</div>
            <div className="mt-4">
              <span className="font-display text-sm font-bold uppercase text-secondary block">TX INVESTIGATION</span>
              <span className="font-mono text-[0.6875rem] text-muted-ink">INPUT / OUTPUT STRUCTURE</span>
            </div>
          </div>
          <div className="p-4 bg-surface-accent border-r border-structural-border flex flex-col justify-between opacity-50 cursor-not-allowed">
            <div className="font-mono text-[0.6875rem] font-bold text-muted-ink">04</div>
            <div className="mt-4">
              <span className="font-display text-sm font-bold uppercase text-secondary block">NETWORK GRAPH</span>
              <span className="font-mono text-[0.6875rem] text-muted-ink">TOPOLOGY & PROPAGATION</span>
            </div>
          </div>
          <div className="p-4 bg-surface-accent flex flex-col justify-between col-span-2 md:col-span-1 border-t md:border-t-0 border-structural-border opacity-50 cursor-not-allowed">
            <div className="font-mono text-[0.6875rem] font-bold text-muted-ink">05</div>
            <div className="mt-4">
              <span className="font-display text-sm font-bold uppercase text-secondary block">PROVENANCE</span>
              <span className="font-mono text-[0.6875rem] text-muted-ink">EVIDENCE & TRACEABILITY</span>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-structural-border bg-secondary text-neutral p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-structural-border/40 gap-3">
          <div className="flex items-center gap-2">
            <span className="font-display text-xl uppercase tracking-wider text-neutral">
              EPISTEMIC BOUNDARY // LEGAL & ANALYTICAL SAFEGUARDS
            </span>
          </div>
          <span className="font-mono text-[0.6875rem] font-bold bg-primary text-secondary px-2.5 py-1 tracking-wider uppercase">
            STRICT NON-ASSERTION // ZERO SPECULATION POLICY
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 font-body text-sm text-neutral/80 leading-relaxed">
          <div className="p-4 border border-structural-border bg-secondary space-y-2">
            <div className="font-mono text-[0.6875rem] font-bold text-primary uppercase">
              STRUCTURAL PATTERN NOTICE
            </div>
            <p className="m-0">
              Structural anomaly does not mean criminal activity. CryptoNexus surfaces patterns for human investigation. It does not determine identity, ownership, or criminal intent.
            </p>
          </div>
          <div className="p-4 border border-structural-border bg-secondary space-y-2">
            <div className="font-mono text-[0.6875rem] font-bold text-primary uppercase">
              PSEUDONYMITY & SENSOR LIMITATIONS
            </div>
            <p className="m-0">
              Bitcoin addresses are pseudonymous identifiers. Address ≠ wallet ≠ entity. IP association ≠ ownership. GeoIP is enrichment, not identity. Network observation time is sensor observation time.
            </p>
          </div>
        </div>
      </section>
    </PageFrame>
  );
}
