import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { loadRepoDetail, safeFetchJson } from '../lib/api';
import { getRepoName, type RepoRecord } from '../lib/adapters';
import { asArray, encodedName, toDisplay } from '../lib/utils';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';

const gateNames = ['Similarity Check', 'Difference Check', 'Evidence Check', 'Risk Check', 'Final Verdict'];

export function Compare() {
  const params = useParams();
  const repoName = params.repoName ? decodeURIComponent(params.repoName) : '';
  const [loading, setLoading] = useState(true);
  const [repo, setRepo] = useState<RepoRecord | null>(null);
  const [comparisons, setComparisons] = useState<RepoRecord[]>([]);

  useEffect(() => {
    let alive = true;
    async function load() {
      const [detail, comparisonRaw] = await Promise.all([loadRepoDetail(repoName), safeFetchJson<unknown>(`/data/comparisons/${encodeURIComponent(repoName)}.json`, {})]);
      if (!alive) return;
      setRepo(detail);
      setComparisons(asArray<RepoRecord>(comparisonRaw));
      setLoading(false);
    }
    load();
    return () => { alive = false; };
  }, [repoName]);

  if (loading) return <LoadingState />;
  if (!comparisons.length) return <EmptyState title="暂无历史对比数据" message="请先完成 target 仓库分析和历史项目检索。" />;

  const first = comparisons[0] ?? {};
  const gates = gateNames.map((name) => ({ name, status: 'done', conclusion: toDisplay(first.similarity_summary ?? first.final_verdict ?? first.verdict), evidence: toDisplay(first.main_similarities ?? first.main_differences ?? first.target_advantages) }));

  return (
    <div className="page-stack">
      <section className="page-title"><p className="eyebrow">Comparison</p><h1>{repo ? getRepoName(repo) : repoName}</h1><p>Review Gate 用于检查 target 仓库与相似历史项目之间的相似、差异、证据与风险。</p><Link to={`/workspaces/${encodedName(repoName)}`}>返回详情页</Link></section>
      <section className="gate-grid">{gates.map((gate) => <div className="gate-card" key={gate.name}><span>{gate.status}</span><h3>{gate.name}</h3><p>{gate.conclusion}</p><small>{gate.evidence}</small></div>)}</section>
      <section className="section-block"><h2>相似历史项目列表</h2><div className="similar-list">{comparisons.map((item, index) => <div className="similar-card" key={`${toDisplay(item.history_repo_name)}-${index}`}><div><span>#{index + 1}</span><strong>{toDisplay(item.history_repo_name ?? item.repo_name)}</strong></div><p>{toDisplay(item.similarity_summary)}</p><dl><div><dt>相似度</dt><dd>{toDisplay(item.similarity_score ?? item.hybrid_score)}</dd></div><div><dt>置信度</dt><dd>{toDisplay(item.comparison_confidence)}</dd></div></dl><div className="reason-grid"><div><h3>相似点</h3><p>{toDisplay(item.main_similarities)}</p></div><div><h3>差异点</h3><p>{toDisplay(item.main_differences)}</p></div><div><h3>目标优势</h3><p>{toDisplay(item.target_advantages)}</p></div><div><h3>目标短板</h3><p>{toDisplay(item.target_weaknesses)}</p></div></div></div>)}</div></section>
    </div>
  );
}
