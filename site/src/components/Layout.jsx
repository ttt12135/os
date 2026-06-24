import { Link, NavLink, Outlet } from 'react-router-dom'
import { Cpu, Database, Search, BarChart3, FileCode2 } from 'lucide-react'

const links = [
  ['/', '首页'],
  ['/history', '历史库'],
  ['/works', '本届作品'],
  ['/search', '仓库查询'],
  ['/scoring', '评分逻辑'],
  ['/method', '技术方法'],
]

export default function Layout() {
  return (
    <div className="app-shell">
      <div className="bg-orb orb-a" />
      <div className="bg-orb orb-b" />
      <header className="topbar">
        <Link className="brand" to="/">
          <span className="brand-icon"><Cpu size={22} /></span>
          <span>
            <b>KernelInsight Agent</b>
            <small>OS Kernel Track Analysis Platform</small>
          </span>
        </Link>
        <nav className="nav-links">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="page-main"><Outlet /></main>
      <footer className="footer">
        <span><Database size={15} /> 离线分析结果 + 前端动态展示</span>
        <span><Search size={15} /> 仓库地址匹配</span>
        <span><BarChart3 size={15} /> 五维评分</span>
        <span><FileCode2 size={15} /> Markdown 报告</span>
      </footer>
    </div>
  )
}
