import { ClipboardCopy, Download } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { loadSummary, safeFetchJson, safeFetchText } from '../lib/api';
import { getLevel, getRepoName, getRepoUrl, getSchool, getScore, getStrengths, getTeamName, getWeaknesses, getYear, hasUsableScore, normalizeRepo, type RepoRecord } from '../lib/adapters';
import { asArray, downloadText, toDisplay } from '../lib/utils';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { MarkdownViewer } from '../components/common/MarkdownViewer';
import { RankingTable } from '../components/ranking/RankingTable';

export function Ranking() {
  const [mode, setMode] = useState<'target' | 'history'>('target');
  const [loading, setLoading] = useState(true);
  const [targetRows, setTargetRows] = useState<RepoRecord[]>([]);
  const [historyRows, setHistoryRows] = useState<RepoRecord[]>([]);
  const [targetReport, setTargetReport] = useState('');
  const [historyReport, setHistoryReport] = useState('');

  useEffect(() => {
    let alive = true;
    async function load() {
      const [targetRankingRaw, historyRankingRaw, works, history, targetMdA, targetMdB, historyMd] = await Promise.all([
        safeFetchJson<unknown>('/data/target_repository_quality_ranking.json', []),
        safeFetchJson<unknown>('/data/history_repository_quality_ranking.json', []),
        loadSummary('/data/works_summary.json'),
        loadSummary('/data/history_summary.json'),
        safeFetchText('/reports/target_repository_quality_ranking.md', ''),
        safeFetchText('/data/target_repository_quality_ranking.md', ''),
        safeFetchText('/reports/history_repository_quality_ranking.md', '')
      ]);
      if (!alive) return;
      const targetFallback = works.map((row) => normalizeRepo(row, 'target')).filter(hasUsableScore).sort((a, b) => (getScore(b) ?? -1) - (getScore(a) ?? -1));
      const historyFallback = history.map((row) => normalizeRepo(row, 'history')).filter(hasUsableScore).sort((a, b) => (getScore(b) ?? -1) - (getScore(a) ?? -1));
      setTargetRows(asArray<RepoRecord>(targetRankingRaw).length ? asArray<RepoRecord>(targetRankingRaw) : targetFallback);
      setHistoryRows(asArray<RepoRecord>(historyRankingRaw).length ? asArray<RepoRecord>(historyRankingRaw) : historyFallback);
      setTargetReport(targetMdA || targetMdB);
      setHistoryReport(historyMd);
      setLoading(false);
    }
    load();
    return () => { alive = false; };
  }, []);

  const rows = mode === 'target' ? targetRows : historyRows;
  const report = mode === 'target' ? targetReport : historyReport;
  const markdown = useMemo(() => {
    const title = mode === 'target' ? '# Target 作品质量排名' : '# History 作品质量排名';
    const lines = [title, '', '| 排名 | 队伍编号 | 综合评分 | 等级 | 主要优势 | 主要短板 |', '|---|---|---|---|---|---|'];
    rows.forEach((row, index) => lines.push(`| ${index + 1} | ${getRepoName(row)} | ${getScore(row) ?? '暂无评分'} | ${getLevel(row)} | ${toDisplay(getStrengths(row).slice(0, 2))} | ${toDisplay(getWeaknesses(row).slice(0, 2))} |`));
    return lines.join('\n');
  }, [mode, rows]);

  function exportJson() { downloadText(`${mode}_ranking.json`, JSON.stringify(rows, null, 2), 'application/json;charset=utf-8'); }
  function exportCsv() {
    const header = ['rank','repo_name','team_name','school','year','repo_url','score','level','strengths','weaknesses'];
    const csv = [header.join(','), ...rows.map((row, index) => [index + 1, getRepoName(row), getTeamName(row), getSchool(row), getYear(row), getRepoUrl(row), getScore(row) ?? '', getLevel(row), getStrengths(row).join('; '), getWeaknesses(row).join('; ')].map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))].join('\n');
    downloadText(`${mode}_ranking.csv`, csv, 'text/csv;charset=utf-8');
  }
  async function copyMarkdown() { await navigator.clipboard?.writeText(markdown); }

  if (loading) return <LoadingState />;

  return (
    <div className="page-stack">
      <section className="page-title"><p className="eyebrow">Ranking</p><h1>作品质量排名</h1><p>默认展示 Target Ranking，主分数使用最终综合评分口径。</p></section>
      <section className="toolbar"><div className="filter-tabs"><button className={mode === 'target' ? 'tab is-active' : 'tab'} onClick={() => setMode('target')} type="button">Target Ranking</button><button className={mode === 'history' ? 'tab is-active' : 'tab'} onClick={() => setMode('history')} type="button">History Ranking</button></div><div className="button-row"><button className="button button--subtle" onClick={exportJson} disabled={!rows.length} type="button"><Download size={16} />Download JSON</button><button className="button button--subtle" onClick={exportCsv} disabled={!rows.length} type="button"><Download size={16} />Download CSV</button><button className="button button--subtle" onClick={copyMarkdown} disabled={!rows.length} type="button"><ClipboardCopy size={16} />Copy Markdown Ranking</button></div></section>
      {rows.length ? <RankingTable rows={rows} /> : <EmptyState title={mode === 'target' ? '暂无 target 排名数据' : '暂无 history 排名数据'} message={mode === 'target' ? '请先运行 Python 分析系统生成 target_repository_quality_ranking.json 或 works_summary.json。' : '请先生成 history_repository_quality_ranking.json 或 history_summary.json。'} />}
      {report.trim() ? <section className="section-block"><h2>查看 Markdown 排名报告</h2><MarkdownViewer content={report} /></section> : null}
    </div>
  );
}

