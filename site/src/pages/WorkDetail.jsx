import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowLeft, FileText, GitCompare } from 'lucide-react'
import { fetchJson, fetchText, formatNumber, safeText, scoreItems, scoreLevelLabel } from '../lib/data.js'
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

  const score = detail.score || {}
  const scores = scoreItems(score)
  const modules = Array.isArray(detail.core_modules) ? detail.core_modules.filter(Boolean) : []
  const similar = Array.isArray(detail.hybrid_top_results) ? detail.hybrid_top_results : []

  return <div className="container">
    <Link className="back" to="/works"><ArrowLeft size={16} /> 返回作品列表</Link>

    <section className="detail-hero glass">
      <div>
        <span className="eyebrow">Target Work Dashboard</span>
        <h1>{safeText(detail.team_name || detail.repo_name)}</h1>
        <p className="muted">{safeText(detail.school, '学校暂无')} / {safeText(detail.repo_name)} / {safeText(detail.project_type, '项目类型暂无')}</p>
        <p className="repo-url">{safeText(detail.repo_url)}</p>
      </div>
      <div className="score-badge">
        <span>综合评分</span>
        <b>{formatNumber(score.overall_score ?? detail.overall_score, '0')}</b>
        <small>{scoreLevelLabel(score.score_level ?? detail.score_level)}</small>
      </div>
    </section>

    <section className="metric-grid four">
      <Metric label="函数数量" value={detail.function_count} />
      <Metric label="调用边数量" value={detail.edge_count} />
      <Metric label="模块数量" value={detail.module_count} />
      <Metric label="结构复杂度" value={detail.structure_complexity} />
    </section>

    <section className="grid-2 detail-grid">
      <div className="glass panel">
        <h2>五维评分图</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={scores}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 20]} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="value" fill="#38bdf8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass panel">
        <h2><GitCompare size={19} /> 相似历史作品 Top-K</h2>
        <div className="rank-list">
          {similar.length ? similar.map((x, i) => (
            <Link to={`/compare/${repoName}`} className="rank-item" key={`${x.repo_name}-${i}`}>
              <b>{i + 1}. {safeText(x.repo_name)}</b>
              <span>Hybrid {formatNumber(x.hybrid_score)}</span>
              <small>结构相似 {formatNumber(x.structured_score)} / 语义相似 {formatNumber(x.semantic_score)}</small>
            </Link>
          )) : <EmptyState title="暂无相似历史作品数据" desc="当前作品尚未导出 Hybrid Top-K 检索结果。" />}
        </div>
      </div>
    </section>

    <section className="glass panel">
      <h2>核心模块</h2>
      <div className="tag-row">
        {modules.length ? modules.map((m) => <span className="tag large" key={m}>{m}</span>) : <span className="tag large muted-tag">暂无数据</span>}
      </div>
    </section>

    <section className="grid-2 detail-grid">
      <div className="glass panel">
        <h2>评分优势</h2>
        {(score.strengths || []).length ? <ul className="clean-list">{score.strengths.map((x, i) => <li key={i}>{String(x)}</li>)}</ul> : <p className="muted">暂无数据</p>}
      </div>
      <div className="glass panel">
        <h2>待完善方向</h2>
        {(score.weaknesses || []).length ? <ul className="clean-list">{score.weaknesses.map((x, i) => <li key={i}>{String(x)}</li>)}</ul> : <p className="muted">暂无数据</p>}
      </div>
    </section>

    <section className="glass panel">
      <h2><FileText size={20} /> Markdown 分析报告</h2>
      <article className="markdown"><ReactMarkdown>{report || '暂无 Markdown 报告内容。'}</ReactMarkdown></article>
    </section>
  </div>
}
