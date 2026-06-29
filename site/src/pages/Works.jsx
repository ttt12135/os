import { useEffect, useMemo, useState } from 'react'
import { fetchJson } from '../lib/data.js'
import { EmptyState, WorkCard } from '../components/Cards.jsx'

export default function Works() {
  const [works, setWorks] = useState([])
  const [keyword, setKeyword] = useState('')

  useEffect(() => { fetchJson('/data/works_summary.json', []).then(setWorks) }, [])

  const filtered = useMemo(() => {
    const query = keyword.trim().toLowerCase()
    return [...works]
      .sort((a, b) => Number(b.overall_score || 0) - Number(a.overall_score || 0))
      .filter((item) => {
        if (!query) return true
        return [item.repo_name, item.team_name, item.school, item.project_type, item.score_level, ...(item.core_modules || []), ...(item.main_languages || [])]
          .join(' ')
          .toLowerCase()
          .includes(query)
      })
  }, [works, keyword])

  return <div className="container">
    <div className="page-title">
      <span>Works</span>
      <h1>本届作品评估结果</h1>
      <p>默认按综合评分从高到低排序，集中展示学校 / 队伍、仓库名称、评分等级、核心模块和结构统计。</p>
    </div>
    <div className="data-toolbar glass">
      <div><b>{filtered.length}</b><span>个匹配作品</span></div>
      <input className="filter-input" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="搜索学校、队伍、仓库、模块、语言或评分等级..." />
    </div>
    <div className="list-stack">
      {filtered.length ? filtered.map((item) => <WorkCard key={item.repo_name} item={item} />) : <EmptyState title="暂无匹配作品" desc="当前筛选条件下没有已导出的本届作品分析结果。" />}
    </div>
  </div>
}
