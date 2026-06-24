import { useEffect, useMemo, useState } from 'react'
import { fetchJson } from '../lib/data.js'
import { WorkCard, EmptyState } from '../components/Cards.jsx'

export default function Works() {
  const [works, setWorks] = useState([])
  const [keyword, setKeyword] = useState('')
  useEffect(() => { fetchJson('/data/works_summary.json', []).then(setWorks) }, [])
  const filtered = useMemo(() => works.filter((item) => [item.repo_name, item.team_name, item.school, item.project_type, ...(item.core_modules || []), ...(item.main_languages || [])].join(' ').toLowerCase().includes(keyword.toLowerCase())), [works, keyword])
  return <div className="container">
    <div className="page-title"><span>Works</span><h1>本届新作品评估结果</h1><p>展示本届内核仓库的结构画像、五维评分和历史对比入口。</p></div>
    <input className="filter-input" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="搜索学校、队伍、仓库、模块、语言..." />
    <div className="list-stack">{filtered.length ? filtered.map((item) => <WorkCard key={item.repo_name} item={item} />) : <EmptyState />}</div>
  </div>
}
