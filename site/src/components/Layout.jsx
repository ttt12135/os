import { Link, NavLink, Outlet } from 'react-router-dom'
import { BarChart3, Database, FileCode2, Search } from 'lucide-react'

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
      <header className="topbar">
        <Link className="brand" to="/">
          <span className="brand-icon tju-brand-icon">
            <span className="tju-logo-text">TJU</span>
          </span>
          <span>
            <b>KernelInsight Agent</b>
            <small>天津大学 · OS Kernel Track Analysis</small>
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
        <span><Database size={15} /> 离线分析引擎</span>
        <span><Search size={15} /> 预计算结果查询</span>
        <span><BarChart3 size={15} /> 五维评分证据链</span>
        <span><FileCode2 size={15} /> 静态报告展示</span>
      </footer>
    </div>
  )
}
