import { Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { loadSummary } from '../lib/api';
import { getLevel, getMetric, getRepoName, getRepoUrl, getSchool, getScope, getScore, getTeamName, getYear, normalizeRepo, type RepoRecord } from '../lib/adapters';
import { encodedName } from '../lib/utils';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { ScoreBadge } from '../components/common/ScoreBadge';

const filters = ['全部', 'target', 'history', '有报告', '无报告'];

export function Workspaces() {
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<RepoRecord[]>([]);
  const [filter, setFilter] = useState('全部');
  const [query, setQuery] = useState('');

  useEffect(() => {
    let alive = true;
    async function load() {
      const [works, history] = await Promise.all([loadSummary('/data/works_summary.json'), loadSummary('/data/history_summary.json')]);
      if (!alive) return;
      setRows([...works.map((row) => normalizeRepo(row, 'target')), ...history.map((row) => normalizeRepo(row, 'history'))]);
      setLoading(false);
    }
    load();
    return () => { alive = false; };
  }, []);

  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return rows.filter((repo) => {
      const scope = getScope(repo);
      const hasReport = Boolean(repo.report_url || repo.report_path || repo.final_report || repo.description_report);
      if (filter === 'target' && scope !== 'target') return false;
      if (filter === 'history' && scope !== 'history') return false;
      if (filter === '有报告' && !hasReport) return false;
      if (filter === '无报告' && hasReport) return false;
      if (!keyword) return true;
      const haystack = [getRepoName(repo), getTeamName(repo), getSchool(repo), getRepoUrl(repo)].join(' ').toLowerCase();
      return haystack.includes(keyword);
    });
  }, [filter, query, rows]);

  if (loading) return <LoadingState />;

  return (
    <div className="page-stack">
      <section className="page-title"><p className="eyebrow">Workspaces</p><h1>仓库列表</h1><p>展示 target 与 history 仓库，支持按 scope、报告状态和关键词筛选。</p></section>
      <section className="toolbar">
        <div className="filter-tabs">{filters.map((item) => <button key={item} className={filter === item ? 'tab is-active' : 'tab'} type="button" onClick={() => setFilter(item)}>{item}</button>)}</div>
        <label className="search-box"><Search size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索仓库名、队伍编号、学校或 Git 地址" /></label>
      </section>
      {!filtered.length ? <EmptyState /> : <><div className="table-wrap desktop-table"><table><thead><tr><th>仓库 / 队伍</th><th>学校</th><th>年份</th><th>Scope</th><th>Git 地址</th><th>评分</th><th>等级</th><th>代码块</th><th>函数</th><th>操作</th></tr></thead><tbody>{filtered.map((repo) => { const name = getRepoName(repo); const url = getRepoUrl(repo); return <tr key={`${getScope(repo)}-${name}`}><td><strong>{name}</strong><small>{getTeamName(repo)}</small></td><td>{getSchool(repo)}</td><td>{getYear(repo)}</td><td>{getScope(repo)}</td><td>{url !== '暂无数据' ? <a className="text-link" href={url} target="_blank" rel="noreferrer">{url}</a> : '暂无数据'}</td><td>{getScore(repo) === undefined ? '暂无评分' : `${getScore(repo)} / 100`}</td><td><ScoreBadge level={getLevel(repo)} /></td><td>{getMetric(repo, ['code_block_count', 'block_count', 'module_count'])}</td><td>{getMetric(repo, ['function_count', 'functions'])}</td><td><Link to={`/workspaces/${encodedName(name)}`}>查看详情</Link></td></tr>; })}</tbody></table></div><div className="mobile-cards">{filtered.map((repo) => { const name = getRepoName(repo); const url = getRepoUrl(repo); return <div className="repo-card" key={`mobile-${getScope(repo)}-${name}`}><div className="repo-card__head"><h3>{name}</h3><ScoreBadge level={getLevel(repo)} /></div><p>{getTeamName(repo)} · {getSchool(repo)} · {getYear(repo)}</p><p>Scope: {getScope(repo)}</p><p>Score: {getScore(repo) === undefined ? '暂无评分' : `${getScore(repo)} / 100`}</p>{url !== '暂无数据' ? <a className="text-link" href={url} target="_blank" rel="noreferrer">{url}</a> : null}<Link className="button" to={`/workspaces/${encodedName(name)}`}>查看详情</Link></div>; })}</div></>}
    </div>
  );
}
