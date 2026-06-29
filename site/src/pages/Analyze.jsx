import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2, Loader2 } from 'lucide-react'

const steps = ['识别仓库地址', '加载预计算项目画像', '读取调用图与模块画像', '加载历史相似作品', '读取 Hybrid 检索结果', '加载五维评分', '加载 Markdown 报告']

export default function Analyze() {
  const [params] = useSearchParams()
  const repo = params.get('repo')
  const navigate = useNavigate()
  const [active, setActive] = useState(0)

  useEffect(() => {
    if (!repo) return navigate('/search')
    const timer = setInterval(() => {
      setActive((cur) => {
        if (cur >= steps.length) {
          clearInterval(timer)
          setTimeout(() => navigate(`/works/${repo}`), 450)
          return cur
        }
        return cur + 1
      })
    }, 460)
    return () => clearInterval(timer)
  }, [repo, navigate])

  return <div className="container narrow center-page">
    <div className="glass analyze-card">
      <span className="eyebrow">Loading Static Analysis Result</span>
      <h1>正在加载预计算分析结果</h1>
      <p className="muted">当前仓库：<b className="mono blue-text">{repo}</b></p>
      <div className="step-list">
        {steps.map((step, idx) => {
          const done = idx < active
          const running = idx === active
          return <div className="step" key={step}>
            <span className={done ? 'step-icon done' : running ? 'step-icon running' : 'step-icon'}>{done ? <CheckCircle2 size={19} /> : running ? <Loader2 className="spin" size={19} /> : idx + 1}</span>
            <b className={done || running ? 'bright' : ''}>{step}</b>
          </div>
        })}
      </div>
    </div>
  </div>
}
