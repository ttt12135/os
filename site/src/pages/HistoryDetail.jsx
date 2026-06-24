import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { fetchJson } from '../lib/data.js'
import { EmptyState, Metric } from '../components/Cards.jsx'

export default function HistoryDetail() {
  const { repoName } = useParams()
  const [detail, setDetail] = useState(null)
  useEffect(() => { fetchJson(`/data/history/${repoName}.json`, null).then(setDetail) }, [repoName])
  if (!detail) return <div className="container"><EmptyState title="未找到历史作品" desc={`缺少 /data/history/${repoName}.json`} /></div>
  return <div className="container">
    <Link className="back" to="/history"><ArrowLeft size={16} /> 返回历史库</Link>
    <section className="detail-hero glass"><div><span className="eyebrow">History Work</span><h1>{detail.team_name || detail.repo_name}</h1><p className="muted">{detail.school} · {detail.repo_name} · {detail.project_type}</p><p className="repo-url">{detail.repo_url}</p></div></section>
    <section className="metric-grid four"><Metric label="函数数量" value={detail.function_count} /><Metric label="调用边" value={detail.edge_count} /><Metric label="模块数量" value={detail.module_count} /><Metric label="结构复杂度" value={detail.structure_complexity} /></section>
    <section className="glass panel"><h2>核心模块</h2><div className="tag-row">{(detail.core_modules || []).map((m) => <span className="tag large" key={m}>{m}</span>)}</div></section>
    <section className="glass panel"><h2>技术特征</h2>{(detail.technical_features || []).length ? <ul className="clean-list">{detail.technical_features.map((x, i) => <li key={i}>{String(x)}</li>)}</ul> : <p className="muted">暂无技术特征数据。</p>}</section>
  </div>
}
