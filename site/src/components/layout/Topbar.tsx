import { Menu } from 'lucide-react';

export function Topbar({ onMenu }: { onMenu: () => void }) {
  return (
    <header className="topbar">
      <button className="icon-button" type="button" onClick={onMenu} aria-label="Open navigation">
        <Menu size={20} />
      </button>
      <div>
        <strong>KernelInsight</strong>
        <span>OS Kernel Repository Review Workspace</span>
      </div>
    </header>
  );
}
