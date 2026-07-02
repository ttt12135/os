const pipeline = ['Repository Import', 'Static Code Parsing', 'Code Block Extraction', 'AI-assisted Understanding', 'Repository Profile', 'History Retrieval', 'Comparison', 'Scoring', 'Markdown Report', 'Frontend Export'];
const updateFlow = ['Analyze Target Repos', 'Generate Target Ranking', 'Export Site Data', 'Replace public/data and public/reports', 'Build Frontend', 'Deploy Website'];

export function Method() {
  return (
    <div className="page-stack">
      <section className="page-title"><p className="eyebrow">Method</p><h1>技术路线</h1><p>Python 系统负责离线分析，前端只读取 JSON 与 Markdown 静态产物。</p></section>
      <section className="section-block"><h2>System Pipeline</h2><div className="method-flow">{pipeline.map((item, index) => <div className="pipeline-step" key={item}><span>{index + 1}</span><strong>{item}</strong></div>)}</div></section>
      <section className="section-block"><h2>边界说明</h2><div className="evidence-grid"><div className="evidence-item"><span>Python 系统</span><strong>负责离线分析、检索、评分和报告生成</strong></div><div className="evidence-item"><span>前端</span><strong>只读取 JSON 和 Markdown</strong></div><div className="evidence-item"><span>运行时</span><strong>不运行 Python、不调用 AI、不依赖后端</strong></div><div className="evidence-item"><span>部署</span><strong>Vercel / GitHub Pages / 静态服务器均可</strong></div></div></section>
      <section className="section-block"><h2>Data Update / 数据更新说明</h2><div className="method-flow">{updateFlow.map((item, index) => <div className="pipeline-step" key={item}><span>{index + 1}</span><strong>{item}</strong></div>)}</div><p className="readable-text">前端不需要也不能直接更新线上数据。只要 site/public/data 和 site/public/reports 被替换成新数据，重新构建并部署后，刷新页面即可展示最新内容。</p></section>
    </div>
  );
}
