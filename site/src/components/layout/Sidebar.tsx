import { BarChart3, FileText, GitCompare, Home, ListChecks, Network, Trophy } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/workspaces', label: 'Workspaces', icon: Network },
  { to: '/ranking', label: 'Ranking', icon: Trophy },
  { to: '/scoring', label: 'Scoring', icon: BarChart3 },
  { to: '/method', label: 'Method', icon: ListChecks }
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand__mark">KI</div>
        <div>
          <strong>KernelInsight</strong>
          <span>Review Workspace</span>
        </div>
      </div>
      <nav className="nav-list" aria-label="Main navigation">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink key={link.to} to={link.to} end={link.to === '/'} onClick={onNavigate} className={({ isActive }) => isActive ? 'nav-link is-active' : 'nav-link'}>
              <Icon size={18} />
              <span>{link.label}</span>
            </NavLink>
          );
        })}
      </nav>
      <div className="sidebar__note">
        <GitCompare size={16} />
        <span>Static JSON / Markdown viewer</span>
      </div>
      <div className="sidebar__note">
        <FileText size={16} />
        <span>No backend runtime required</span>
      </div>
    </aside>
  );
}
