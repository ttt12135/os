import { Link } from 'react-router-dom'
import { ArrowRight, GitBranch } from 'lucide-react'

export function EmptyState({ title = '暂无数据', desc = '请先运行 export_site_data 导出网站数据。' }) {
  return <div className="empty"><b>{title}</b><p>{desc}</p></div>
}

export function StatCard({ label, value, hint }) {
  return <div className="stat-card glass"><span>{label}</span><b>{value ?? 0}</b><small>{hint}</small></div>
}

export function WorkCard({ item, type = 'work' }) {
  const detailPath = type === 'history' ? `/history/${item.repo_name}` : `/works/${item.repo_name}`
  return (
    <Link className="work-card glass" to={detailPath}>
      <div className="work-card-main">
        <div className="row gap wrap">
          <h3>{item.team_name || item.repo_name}</h3>
          <span className="pill blue">{item.project_type || 'unknown'}</span>
          {item.score_level && <span className="pill purple">{item.score_level}</span>}
        </div>
        <p className="muted">{item.school || 'unknown'} · {item.repo_name}</p>
        {item.repo_url && <p className="repo-url"><GitBranch size={14} />{item.repo_url}</p>}
        <div className="tag-row">
          {(item.core_modules || []).slice(0, 7).map((m) => <span className="tag" key={m}>{m}</span>)}
        </div>
      </div>
      <div className="work-metrics">
        {'overall_score' in item && <Metric label="总分" value={item.overall_score} highlight />}
        <Metric label="函数" value={item.function_count} />
        <Metric label="调用边" value={item.edge_count} />
        <Metric label="模块" value={item.module_count} />
      </div>
      <ArrowRight className="card-arrow" size={20} />
    </Link>
  )
}

export function Metric({ label, value, highlight }) {
  return <div className={highlight ? 'metric highlight' : 'metric'}><b>{value ?? 0}</b><span>{label}</span></div>
}
