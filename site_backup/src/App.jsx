import { HashRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Home from './pages/Home.jsx'
import Works from './pages/Works.jsx'
import History from './pages/History.jsx'
import Search from './pages/Search.jsx'
import Analyze from './pages/Analyze.jsx'
import WorkDetail from './pages/WorkDetail.jsx'
import HistoryDetail from './pages/HistoryDetail.jsx'
import Compare from './pages/Compare.jsx'
import Scoring from './pages/Scoring.jsx'
import Method from './pages/Method.jsx'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/works" element={<Works />} />
          <Route path="/history" element={<History />} />
          <Route path="/search" element={<Search />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/works/:repoName" element={<WorkDetail />} />
          <Route path="/history/:repoName" element={<HistoryDetail />} />
          <Route path="/compare/:repoName" element={<Compare />} />
          <Route path="/scoring" element={<Scoring />} />
          <Route path="/method" element={<Method />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}
