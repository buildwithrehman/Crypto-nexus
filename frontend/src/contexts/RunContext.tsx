/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, ReactNode } from 'react';
import { ActiveRunContext } from '../layouts/RunRibbon';

type RunProviderState = {
  run: ActiveRunContext | undefined;
  setRun: (run: ActiveRunContext | undefined) => void;
};

export const RunContext = createContext<RunProviderState>({
  run: undefined,
  setRun: () => {},
});

export function useRunContext() {
  return useContext(RunContext);
}

export function RunProvider({ children }: { children: ReactNode }) {
  const [run, setRun] = useState<ActiveRunContext | undefined>(undefined);
  return (
    <RunContext.Provider value={{ run, setRun }}>
      {children}
    </RunContext.Provider>
  );
}
