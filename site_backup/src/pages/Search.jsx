import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search as SearchIcon, ArrowRight } from 'lucide-react'
import { fetchJson, matchWorkByRepoInput } from '../lib/data.js'

export default function Search() {
  const [works, setWorks] = useState([])
  const [input, setInput] = useState('')
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  useEffect(() => { fetchJson('/data/works_summary.json', []).then(setWorks) }, [])

  function submit() {
    const matched = matchWorkByRepoInput(works, input)
    if (!input.trim()) return setMessage('请输入 Git 仓库地址。')
    if (!matched) return setMessage('该仓库暂未生成预计算分析结果，请先完成后台分析并重新导出网站数据。')
    navigate(`/analyze?repo=${encodeURIComponent(matched.repo_name)}`)
  }

  return <div className="container narrow center-page">
    <div className="glass search-large">
      <div className="big-icon"><SearchIcon /></div>
      <h1>通过仓库地址查找评估报告</h1>
      <p>输入本届比赛新内核仓库地址，系统会从已导出的 works_summary.json 中匹配对应报告。</p>
      <div className="search-box inner">
        <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && submit()} placeholder="https://github.com/xxx/kernel.git" />
        <button onClick={submit}>匹配报告 <ArrowRight size={16} /></button>
      </div>
      {message && <div className="notice warn">{message}</div>}
    </div>
  </div>
}
