import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Search as SearchIcon } from 'lucide-react'
import { fetchJson, matchWorkByRepoInput } from '../lib/data.js'

export default function Search() {
  const [works, setWorks] = useState([])
  const [input, setInput] = useState('')
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  useEffect(() => { fetchJson('/data/works_summary.json', []).then(setWorks) }, [])

  function submit() {
    const matched = matchWorkByRepoInput(works, input)
    if (!input.trim()) return setMessage('请输入本届作品 Git 仓库地址。')
    if (!matched) return setMessage('该仓库暂未生成预计算分析结果。请先将仓库加入作品清单，运行后台分析流程并重新导出网站数据。')
    setMessage('')
    navigate(`/analyze?repo=${encodeURIComponent(matched.repo_name)}`)
  }

  return <div className="container narrow center-page">
    <div className="glass search-large">
      <div className="big-icon"><SearchIcon /></div>
      <span className="eyebrow">Repository Lookup</span>
      <h1>仓库查询</h1>
      <p>输入本届作品 Git 仓库地址，网站会从已导出的静态 JSON 中匹配预计算分析结果。这里不会实时克隆仓库，也不会在前端执行分析逻辑。</p>
      <div className="search-box inner">
        <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && submit()} placeholder="https://github.com/xxx/kernel.git" />
        <button onClick={submit}>加载报告 <ArrowRight size={16} /></button>
      </div>
      {message && <div className="notice warn">{message}</div>}
    </div>
  </div>
}
