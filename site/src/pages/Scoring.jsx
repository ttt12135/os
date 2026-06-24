import { useEffect, useState } from 'react'
import { fetchJson } from '../lib/data.js'
import { EmptyState } from '../components/Cards.jsx'

export default function Scoring() {
  const [logic, setLogic] = useState(null)
  useEffect(() => { fetchJson('/data/scoring_logic.json', null).then(setLogic) }, [])
  const dims = logic?.dimensions || []
  return <div className="container">
    <div className="page-title"><span>Scoring Logic</span><h1>{logic?.title || '内核赛道作品五维评分体系'}</h1><p>展示评分依据，让评委看到评分来自结构画像、历史对比和实现证据，而不是主观判断。</p></div>
    {!logic && <EmptyState title="暂无评分逻辑数据" desc="请确认已导出 /data/scoring_logic.json。" />}
    <section className="score-dim-grid">
      {dims.map((d) => <div className="glass score-dim" key={d.key}><div className="dim-head"><h2>{d.name}</h2><span>{d.english_name}</span><b>{d.max_score} 分</b></div><p>{d.meaning}</p><h4>主要依据</h4><ul>{(d.basis || []).map((x, i) => <li key={i}>{x}</li>)}</ul><div className="high-low"><div><b>高分表现</b><span>{d.high_score}</span></div><div><b>低分表现</b><span>{d.low_score}</span></div></div></div>)}
    </section>
    {logic?.workflow && <section className="glass panel"><h2>评分流程</h2><div className="workflow-row">{logic.workflow.map((x, i) => <div className="workflow-node" key={x}><span>{i+1}</span><b>{x}</b></div>)}</div></section>}
  </div>
}
