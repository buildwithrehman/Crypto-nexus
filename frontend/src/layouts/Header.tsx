import { Link, useLocation } from 'react-router-dom';
import { Search } from 'lucide-react';
import { useRunContext } from '../contexts/RunContext';
import { useNavigate } from 'react-router-dom';

type NavItem = {
  label: string;
  path: string | null;
  isActive?: (pathname: string) => boolean;
};

const NAV_ITEMS: NavItem[] = [
  { label: 'OVERVIEW', path: '/', isActive: (p) => p === '/' },
  { label: 'INVESTIGATIONS', path: null, isActive: (p) => p.startsWith('/runs/') },
  { label: 'ANALYTICS', path: null },
  { label: 'DOCUMENTATION', path: null },
  { label: 'SEARCH', path: '/search', isActive: (p) => p === '/search' },
];

export function Header() {
  const navigate = useNavigate();
  const { run } = useRunContext();

  const handleStart = () => {
    if (run) navigate(`/runs/${run.id}`);
  };

  const location = useLocation();

  return (
    <header className="w-full border-b border-structural-border flex items-stretch justify-between px-6 py-0 bg-neutral sticky top-0 z-50">
      <div className="flex items-center gap-3 border-r border-structural-border pr-8 py-3.5">
        <Link to="/" className="flex items-center">
          <img src="/images/logo.png" alt="CryptoNexus" className="h-10 w-auto object-contain" />
        </Link>
      </div>

      <nav className="hidden md:flex items-stretch space-x-8">
        {NAV_ITEMS.map((item) => {
          const active = item.isActive ? item.isActive(location.pathname) : false;
          
          if (!item.path && !active) {
            return (
              <div
                key={item.label}
                className="flex items-center text-xs font-mono font-bold tracking-widest uppercase border-b-2 border-transparent text-muted-ink cursor-default"
              >
                {item.label}
              </div>
            );
          }
          
          if (!item.path && active) {
            return (
              <div
                key={item.label}
                className="flex items-center text-xs font-mono font-bold tracking-widest uppercase border-b-2 border-primary text-secondary cursor-default"
              >
                {item.label}
              </div>
            );
          }

          return (
            <Link
              key={item.label}
              to={item.path!}
              className={`flex items-center text-xs font-mono font-bold tracking-widest uppercase border-b-2 transition-colors ${
                active
                  ? 'border-primary text-secondary'
                  : 'border-transparent text-muted-ink hover:text-secondary hover:border-muted-ink'
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="flex items-center gap-6 border-l border-structural-border pl-8 py-3.5">
        <Link to="/search" className="text-secondary hover:text-primary transition-colors" aria-label="Search">
          <Search size={20} />
        </Link>
        <div className="font-mono text-xs font-bold border border-structural-border px-2 py-1 tracking-widest">
          LOCAL / OFFLINE
        </div>
        <button onClick={handleStart} className={`bg-secondary text-neutral hover:bg-primary hover:text-secondary px-6 py-2 font-mono text-[0.6875rem] font-bold tracking-widest uppercase transition-none ${!run && 'opacity-50 cursor-not-allowed'}`}>START INVESTIGATING ↗</button>
      </div>
    </header>
  );
}
