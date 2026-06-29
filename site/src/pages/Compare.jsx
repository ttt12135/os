import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, GitCompare } from 'lucide-react'
import { fetchJson, formatNumber, safeText } from '../lib/data.js'
import { EmptyState } from '../components/Cards.jsx'

function ListBlock({ title, items }) {
  const list = Array.isArray(items) ? items.filter(Boolean) : []
  return <div className="mini-block">
    <b>{title}</b>
    {list.length ? <ul>{list.map((x, i) => <li key={i}>{String(x)}</li>)}</ul> : <p className="muted">暂无数据</p>}
  </div>
}

export default function Compare() {
  const { repoName } = useParams()
  const [data, setData] = useState(null)

  useEffect(() => { fetchJson(`/data/comparisons/${repoName}.json`, null).then(setData) }, [repoName])

  const comparisons = data?.comparisons || []

  return <div className="container">
    <Link className="back" to={`/works/${repoName}`}><ArrowLeft size={16} /> 返回作品详情</Link>
    <div className="page-title">
      <span>Historical Comparison</span>
      <h1>{safeText(repoName)} 的历史对比结果</h1>
      <p>页面展示目标作品与相似历史项目之间的关系，包括 Hybrid 综合分、结构相似分、语义相似分、主要相似点、差异点、优势、不足和可借鉴设计。</p>
    </div>

    {!comparisons.length && <EmptyState title="暂无对比数据" desc={`缺少 /data/comparisons/${repoName}.json 或 comparisons 为空。`} />}

    <div className="compare-list">
      {comparisons.map((item, index) => <section className="glass compare-card" key={`${item.history_repo_name}-${index}`}>
        <div className="compare-head">
          <div>
            <span className="eyebrow">Top {index + 1}</span>
            <h2><GitCompare size={20} /> {safeText(item.history_repo_name, '历史项目暂无')}</h2>
          </div>
          <div className="compare-score">
            <b>{formatNumber(item.hybrid_score ?? item.similarity_score, '0')}</b>
            <span>Hybrid 综合分</span>
            <div className="score-pair">
              <span className="pill">结构 {formatNumber(item.structured_score)}</span>
              <span className="pill">语义 {formatNumber(item.semantic_score)}</span>
            </div>
          </div>
        </div>

        <p className="summary-text">{safeText(item.similarity_summary, '暂无对比摘要。')}</p>

        <div className="mini-grid">
          <ListBlock title="主要相似点" items={item.main_similarities} />
          <ListBlock title="主要差异点" items={item.main_differences} />
          <ListBlock title="目标项目优势" items={item.target_advantages} />
          <ListBlock title="目标项目不足" items={item.target_weaknesses} />
          <ListBlock title="可借鉴设计" items={item.borrowable_designs} />
        </div>
      </section>)}
    </div>
  </div>
}
