import { useEffect, useMemo, useState } from 'react'
import { fetchJson } from '../lib/data.js'
import { EmptyState, WorkCard } from '../components/Cards.jsx'

export default function History() {
  const [items, setItems] = useState([])
  const [keyword, setKeyword] = useState('')

  useEffect(() => { fetchJson('/data/history_summary.json', []).then(setItems) }, [])

  const filtered = useMemo(() => {
    const query = keyword.trim().toLowerCase()
    return items.filter((item) => {
      if (!query) return true
      return [item.repo_name, item.team_name, item.school, item.project_type, ...(item.core_modules || []), ...(item.main_languages || [])]
        .join(' ')
        .toLowerCase()
        .includes(query)
    })
  }, [items, keyword])

  return <div className="container">
    <div className="page-title">
      <span>History Knowledge Base</span>
      <h1>往届作品历史知识库</h1>
      <p>历史库用于支撑本届作品的相似项目检索和创新性判断。每个样本保留主要语言、核心模块、函数数量、调用边和模块数量等结构画像。</p>
    </div>
    <div className="data-toolbar glass">
      <div><b>{filtered.length}</b><span>个历史样本</span></div>
      <input className="filter-input" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="搜索历史作品、学校、队伍、模块或语言..." />
    </div>
    <div className="list-stack">
      {filtered.length ? filtered.map((item) => <WorkCard key={item.repo_name} item={item} type="history" />) : <EmptyState title="暂无历史库数据" desc="请确认已导出 /data/history_summary.json。" />}
    </div>
  </div>
}
