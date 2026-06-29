import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, BarChart3, Brain, Database, GitCompare, Layers, ShieldCheck } from 'lucide-react'
import { fetchJson, matchWorkByRepoInput } from '../lib/data.js'
import { EmptyState, StatCard, WorkCard } from '../components/Cards.jsx'

const flow = [
  '历史库入库',
  '新作品解析',
  '函数理解',
  '调用图与模块画像',
  '相似检索',
  'Hybrid 对比',
  '五维评分',
  '报告生成',
]

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

  const recent = useMemo(
    () => [...works].sort((a, b) => Number(b.overall_score || 0) - Number(a.overall_score || 0)).slice(0, 3),
    [works],
  )

  function submit() {
    const matched = matchWorkByRepoInput(works, repoInput)
    if (!repoInput.trim()) return setError('请输入本届作品 Git 仓库地址。')
    if (!matched) return setError('该仓库暂未生成预计算分析结果。请先将仓库加入作品清单，运行后台分析流程并重新导出网站数据。')
    setError('')
    navigate(`/analyze?repo=${encodeURIComponent(matched.repo_name)}`)
  }

  return (
    <div className="container hero-page">
      <section className="hero grid-2">
        <div>
          <div className="tju-badge-row">
            <span className="tju-badge">天津大学 · Tianjin University</span>
            <span className="tju-badge muted-badge">TJU Student Research Project</span>
            <span className="tju-badge gold-badge">求是</span>
          </div>

          <div className="eyebrow"><ShieldCheck size={16} /> Kernel Track Analysis Platform</div>
          <h1>内核赛道作品智能分析与历史对比平台</h1>
          <p className="hero-desc">
            面向操作系统比赛内核赛道，本平台将往届作品构建为历史知识库，对本届新作品进行源码结构解析、相似项目检索、Hybrid 历史对比和五维评分，并自动生成可视化分析报告。
          </p>

          <div className="search-box glass">
            <input
              value={repoInput}
              onChange={(e) => setRepoInput(e.target.value)}
              placeholder="输入本届作品 Git 仓库地址，例如 https://github.com/team/kernel.git"
              onKeyDown={(e) => e.key === 'Enter' && submit()}
            />
            <button onClick={submit}>查询预计算结果 <ArrowRight size={16} /></button>
          </div>
          {error && <div className="notice warn">{error}</div>}

          <p className="tju-platform-note">
            当前平台采用“离线分析引擎 + 前端交互展示”架构。Python Agent 负责完成仓库分析、历史对比与五维评分，网站负责读取预计算结果并进行可视化展示。
          </p>

          <div className="system-overview glass">
            <div><span>分析对象</span><b>操作系统比赛内核赛道作品</b></div>
            <div><span>核心能力</span><b>源码画像 / 历史检索 / Hybrid 对比 / 五维评分</b></div>
            <div><span>展示方式</span><b>静态数据驱动的前端 Dashboard</b></div>
          </div>

          <div className="hero-actions">
            <Link className="secondary-btn" to="/works">查看本届作品</Link>
            <Link className="secondary-btn" to="/history">浏览历史库</Link>
          </div>
        </div>

        <div className="pipeline glass">
          <div className="panel-title"><Brain size={18} /> 分析流程</div>
          <div className="pipeline-subtitle">从历史知识库到评估报告的离线证据链</div>
          {flow.map((item, idx) => <div className="flow-item" key={item}><span>{idx + 1}</span><b>{item}</b></div>)}
        </div>
      </section>

      <section className="stats-grid">
        <StatCard label="历史作品数" value={stats.history_count} hint="往届样本库规模" />
        <StatCard label="本届作品数" value={stats.analyzed_works ?? stats.target_work_count} hint="已导出分析结果" />
        <StatCard label="平均评分" value={stats.average_score} hint="五维综合均值" />
        <StatCard label="核心模块数" value={stats.core_module_count} hint="OS 模块覆盖" />
      </section>

      <section className="section-head">
        <div><h2>平台能力</h2><p>围绕源码结构、历史相似性与评分证据构建稳定的展示链路。</p></div>
      </section>
      <div className="feature-grid">
        <div className="feature glass"><Database /><h3>历史知识库</h3><p>将往届内核作品转化为可检索画像，支撑相似项目检索和创新性判断。</p></div>
        <div className="feature glass"><Layers /><h3>结构化画像</h3><p>展示函数数量、调用边、模块归属、复杂度和核心模块覆盖等指标。</p></div>
        <div className="feature glass"><GitCompare /><h3>Hybrid 对比</h3><p>融合结构相似分与语义相似分，形成可解释的历史对比结果。</p></div>
        <div className="feature glass"><BarChart3 /><h3>五维评分</h3><p>从原创性、新颖性、可实践性、技术难度和完成度五个维度呈现评估结果。</p></div>
      </div>

      <section className="section-head">
        <div><h2>本届作品概览</h2><p>按综合评分展示已完成预计算分析的新作品。</p></div>
        <Link to="/works">全部作品 <ArrowRight size={15} /></Link>
      </section>
      <div className="list-stack">
        {recent.length ? recent.map((item) => <WorkCard key={item.repo_name} item={item} />) : <EmptyState />}
      </div>
    </div>
  )
}
