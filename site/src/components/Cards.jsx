import { Link } from 'react-router-dom'
import { ArrowRight, GitBranch } from 'lucide-react'
import { formatNumber, safeText, scoreLevelLabel } from '../lib/data.js'

export function EmptyState({ title = '暂无数据', desc = '请先运行 export_site_data 导出网站数据。' }) {
  return <div className="empty"><b>{title}</b><p>{desc}</p></div>
}

export function StatCard({ label, value, hint }) {
  return <div className="stat-card glass"><span>{label}</span><b>{formatNumber(value, '0')}</b><small>{hint}</small></div>
}

export function WorkCard({ item, type = 'work' }) {
  const detailPath = type === 'history' ? `/history/${item.repo_name}` : `/works/${item.repo_name}`
  const modules = Array.isArray(item.core_modules) ? item.core_modules.filter(Boolean) : []
  const languages = Array.isArray(item.main_languages) ? item.main_languages.filter(Boolean) : []

  return (
    <Link className="work-card glass" to={detailPath}>
      <div className="work-card-main">
        <div className="row gap wrap">
          <h3>{safeText(item.team_name || item.repo_name)}</h3>
          <span className="pill blue">{safeText(item.project_type, '项目类型暂无')}</span>
          {type === 'history' && <span className="pill">{languages.length ? languages.join(' / ') : '语言暂无'}</span>}
          {type !== 'history' && item.score_level && <span className="pill gold">{scoreLevelLabel(item.score_level)}</span>}
        </div>
        <p className="muted">{safeText(item.school, '学校暂无')} / {safeText(item.repo_name)}</p>
        {item.repo_url && <p className="repo-url"><GitBranch size={14} />{item.repo_url}</p>}
        <div className="tag-row">
          {modules.length ? modules.slice(0, 7).map((m) => <span className="tag" key={m}>{m}</span>) : <span className="tag muted-tag">核心模块暂无</span>}
        </div>
      </div>
      <div className="work-metrics">
        {type !== 'history' && 'overall_score' in item && <Metric label="综合评分" value={item.overall_score} highlight />}
        <Metric label="函数数" value={item.function_count} />
        <Metric label="调用边" value={item.edge_count} />
        <Metric label="模块数" value={item.module_count} />
      </div>
      <ArrowRight className="card-arrow" size={20} />
    </Link>
  )
}

export function Metric({ label, value, highlight }) {
  return <div className={highlight ? 'metric highlight' : 'metric'}><b>{formatNumber(value)}</b><span>{label}</span></div>
}
