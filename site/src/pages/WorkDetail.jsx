import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowLeft, FileText, GitCompare } from 'lucide-react'
import { fetchJson, fetchText, scoreItems } from '../lib/data.js'
import { EmptyState, Metric } from '../components/Cards.jsx'

export default function WorkDetail() {
  const { repoName } = useParams()
  const [detail, setDetail] = useState(null)
  const [report, setReport] = useState('')
  useEffect(() => {
    fetchJson(`/data/works/${repoName}.json`, null).then((data) => {
      setDetail(data)
      if (data?.urls?.report_markdown) fetchText(data.urls.report_markdown, '').then(setReport)
      else fetchText(`/reports/${repoName}_final_report.md`, '').then(setReport)
    })
  }, [repoName])

  if (!detail) return <div className="container"><EmptyState title="正在加载或未找到作品数据" desc={`缺少 /data/works/${repoName}.json`} /></div>
  const scores = scoreItems(detail.score)

  return <div className="container">
    <Link className="back" to="/works"><ArrowLeft size={16} /> 返回作品列表</Link>
    <section className="detail-hero glass">
      <div><span className="eyebrow">Target Work</span><h1>{detail.team_name || detail.repo_name}</h1><p className="muted">{detail.school} · {detail.repo_name} · {detail.project_type}</p><p className="repo-url">{detail.repo_url}</p></div>
      <div className="score-badge"><span>综合评分</span><b>{detail.score?.overall_score ?? 0}</b><small>{detail.score?.score_level || 'unknown'}</small></div>
    </section>
    <section className="metric-grid four"><Metric label="函数数量" value={detail.function_count} /><Metric label="调用边" value={detail.edge_count} /><Metric label="模块数量" value={detail.module_count} /><Metric label="结构复杂度" value={detail.structure_complexity} /></section>
    <section className="grid-2 detail-grid">
      <div className="glass panel"><h2>五维评分</h2><div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><BarChart data={scores}><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" /><XAxis dataKey="name" stroke="#94a3b8" fontSize={12} /><YAxis stroke="#94a3b8" fontSize={12} /><Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #334155', borderRadius:12 }} /><Bar dataKey="value" fill="#38bdf8" radius={[8,8,0,0]} /></BarChart></ResponsiveContainer></div></div>
      <div className="glass panel"><h2><GitCompare size={19} /> 相似历史作品 Top-K</h2><div className="rank-list">{(detail.hybrid_top_results || []).map((x, i) => <Link to={`/compare/${repoName}`} className="rank-item" key={x.repo_name + i}><b>{i+1}. {x.repo_name}</b><span>Hybrid {x.hybrid_score ?? 0}</span><small>结构 {x.structured_score ?? 0} · 语义 {x.semantic_score ?? 0}</small></Link>)}{!(detail.hybrid_top_results || []).length && <EmptyState title="暂无相似项目数据" />}</div></div>
    </section>
    <section className="glass panel"><h2>核心模块</h2><div className="tag-row">{(detail.core_modules || []).map((m) => <span className="tag large" key={m}>{m}</span>)}</div></section>
    <section className="glass panel"><h2><FileText size={20} /> 最终分析报告</h2><article className="markdown"><ReactMarkdown>{report || '暂无 Markdown 报告内容。'}</ReactMarkdown></article></section>
  </div>
}
