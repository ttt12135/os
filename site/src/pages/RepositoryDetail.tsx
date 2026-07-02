import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { loadRepoDetail, loadReports, loadSummary, safeFetchJson } from '../lib/api';
import { getDescription, getMetricNumber, getRepoName, getScope, getScore, getStrengths, getWeaknesses, mergeByRepoName, normalizeRepo, type RepoRecord } from '../lib/adapters';
import { asArray, encodedName, extractReportOverview, truncateMarkdown } from '../lib/utils';
import { AnalysisPipeline } from '../components/workspace/AnalysisPipeline';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { RepositoryIdentityCard } from '../components/workspace/RepositoryIdentityCard';
import { ScoreBar } from '../components/common/ScoreBar';
import { EvidencePanel } from '../components/workspace/EvidencePanel';
import { SimilarHistoryList } from '../components/workspace/SimilarHistoryList';
import { ReportTabs } from '../components/workspace/ReportTabs';

export function RepositoryDetail() {
  const params = useParams();
  const repoName = params.repoName ? decodeURIComponent(params.repoName) : '';
  const [loading, setLoading] = useState(true);
  const [repo, setRepo] = useState<RepoRecord | null>(null);
  const [reports, setReports] = useState({ description: '', final: '' });
  const [comparisons, setComparisons] = useState<RepoRecord[]>([]);

  useEffect(() => {
    let alive = true;
    async function load() {
      const [works, history] = await Promise.all([loadSummary('/data/works_summary.json'), loadSummary('/data/history_summary.json')]);
      const summary = [...works.map((row) => normalizeRepo(row, 'target')), ...history.map((row) => normalizeRepo(row, 'history'))].find((row) => getRepoName(row) === repoName);
      const detail = await loadRepoDetail(repoName, summary ? getScope(summary) : undefined);
      const comparisonRaw = await safeFetchJson<unknown>(`/data/comparisons/${encodeURIComponent(repoName)}.json`, {});
      const reportContent = await loadReports(repoName);
      if (!alive) return;
      setRepo(detail ? mergeByRepoName(detail, summary) : summary ?? null);
      setComparisons(asArray<RepoRecord>(comparisonRaw));
      setReports(reportContent);
      setLoading(false);
    }
    load();
    return () => { alive = false; };
  }, [repoName]);

  const overview = useMemo(() => {
    if (!repo) return '';
    const jsonDescription = getDescription(repo);
    if (jsonDescription !== '暂无项目描述') return jsonDescription;
    const descriptionOverview = extractReportOverview(reports.description);
    if (descriptionOverview) return descriptionOverview;
    const finalOverview = extractReportOverview(reports.final);
    if (finalOverview) return finalOverview;
    if (reports.description.trim()) return truncateMarkdown(reports.description) || '暂无项目描述';
    if (reports.final.trim()) return truncateMarkdown(reports.final) || '暂无项目描述';
    return '暂无项目描述';
  }, [repo, reports]);

  if (loading) return <LoadingState />;
  if (!repo) return <EmptyState title="暂无数据" message="未找到该仓库的 summary 或 detail JSON。" />;

  const score = getScore(repo);
  const scoreItems = [
    ['原创性', getMetricNumber(repo, ['originality_score', 'originality']) ?? score],
    ['新颖性', getMetricNumber(repo, ['novelty_score', 'innovation_score', 'novelty']) ?? score],
    ['可实践性', getMetricNumber(repo, ['practicality_score', 'practicality']) ?? score],
    ['技术难度', getMetricNumber(repo, ['technical_difficulty_score', 'difficulty_score']) ?? score],
    ['完成度', getMetricNumber(repo, ['completion_score', 'completeness_score']) ?? score]
  ] as const;

  return (
    <div className="page-stack">
      <RepositoryIdentityCard repo={repo} />
      <section className="section-block"><div className="section-head"><h2>Overview</h2><Link to={`/reports/${encodedName(getRepoName(repo))}`}>打开独立报告页</Link></div><p className="readable-text">{overview}</p></section>
      <section className="section-block"><div className="section-head"><h2>Analysis Pipeline</h2></div><AnalysisPipeline repo={repo} /></section>
      <section className="detail-grid"><div className="section-block"><h2>Score Summary</h2><div className="score-list">{scoreItems.map(([label, value]) => <ScoreBar key={label} label={label} score={value} />)}</div></div><div className="section-block"><h2>Why This Score</h2><div className="reason-grid"><div><h3>优势</h3>{getStrengths(repo).length ? <ul>{getStrengths(repo).map((item) => <li key={item}>{item}</li>)}</ul> : <p>暂无明确优势说明</p>}</div><div><h3>短板</h3>{getWeaknesses(repo).length ? <ul>{getWeaknesses(repo).map((item) => <li key={item}>{item}</li>)}</ul> : <p>暂无明确短板说明</p>}</div></div></div></section>
      <section className="section-block"><h2>Evidence Panel</h2><EvidencePanel repo={repo} hasFinalReport={Boolean(reports.final.trim())} hasComparison={comparisons.length > 0} /></section>
      {getScope(repo) === 'target' ? <section className="section-block"><h2>Similar History</h2><SimilarHistoryList comparisons={comparisons} repoName={repoName} /></section> : null}
      <section className="section-block"><h2>Reports</h2><ReportTabs description={reports.description} final={reports.final} /></section>
    </div>
  );
}


