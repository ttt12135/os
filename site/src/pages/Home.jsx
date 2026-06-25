import { useEffect, useMemo, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowRight, Brain, GitCompare, Layers, ShieldCheck } from 'lucide-react'
import { fetchJson, matchWorkByRepoInput } from '../lib/data.js'
import { StatCard, WorkCard, EmptyState } from '../components/Cards.jsx'

const flow = ['历史仓库入库', '新作品源码解析', '函数语义理解', '调用图与模块画像', '历史相似检索', 'RAG 语义检索', 'Hybrid 融合对比', '五维评分', '报告生成']

export default function Home() {
  const [stats, setStats] = useState({})
  const [works, setWorks] = useState([])
  const [repoInput, setRepoInput] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchJson('/data/site_stats.json', {}).then(setStats)
    fetchJson('/data/works_summary.json', []).then(setWorks)
  }, [])

  const recent = useMemo(() => works.slice(0, 3), [works])

  function submit() {
    const matched = matchWorkByRepoInput(works, repoInput)
    if (!repoInput.trim()) return setError('请输入 Git 仓库地址。')
    if (!matched) return setError('该仓库暂未生成预计算分析结果，请先完成后台分析并重新导出网站数据。')
    setError('')
    navigate(`/analyze?repo=${encodeURIComponent(matched.repo_name)}`)
  }

  return (
    <div className="container hero-page">
      <section className="hero grid-2">
        <div>
          <div className="tju-badge-row">
            <span className="tju-badge">天津大学</span>
            <span className="tju-badge muted-badge">Tianjin University</span>
            <span className="tju-badge gold-badge">求是</span>
          </div>

          <div className="eyebrow"><ShieldCheck size={16} /> TJU Kernel Track Intelligence Platform</div>
          <h1>天津大学内核赛道作品<br /><span>智能分析与历史对比平台</span></h1>
          <p className="hero-desc">
            面向操作系统比赛内核赛道，本平台由天津大学学生团队建设，将往届作品构建为历史知识库，
            对本届新作品进行源码结构解析、相似项目检索、Hybrid 历史对比和五维评分，并自动生成可视化分析报告。
          </p>
          <div className="search-box glass">
            <input value={repoInput} onChange={(e) => setRepoInput(e.target.value)} placeholder="输入本届作品 Git 仓库地址，例如 https://github.com/team/kernel.git" onKeyDown={(e) => e.key === 'Enter' && submit()} />
            <button onClick={submit}>开始查询 <ArrowRight size={16} /></button>
          </div>
          {error && <div className="notice warn">{error}</div>}
          
          <p className="tju-platform-note">
            当前平台采用“离线分析引擎 + 前端交互展示”架构。Python Agent 负责完成仓库分析、历史对比与五维评分，
            网站负责读取预计算结果并进行可视化展示。
          </p>
          
          <div className="hero-actions">
            <Link className="secondary-btn" to="/works">查看本届作品</Link>
            <Link className="secondary-btn" to="/history">浏览历史库</Link>
          </div>
        </div>
        <div className="pipeline glass tju-pipeline">
          <div className="tju-watermark">TJU</div>
          <div className="panel-title"><Brain size={18} /> 分析流水线</div>
          <div className="pipeline-subtitle">Tianjin University · 求是创新实践</div>
          {flow.map((item, idx) => <div className="flow-item" key={item}><span>{idx + 1}</span><b>{item}</b></div>)}
        </div>
      </section>

      <section className="stats-grid">
        <StatCard label="历史作品库" value={stats.history_count ?? 0} hint="indexed history repos" />
        <StatCard label="本届已分析" value={stats.analyzed_works ?? stats.target_work_count ?? 0} hint="target works" />
        <StatCard label="平均评分" value={stats.average_score ?? 0} hint="five-dimensional score" />
        <StatCard label="核心模块" value={stats.core_module_count ?? 0} hint="OS module coverage" />
      </section>

      <section className="section-head">
        <div><h2>平台能力</h2><p>从源码结构到公开展示，形成完整评估闭环。</p></div>
      </section>
      <div className="feature-grid">
        <div className="feature glass"><Layers /><h3>结构画像</h3><p>提取函数、调用边、模块归属和复杂度指标。</p></div>
        <div className="feature glass"><GitCompare /><h3>历史对比</h3><p>基于历史库进行结构检索、语义检索与融合排序。</p></div>
        <div className="feature glass"><ShieldCheck /><h3>评分解释</h3><p>围绕原创性、新颖性、可实践性、难度、完成度给出证据化评价。</p></div>
      </div>

      <section className="section-head">
        <div><h2>最近分析作品</h2><p>本届新内核仓库的最新评估结果。</p></div>
        <Link to="/works">全部作品 →</Link>
      </section>
      {recent.length ? recent.map((item) => <WorkCard key={item.repo_name} item={item} />) : <EmptyState />}
    </div>
  )
}
