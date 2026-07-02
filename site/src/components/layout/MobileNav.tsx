import { X } from 'lucide-react';
import { Sidebar } from './Sidebar';

export function MobileNav({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  return (
    <div className="mobile-nav" role="dialog" aria-modal="true">
      <button className="mobile-nav__backdrop" onClick={onClose} aria-label="Close navigation" />
      <div className="mobile-nav__panel">
        <button className="icon-button mobile-nav__close" type="button" onClick={onClose} aria-label="Close navigation">
          <X size={20} />
        </button>
        <Sidebar onNavigate={onClose} />
      </div>
    </div>
  );
}
