const items = [
  ['Tree-sitter 多语言源码解析', '对 C/C++/Rust/Python 等代码进行结构化解析，提取函数、结构和关键代码块。'],
  ['函数级代码切块', '把大型仓库拆分为可分析的函数级单元，支撑后续语义理解和调用关系提取。'],
  ['AI 函数语义理解', '调用大模型生成函数用途、模块归属、复杂度和调用关系等结构化信息。'],
  ['调用图与模块画像', '融合规则和 AI 输出，形成函数调用图和 OS 模块级画像。'],
  ['历史知识库构建', '将往届作品的 repo profile 入库，形成可检索的历史样本集合。'],
  ['RAG 语义检索', '将历史项目转化为 RAG 文档，检索技术路线和模块功能相似的项目。'],
  ['Hybrid 融合检索', '融合结构相似度和语义相似度，获得更稳的相似历史项目排序。'],
  ['五维评分与报告生成', '结合结构、历史对比和完成度证据，输出评分和 Markdown 报告。'],
]
export default function Method() {
  return <div className="container">
    <div className="page-title"><span>Methodology</span><h1>系统技术路线</h1><p>从源码解析、历史检索到评分报告生成的完整链路。</p></div>
    <div className="method-timeline">{items.map(([title, desc], i) => <div className="glass method-item" key={title}><span>{i+1}</span><div><h2>{title}</h2><p>{desc}</p></div></div>)}</div>
  </div>
}
