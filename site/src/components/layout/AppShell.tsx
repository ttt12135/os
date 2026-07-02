import type { ReactNode } from 'react';
import { useState } from 'react';
import { MobileNav } from './MobileNav';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="app-shell">
      <div className="desktop-sidebar"><Sidebar /></div>
      <Topbar onMenu={() => setOpen(true)} />
      <MobileNav open={open} onClose={() => setOpen(false)} />
      <main className="main-content">{children}</main>
    </div>
  );
}
