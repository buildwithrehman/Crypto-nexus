export type ActiveRunContext = {
  id?: string;
  source?: string;
  blocks?: string;
  model?: string;
  status?: string;
};

export function RunRibbon({ run }: { run?: ActiveRunContext }) {
  if (!run) {
    return (
      <div className="w-full border-b border-structural-border bg-primary text-secondary px-6 py-2 flex items-center justify-between font-mono text-xs font-bold uppercase tracking-widest overflow-x-auto whitespace-nowrap">
        <span>RUN ID: NONE</span>
        <span>RUNTIME: LOCAL/OFFLINE</span>
        <span>DATABASE: DUCKDB</span>
        <span>RUN STATUS: NO ACTIVE RUN</span>
      </div>
    );
  }

  return (
    <div className="w-full border-b border-structural-border bg-primary text-secondary px-6 py-2 flex items-center gap-8 font-mono text-xs font-bold uppercase tracking-widest overflow-x-auto whitespace-nowrap">
      <span>RUN ID: {run.id || '[DYNAMIC RUN ID]'}</span>
      <span>SOURCE: {run.source || '[DYNAMIC SOURCE]'}</span>
      <span>SOURCE BLOCKS: {run.blocks || '[DYNAMIC SOURCE BLOCK RANGE]'}</span>
      <span>RUNTIME: LOCAL/OFFLINE</span>
      <span>MODEL: {run.model || '[DYNAMIC MODEL]'}</span>
      <span>DATABASE: DUCKDB</span>
      <span>RUN STATUS: {run.status || '[DYNAMIC RUN STATUS]'}</span>
    </div>
  );
}
