const items = [
  ['Tree-sitter 多语言源码解析', '对 C、C++、Rust、Python 等源码进行结构化解析，提取函数、文件和语法结构信息。'],
  ['函数级代码切块', '将大型仓库拆分为可分析的函数级单元，为语义理解和调用关系抽取提供稳定输入。'],
  ['AI 函数语义理解', '对函数用途、关联 OS 模块、复杂度和潜在调用关系进行结构化理解。'],
  ['调用图构建', '融合静态规则与语义结果，形成函数节点、调用边和内部 / 外部调用统计。'],
  ['模块画像生成', '按 boot、memory、process、filesystem、syscall 等 OS 模块汇总函数、权重和完成度。'],
  ['历史知识库构建', '将往届作品的 repo profile 入库，形成用于检索、对比和创新性判断的历史样本库。'],
  ['RAG 语义检索', '把历史项目画像转化为检索文档，从技术路线和模块语义层面寻找相似项目。'],
  ['Hybrid 结构 + 语义融合检索', '融合结构相似分和语义相似分，得到更稳健的相似历史作品 Top-K。'],
  ['AI 历史对比', '围绕相似点、差异点、目标项目优势、不足和可借鉴设计生成对比说明。'],
  ['五维评分与报告生成', '结合结构画像、历史对比和模块完成度证据，输出五维评分与 Markdown 分析报告。'],
]

export default function Method() {
  return <div className="container">
    <div className="page-title">
      <span>Methodology</span>
      <h1>技术方法说明</h1>
      <p>平台采用离线分析引擎生成结构化结果，前端只负责读取静态 JSON 和 Markdown 并完成交互展示。</p>
    </div>
    <div className="method-timeline">
      {items.map(([title, desc], i) => <div className="glass method-item" key={title}><span>{i + 1}</span><div><h2>{title}</h2><p>{desc}</p></div></div>)}
    </div>
  </div>
}
