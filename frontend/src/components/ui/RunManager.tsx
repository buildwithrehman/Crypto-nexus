import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, ApiError } from '../../lib/api';


export function RunManager({ demoRunId }: { demoRunId: string | null }) {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDemo = () => {
    if (demoRunId) {
      navigate(`/runs/${demoRunId}`);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      // 1. Create run
      const run = await apiClient.createRun();
      const runId = run.run_id;
      
      // 2. Upload file
      await apiClient.uploadDataset(runId, file);
      
      // 3. Execute run
      await apiClient.executeRun(runId);
      
      // 4. Navigate to progress state
      setIsOpen(false);
      navigate(`/runs/${runId}`);
    } catch (err: any) {
      setError(err instanceof ApiError ? err.message : String(err));
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-4">
      <button 
        onClick={handleDemo}
        disabled={!demoRunId}
        className={`bg-secondary text-neutral border border-structural-border px-8 py-4 font-mono text-[0.6875rem] font-bold uppercase tracking-wider transition-none flex items-center gap-2 ${demoRunId ? 'hover:bg-primary hover:text-secondary' : 'opacity-50 cursor-not-allowed'}`}
      >
        EXPLORE DEMO_V1 <span className="text-base leading-none">↗</span>
      </button>

      <button 
        onClick={() => setIsOpen(true)}
        className="bg-neutral text-secondary border border-structural-border px-8 py-4 font-mono text-[0.6875rem] font-bold uppercase tracking-wider transition-none hover:bg-surface-accent"
      >
        NEW INVESTIGATION (UPLOAD)
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-secondary/80 backdrop-blur-sm p-4">
          <div className="bg-neutral border border-structural-border w-full max-w-lg shadow-2xl flex flex-col">
            <div className="p-4 border-b border-structural-border flex justify-between items-center bg-surface-accent">
              <h2 className="font-display text-lg uppercase text-secondary">NEW INVESTIGATION RUN</h2>
              <button onClick={() => setIsOpen(false)} className="text-muted-ink hover:text-secondary font-mono text-sm">
                [X]
              </button>
            </div>
            
            <div className="p-6 flex flex-col gap-6">
              <div>
                <label className="font-mono text-xs font-bold text-secondary uppercase block mb-2">
                  DATASET PAYLOAD (.JSON, .CSV, .XML)
                </label>
                <input 
                  type="file" 
                  accept=".csv,.json,.xml"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full border border-structural-border p-3 font-mono text-xs focus:outline-none focus:border-primary bg-surface-accent text-secondary"
                  disabled={loading}
                />
              </div>

              {error && (
                <div className="p-3 border border-red-900 bg-red-950/20 text-red-500 font-mono text-xs">
                  {error}
                </div>
              )}

              <div className="flex justify-end pt-4 border-t border-structural-border">
                <button 
                  onClick={handleUpload}
                  disabled={!file || loading}
                  className={`bg-secondary text-neutral px-6 py-3 font-mono text-[0.6875rem] font-bold uppercase ${(!file || loading) ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary hover:text-secondary'}`}
                >
                  {loading ? 'PROCESSING...' : 'UPLOAD & EXECUTE'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
