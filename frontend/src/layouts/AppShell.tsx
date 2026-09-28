import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { RunRibbon } from './RunRibbon';
import { RunProvider, useRunContext } from '../contexts/RunContext';

function AppShellInner() {
  const { run } = useRunContext();

  return (
    <div className="min-h-screen flex flex-col w-full">
      <Header />
      <RunRibbon run={run} />
      <main className="flex-1 w-full bg-neutral">
        <Outlet />
      </main>
      <footer className="w-full border-t border-structural-border px-6 py-8 flex flex-col md:flex-row justify-between items-center gap-4 bg-neutral">
        <div className="flex flex-col gap-2 max-w-xl text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-3">
            <img src="/images/logo.png" alt="CryptoNexus" className="h-8 w-auto object-contain" />
            <span className="font-mono text-[0.6875rem] border border-structural-border px-1.5 py-0.5 tracking-wider">
              LOCAL / OFFLINE
            </span>
          </div>
          <p className="font-body text-[0.8125rem] text-muted-ink">
            © 2026 CRYPTONEXUS. BITCOIN INTELLIGENCE PLATFORM. LOCAL / OFFLINE.
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-6 font-mono text-[0.6875rem] tracking-wider text-secondary">
          <div className="cursor-default hover:text-primary transition-colors">DISCLAIMER</div>
          <div className="cursor-default hover:text-primary transition-colors">METHODOLOGY</div>
          <div className="cursor-default hover:text-primary transition-colors">ABOUT</div>
        </div>
      </footer>
    </div>
  );
}

export function AppShell() {
  return (
    <RunProvider>
      <AppShellInner />
    </RunProvider>
  );
}
