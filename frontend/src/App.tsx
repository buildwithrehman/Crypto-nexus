import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './layouts/AppShell';
import { CommandCenter } from './pages/CommandCenter';
import { InvestigationQueue } from './pages/InvestigationQueue';
import { AlertInvestigation } from './pages/AlertInvestigation';
import { TransactionInvestigation } from './pages/TransactionInvestigation';
import { NetworkGraph } from './pages/NetworkGraph';
import { EvidenceProvenance } from './pages/EvidenceProvenance';
import { GlobalSearch } from './pages/GlobalSearch';
import { Landing } from './pages/Landing';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Landing />} />
          <Route path="runs/:runId" element={<CommandCenter />} />
          <Route path="runs/:runId/alerts" element={<InvestigationQueue />} />
          <Route path="runs/:runId/alerts/:alertId" element={<AlertInvestigation />} />
          <Route path="runs/:runId/transactions/:txid" element={<TransactionInvestigation />} />
          <Route path="runs/:runId/transactions/:txid/graph" element={<NetworkGraph />} />
          <Route path="runs/:runId/alerts/:alertId/provenance" element={<EvidenceProvenance />} />
          <Route path="search" element={<GlobalSearch />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
