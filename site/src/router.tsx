import { Navigate, Route, Routes } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Workspaces } from './pages/Workspaces';
import { RepositoryDetail } from './pages/RepositoryDetail';
import { Ranking } from './pages/Ranking';
import { Compare } from './pages/Compare';
import { Scoring } from './pages/Scoring';
import { Method } from './pages/Method';
import { ReportPage } from './pages/ReportPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/workspaces" element={<Workspaces />} />
      <Route path="/workspaces/:repoName" element={<RepositoryDetail />} />
      <Route path="/ranking" element={<Ranking />} />
      <Route path="/compare/:repoName" element={<Compare />} />
      <Route path="/scoring" element={<Scoring />} />
      <Route path="/method" element={<Method />} />
      <Route path="/reports/:repoName" element={<ReportPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
