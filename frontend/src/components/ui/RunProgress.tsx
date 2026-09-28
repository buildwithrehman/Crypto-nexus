import React from 'react';
import { RunResponse } from '../../lib/api';

const PIPELINE_STAGES = [
  'INGEST',
  'GEOIP',
  'CORRELATION',
  'CIH',
  'GRAPH',
  'GRAPH_ANALYSIS',
  'FEATURES',
  'ML_SCORING',
  'ALERTS',
  'FINALIZE'
];

interface RunProgressProps {
  run: RunResponse;
}

export function RunProgress({ run }: RunProgressProps) {
  const isFailed = run.status === 'FAILED';
  const isCompleted = run.status === 'COMPLETED';
  

  // Determine current stage index
  let currentIndex = -1;
  if (run.current_stage) {
    currentIndex = PIPELINE_STAGES.indexOf(run.current_stage);
  }
  
  if (isCompleted) {
    currentIndex = PIPELINE_STAGES.length;
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6 flex flex-col gap-8">
      <div className="border border-structural-border bg-neutral p-6">
        <div className="flex items-center justify-between mb-8 border-b border-structural-border pb-4">
          <div>
            <div className="font-mono text-xs font-bold text-primary uppercase mb-1">RUN METADATA</div>
            <h2 className="font-display text-2xl uppercase text-secondary tracking-tight">PIPELINE EXECUTION</h2>
            <div className="font-mono text-xs text-muted-ink mt-2">CASE ID: {run.run_id}</div>
          </div>
          <div className="flex flex-col items-end">
            <div className="font-mono text-[0.6875rem] text-muted-ink uppercase mb-1">STATUS</div>
            <div className={`px-3 py-1 font-mono text-sm font-bold uppercase border border-structural-border ${
              isFailed ? 'bg-red-950/50 text-red-500 border-red-900' : 
              isCompleted ? 'bg-primary text-secondary' : 
              'bg-secondary text-neutral'
            }`}>
              {run.status}
            </div>
          </div>
        </div>

        {isFailed && (
          <div className="mb-8 p-4 border border-red-900 bg-red-950/20">
            <div className="font-mono text-xs font-bold text-red-500 uppercase mb-2">PIPELINE FAILED</div>
            <div className="font-mono text-[0.6875rem] text-red-400 mb-1">STAGE: {run.failed_stage || 'UNKNOWN'}</div>
            <div className="font-mono text-[0.6875rem] text-red-400 break-all">{run.error_message || 'No error message provided.'}</div>
          </div>
        )}

        <div className="flex flex-col gap-2">
          {PIPELINE_STAGES.map((stage, idx) => {
            const isPast = currentIndex > idx;
            const isCurrent = currentIndex === idx && !isFailed && !isCompleted;
            const isFailedStage = isFailed && run.failed_stage === stage;
            
            let statusText = '[ PENDING ]';
            let colorClass = 'text-muted-ink';
            
            if (isPast || isCompleted) {
              statusText = '[ COMPLETED ]';
              colorClass = 'text-primary';
            } else if (isCurrent) {
              statusText = '[ EXECUTING ]';
              colorClass = 'text-secondary animate-pulse';
            } else if (isFailedStage) {
              statusText = '[ FAILED ]';
              colorClass = 'text-red-500';
            } else if (isFailed) {
              statusText = '[ ABORTED ]';
            }

            return (
              <div key={stage} className={`flex justify-between items-center p-3 border border-structural-border ${isCurrent ? 'bg-surface-accent' : 'bg-neutral'}`}>
                <div className="flex items-center gap-4">
                  <span className={`font-mono text-xs font-bold ${colorClass}`}>
                    {(idx + 1).toString().padStart(2, '0')}
                  </span>
                  <span className={`font-display text-sm uppercase font-bold ${colorClass}`}>
                    {stage}
                  </span>
                </div>
                <div className={`font-mono text-[0.6875rem] font-bold tracking-wider ${colorClass}`}>
                  {statusText}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
