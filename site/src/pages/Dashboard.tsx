import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { loadSummary, safeFetchJson } from '../lib/api';
import { getLevel, getMetricNumber, getRepoName, getScore, normalizeRepo, type RepoRecord } from '../lib/adapters';
import { asArray, encodedName, toDisplay } from '../lib/utils';
import { AnalysisPipeline } from '../components/workspace/AnalysisPipeline';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { ScoreBadge } from '../components/common/ScoreBadge';
import { StatCard } from '../components/common/StatCard';

export function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<Record<string, unknown>>({});
  const [works, setWorks] = useState<RepoRecord[]>([]);
  const [ranking, setRanking] = useState<RepoRecord[]>([]);

  useEffect(() => {
    let alive = true;
    async function load() {
      const [siteStats, workRows, rankingRaw] = await Promise.all([
        safeFetchJson<Record<string, unknown>>('/data/site_stats.json', {}),
        loadSummary('/data/works_summary.json'),
        safeFetchJson<unknown>('/data/target_repository_quality_ranking.json', [])
      ]);
      if (!alive) return;
      const normalizedWorks = workRows.map((row) => normalizeRepo(row, 'target'));
      const rankingRows = asArray<RepoRecord>(rankingRaw).length ? asArray<RepoRecord>(rankingRaw) : normalizedWorks.filter((row) => getScore(row) !== undefined).sort((a, b) => (getScore(b) ?? -1) - (getScore(a) ?? -1));
      setStats(siteStats);
      setWorks(normalizedWorks);
      setRanking(rankingRows);
      setLoading(false);
    }
    load();
    return () => { alive = false; };
  }, []);

  const derived = useMemo(() => {
    const scores = works.map(getScore).filter((score): score is number => score !== undefined);
    const codeBlocks = works.reduce((sum, row) => sum + (getMetricNumber(row, ['code_block_count', 'block_count', 'module_count']) ?? 0), 0);
    return {
      targetCount: stats.target_work_count ?? stats.target_count ?? works.length,
      historyCount: stats.history_count ?? stats.history_repository_count ?? '暂无数据',
      blockCount: (stats.analyzed_code_blocks ?? stats.code_block_count ?? codeBlocks) || '暂无数据',
      reportCount: (stats.report_count ?? works.filter((row) => row.report_url || row.final_report).length) || '暂无数据',
      averageScore: stats.average_score ?? (scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length * 10) / 10 : '暂无数据'),
      maxScore: stats.max_score ?? (scores.length ? Math.max(...scores) : '暂无数据')
    };
  }, [stats, works]);

  if (loading) return <LoadingState />;

  return (
    <div className="page-stack">
      <section className="page-hero">
        <p className="eyebrow">KernelInsight</p>
        <h1>OS Kernel Repository Review Workspace</h1>
        <p>面向操作系统内核赛道的仓库分析、历史对比与评分展示平台。</p>
      </section>
      <section className="stat-grid">
        <StatCard label="历史仓库数量" value={toDisplay(derived.historyCount)} />
        <StatCard label="目标仓库数量" value={toDisplay(derived.targetCount)} />
        <StatCard label="已分析代码块数量" value={toDisplay(derived.blockCount)} />
        <StatCard label="已生成报告数量" value={toDisplay(derived.reportCount)} />
        <StatCard label="平均评分" value={toDisplay(derived.averageScore)} />
        <StatCard label="最高评分" value={toDisplay(derived.maxScore)} />
      </section>
      <section className="section-block">
        <div className="section-head"><div><p className="eyebrow">Analysis Pipeline</p><h2>离线分析流程</h2></div></div>
        <AnalysisPipeline compact />
      </section>
      <section className="two-column">
        <div className="section-block">
          <div className="section-head"><h2>Recent Workspaces</h2><Link to="/workspaces">查看全部</Link></div>
          {works.length ? <div className="list-stack">{works.slice(0, 5).map((repo) => { const name = getRepoName(repo); return <div className="workspace-row" key={name}><div><strong>{name}</strong><span>{getScore(repo) === undefined ? '暂无评分' : `${getScore(repo)} / 100`}</span></div><ScoreBadge level={getLevel(repo)} /><Link className="button button--subtle" to={`/workspaces/${encodedName(name)}`}>查看详情</Link></div>; })}</div> : <EmptyState />}
        </div>
        <div className="section-block">
          <div className="section-head"><h2>Target Ranking Preview</h2><Link to="/ranking">打开排名</Link></div>
          {ranking.length ? <div className="list-stack">{ranking.slice(0, 5).map((repo, index) => { const name = getRepoName(repo); return <div className="workspace-row" key={`${name}-${index}`}><div><strong>#{index + 1} {name}</strong><span>{getScore(repo) === undefined ? '暂无评分' : `${getScore(repo)} / 100`}</span></div><ScoreBadge level={getLevel(repo)} /><Link className="button button--subtle" to={`/reports/${encodedName(name)}`}>查看报告</Link></div>; })}</div> : <EmptyState title="暂无 target 排名数据" message="请先生成 target_repository_quality_ranking.json 或 works_summary.json。" />}
        </div>
      </section>
    </div>
  );
}

