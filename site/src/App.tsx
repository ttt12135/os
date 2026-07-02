import { HashRouter } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { AppRoutes } from './router';

export default function App() {
  return (
    <HashRouter>
      <AppShell>
        <AppRoutes />
      </AppShell>
    </HashRouter>
  );
}
