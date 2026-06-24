import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, GitCompare } from 'lucide-react'
import { fetchJson } from '../lib/data.js'
import { EmptyState } from '../components/Cards.jsx'

function ListBlock({ title, items }) {
  if (!items || !items.length) return null
  return <div className="mini-block"><b>{title}</b><ul>{items.map((x, i) => <li key={i}>{String(x)}</li>)}</ul></div>
}

export default function Compare() {
  const { repoName } = useParams()
  const [data, setData] = useState(null)
  useEffect(() => { fetchJson(`/data/comparisons/${repoName}.json`, null).then(setData) }, [repoName])
  const comparisons = data?.comparisons || []
  return <div className="container">
    <Link className="back" to={`/works/${repoName}`}><ArrowLeft size={16} /> 返回作品详情</Link>
    <div className="page-title"><span>Comparison</span><h1>{repoName} 的历史对比结果</h1><p>展示相似历史作品、结构相似性、语义相似性和可借鉴设计。</p></div>
    {!comparisons.length && <EmptyState title="暂无对比数据" desc={`缺少 /data/comparisons/${repoName}.json 或 comparisons 为空。`} />}
    <div className="compare-list">
      {comparisons.map((item, index) => <section className="glass compare-card" key={index}>
        <div className="compare-head"><div><span className="eyebrow">Top {index + 1}</span><h2><GitCompare size={20} /> {item.history_repo_name}</h2></div><div className="compare-score"><b>{item.similarity_score ?? 0}</b><span>similarity</span></div></div>
        {item.similarity_summary && <p className="summary-text">{item.similarity_summary}</p>}
        <div className="mini-grid"><ListBlock title="主要相似点" items={item.main_similarities} /><ListBlock title="主要差异点" items={item.main_differences} /><ListBlock title="目标项目优势" items={item.target_advantages} /><ListBlock title="目标项目不足" items={item.target_weaknesses} /><ListBlock title="可借鉴设计" items={item.borrowable_designs} /></div>
      </section>)}
    </div>
  </div>
}
