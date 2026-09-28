import React from 'react';

type StateType = 'READY' | 'LOADING' | 'EMPTY' | 'NO_RESULTS' | 'ERROR' | 'INVALID_QUERY' | 'RUN_UNAVAILABLE' | 'TRANSACTION_UNAVAILABLE' | 'ALERT_UNAVAILABLE' | 'PIPELINE_RUNNING' | 'PIPELINE_COMPLETE' | 'LOCAL_OFFLINE';

interface SystemStateProps {
  type: StateType;
}

const stateMessages: Record<StateType, string> = {
  READY: "System ready.",
  LOADING: "Local operation in progress.",
  EMPTY: "No data available.",
  NO_RESULTS: "No matching records were returned for the current scope.",
  ERROR: "The requested operation could not be completed.",
  INVALID_QUERY: "The submitted query could not be processed.",
  RUN_UNAVAILABLE: "The requested analytical run is unavailable.",
  ALERT_UNAVAILABLE: "The requested alert is unavailable.",
  TRANSACTION_UNAVAILABLE: "The requested transaction record is unavailable.",
  PIPELINE_RUNNING: "The analytical pipeline is currently executing.",
  PIPELINE_COMPLETE: "The analytical pipeline has completed successfully.",
  LOCAL_OFFLINE: "Workspace operating in local/offline mode."
};

export function SystemState({ type }: SystemStateProps) {
  const isError = type === 'ERROR' || type === 'INVALID_QUERY' || type === 'RUN_UNAVAILABLE' || type === 'TRANSACTION_UNAVAILABLE' || type === 'ALERT_UNAVAILABLE';
  const role = isError ? 'alert' : 'status';
  const ariaLive = isError ? 'assertive' : 'polite';

  return (
    <div 
      className="flex flex-col items-center justify-center p-8 border border-structural-border bg-surface-accent text-center h-64"
      role={role}
      aria-live={ariaLive}
    >
      <div className="font-mono text-sm tracking-widest uppercase mb-2 border-b border-structural-border pb-1">
        {type.replace('_', ' ')}
      </div>
      <div className="font-body text-secondary mt-2">
        {stateMessages[type]}
      </div>
    </div>
  );
}

export function StatusTag({ children, active = false, critical = false }: { children: React.ReactNode, active?: boolean, critical?: boolean }) {
  let bgClass = "bg-transparent text-secondary";
  if (active) bgClass = "bg-secondary text-neutral";
  if (critical) bgClass = "bg-primary text-secondary";

  return (
    <span className={`border border-structural-border font-mono uppercase text-[0.6875rem] px-1.5 py-0.5 tracking-wider ${bgClass}`}>
      {children}
    </span>
  );
}
