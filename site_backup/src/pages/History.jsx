import { useEffect, useMemo, useState } from 'react'
import { fetchJson } from '../lib/data.js'
import { WorkCard, EmptyState } from '../components/Cards.jsx'

export default function History() {
  const [items, setItems] = useState([])
  const [keyword, setKeyword] = useState('')
  useEffect(() => { fetchJson('/data/history_summary.json', []).then(setItems) }, [])
  const filtered = useMemo(() => items.filter((item) => [item.repo_name, item.team_name, item.school, item.project_type, ...(item.core_modules || []), ...(item.main_languages || [])].join(' ').toLowerCase().includes(keyword.toLowerCase())), [items, keyword])
  return <div className="container">
    <div className="page-title"><span>History Knowledge Base</span><h1>往届历史作品库</h1><p>历史库用于为新作品提供相似项目检索、结构对比和创新性判断依据。</p></div>
    <input className="filter-input" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="搜索历史作品、学校、模块、语言..." />
    <div className="list-stack">{filtered.length ? filtered.map((item) => <WorkCard key={item.repo_name} item={item} type="history" />) : <EmptyState title="暂无历史库数据" desc="请确认已导出 /data/history_summary.json。" />}</div>
  </div>
}
