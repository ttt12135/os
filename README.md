# KernelInsight

KernelInsight 是一个面向操作系统内核赛道作品的仓库智能分析与历史对比系统。

系统可以自动导入 Git 仓库，分析仓库源码结构，理解关键代码模块，建立历史作品库，并对目标仓库生成评分、排名和 Markdown 分析报告。

本项目主要用于辅助理解 OS 内核赛道作品，帮助开发者和评审者快速了解一个仓库的结构、实现情况、历史相似项目、优势短板和综合评分。

！！！！！

当前只提交了后端算法部分，前端单独维护，请勿轻易使用前端相关命令

！！！！！

---

## 1. 项目能做什么

KernelInsight 主要完成以下工作：

1. 自动导入 Git 仓库；
2. 区分历史仓库 `history` 和目标仓库 `target`；
3. 扫描仓库目录结构，识别源码、文档、构建脚本和关键模块；
4. 对源码进行代码块切片，并过滤第三方依赖、生成文件和低价值代码块；
5. 对关键代码块进行 AI 辅助理解，提取函数作用、模块职责和实现强度；
6. 构建仓库画像，包括语言、模块、函数、调用关系和工程证据；
7. 建立历史作品知识库，用于目标仓库的相似项目检索；
8. 对目标仓库和历史仓库进行横向对比；
9. 从原创性、新颖性、可实践性、技术难度、完成度五个维度进行评分；
10. 自动生成 Markdown 分析报告；
11. 生成仓库质量排名；
12. 导出前端展示所需的 JSON 数据和 Markdown 报告。

---

## 2. 系统整体流程

```text
Git 仓库地址
    ↓
仓库克隆与元信息记录
    ↓
源码结构扫描
    ↓
代码块切片与过滤
    ↓
AI 辅助代码理解
    ↓
仓库画像生成
    ↓
历史项目知识库构建
    ↓
相似历史项目检索
    ↓
目标仓库对比分析
    ↓
五维评分
    ↓
Markdown 报告生成
    ↓
前端展示数据导出
```

---

## 3. 项目结构

```text
KernelInsight/
├── main.py                      # 命令行入口
├── src/                         # 核心功能模块
│   ├── repo_url_workflow.py      # Git 仓库导入流程
│   ├── simple_import_ui.py       # 简化命令行导入界面
│   ├── ingest_pipeline.py        # history / target 入库流程
│   ├── code_splitter.py          # 代码切片与过滤
│   ├── code_understander.py      # AI 辅助代码块理解
│   ├── history_retriever.py      # 历史项目检索
│   ├── final_pipeline.py         # 目标仓库完整分析流程
│   ├── repo_quality_ranker.py    # 仓库质量排名
│   └── ...
├── site_config/                 # 前端展示配置
│   └── works_manifest.json
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
└── README.md
```

---

## 4. 安装与环境配置

### 4.1 安装依赖

进入项目目录：

```bash
cd KernelInsight
```

安装依赖：

```bash
pip install -r requirements.txt
```

### 4.2 配置 API Key

复制 .example.env 为 `.env`：

```bash
copy .example.env .env
```

在 `.env` 中填写：

```env
DEEPSEEK_API_KEY=your_api_key_here
```

说明：`.env` 文件只用于本地运行，不应提交到公开仓库。

---

## 5. 命令行使用说明

启动系统：

```bash
python main.py
```

启动后会进入命令行菜单：

```text
1. 导入 Git 仓库并分析
2. 导出网站数据
3. 生成仓库质量排名
4. 查看推荐流程

h. 查看高级命令
q. 退出程序
```

---

### 5.1 导入 Git 仓库并分析

命令编号：

```text
1
```

该命令是系统最核心的入口，用于输入一个 Git 仓库地址，并自动完成仓库克隆、源码分析、代码理解、仓库画像、评分和报告生成等流程。

适用场景：

- 将往届作品加入历史库；
- 分析本届目标仓库；
- 生成目标仓库的描述报告、评分结果和最终报告；
- 为前端展示准备基础数据。

运行后需要输入的信息包括：

```text
Git 仓库地址
仓库类型：history / target
仓库简称
队伍名
学校名
年份
分析强度
```

仓库类型说明：

| 类型 | 含义 |
|---|---|
| `history` | 历史仓库，用于建立历史作品库和对比基准 |
| `target` | 目标仓库，用于生成评分、对比结果和最终报告 |

分析强度说明：

| 模式 | 用途 | 特点 |
|---|---|---|
| 快速测试 | 检查仓库能否正常导入 | 只分析少量代码块，速度快 |
| 正式入库 | 正式加入历史库或分析目标仓库 | 全仓扫描，动态选择高优先级代码块 |
| 深度最终 | 最终展示前使用 | 尽可能进行全量代码理解，耗时较长 |

---

### 5.2 history 仓库会生成什么

如果导入的是 `history` 仓库，系统主要生成以下文件：

| 路径 | 作用 |
|---|---|
| `external_repos/history/{repo_name}/` | 克隆到本地的历史仓库源码 |
| `repo_sources/history/{repo_name}_source.json` | 仓库来源信息，包括原始 Git 地址、学校、队伍、年份等 |
| `code_blocks/{repo_name}_blocks.json` | 仓库源码切片后的代码块数据 |
| `function_analysis/{repo_name}_function_analysis.json` | AI 对代码块的理解结果 |
| `repo_profiles/history/{repo_name}_repo_profile_full.json` | 历史仓库画像 |
| `history_knowledge_base/history_profiles_full.json` | 汇总后的历史作品知识库 |

说明：

```text
history 仓库主要用于建立历史作品库和对比基准。
为了提高批量入库速度，history 仓库默认不生成详细 description_report。
```

---

### 5.3 target 仓库会生成什么

如果导入的是 `target` 仓库，系统主要生成以下文件：

| 路径 | 作用 |
|---|---|
| `external_repos/target/{repo_name}/` | 克隆到本地的目标仓库源码 |
| `repo_sources/target/{repo_name}_source.json` | 目标仓库来源信息 |
| `code_blocks/{repo_name}_blocks.json` | 目标仓库代码块数据 |
| `function_analysis/{repo_name}_function_analysis.json` | 目标仓库代码理解结果 |
| `repo_profiles/target/{repo_name}_repo_profile_full.json` | 目标仓库画像 |
| `reports/{repo_name}_description.md` | 目标仓库详细描述报告 |
| `evaluation/{repo_name}_score_full.json` | 五维评分结果 |
| `reports/{repo_name}_final_report.md` | 最终综合分析报告 |
| `repository_quality/target_repository_quality_ranking.md` | 目标仓库质量排名报告 |

说明：

```text
target 仓库会生成更详细的 description_report 和 final_report，
用于前端展示、项目答辩和最终结果说明。
```

---

### 5.4 导出网站数据

命令编号：

```text
2
```

该命令用于将分析结果整理成前端展示所需的数据文件。

前端不会直接运行 Python 分析逻辑，也不会直接调用 AI，只读取该命令导出的 JSON 和 Markdown 文件。

主要作用：

1. 汇总仓库列表；
2. 汇总历史库信息；
3. 汇总目标仓库评分结果；
4. 复制最终分析报告；
5. 生成前端可以读取的数据目录。

常见生成文件：

| 路径 | 作用 |
|---|---|
| `public/data/site_stats.json` | 网站首页统计数据 |
| `public/data/works_summary.json` | 目标仓库摘要列表 |
| `public/data/history_summary.json` | 历史仓库摘要列表 |
| `public/data/works/{repo_name}.json` | 单个目标仓库详情数据 |
| `public/data/history/{repo_name}.json` | 单个历史仓库详情数据 |
| `public/data/comparisons/{repo_name}.json` | 目标仓库与历史仓库对比数据 |
| `public/reports/{repo_name}_final_report.md` | 前端展示用 Markdown 报告 |

如果前端项目独立维护，需要将导出路径设置为前端项目的 `public` 目录。

例如：

```text
D:\os\kernelinsight-web\public
```

---

### 5.5 生成仓库质量排名

命令编号：

```text
3
```

该命令用于根据已经生成的评分结果，对 history 或 target 仓库进行排序，生成仓库质量排行榜。

排名使用的主分数与最终分析报告中的综合评分保持一致。

主要作用：

1. 读取 `evaluation/{repo_name}_score_full.json` 中的综合评分；
2. 汇总仓库优势、短板和证据；
3. 按综合评分进行排序；
4. 生成 Markdown 和 JSON 两种排名结果。

生成文件：

| 路径 | 作用 |
|---|---|
| `repository_quality/history_repository_quality_ranking.md` | 历史仓库质量排名报告 |
| `repository_quality/history_repository_quality_ranking.json` | 历史仓库排名结构化数据 |
| `repository_quality/target_repository_quality_ranking.md` | 目标仓库质量排名报告 |
| `repository_quality/target_repository_quality_ranking.json` | 目标仓库排名结构化数据 |

排名报告中会展示：

- 排名；
- 仓库名；
- 学校和队伍；
- 原始 Git 地址；
- 综合评分；
- 等级；
- 主要优势；
- 主要不足；
- 分析报告入口。

---

### 5.6 查看推荐流程

命令编号：

```text
4
```

该命令用于查看系统推荐的标准使用流程。

推荐流程一般为：

```text
1. 导入多个 history 仓库，建立历史作品库
2. 导入 target 仓库，生成目标仓库画像
3. 对 target 仓库执行历史对比与评分
4. 生成仓库质量排名
5. 导出前端展示数据
6. 在前端页面查看仓库详情、排名和报告
```

该命令不会生成新的分析文件，主要用于帮助用户理解系统使用顺序。

---

## 6. 高级命令说明

除主菜单外，系统还保留了一些高级命令，用于调试或单独运行某个分析阶段。

| 命令 | 作用 |
|---|---|
| `import_repo_url` | 输入 Git 地址，导入仓库并自动分析 |
| `ingest_history` | 单独导入历史仓库并生成历史仓库画像 |
| `batch_ingest_history` | 批量导入历史仓库 |
| `analyze_target` | 单独分析目标仓库 |
| `final_analyze_hybrid` | 对目标仓库执行完整分析、检索、对比、评分和报告生成 |
| `rank_repo_quality` | 生成仓库质量排名 |
| `export_site_data` | 导出前端展示数据 |
| `build_rag_docs` | 构建 RAG 检索文档 |
| `build_vector_store` | 构建向量检索库 |
| `hybrid_retrieve` | 执行混合检索，寻找相似历史项目 |
| `compare_full` | 生成目标仓库与历史仓库的详细对比 |
| `score_full` | 生成五维评分结果 |
| `final_report` | 根据已有分析结果生成最终报告 |

一般用户建议使用主菜单，不建议直接运行高级命令，除非需要调试某个具体阶段。

---

## 7. 输出文件与目录说明

| 目录 / 文件 | 作用 |
|---|---|
| `external_repos/` | 保存克隆到本地的 history 和 target 仓库源码 |
| `repo_sources/` | 保存仓库来源信息，如 Git 地址、学校、队伍、年份 |
| `code_blocks/` | 保存代码切片结果 |
| `function_analysis/` | 保存 AI 对代码块和函数的理解结果 |
| `call_graph/` | 保存函数调用关系图数据 |
| `module_summary/` | 保存模块级总结结果 |
| `repo_profiles/` | 保存仓库画像，包括结构、语言、模块和统计信息 |
| `history_knowledge_base/` | 保存历史仓库知识库，用于相似项目检索 |
| `evaluation/` | 保存五维评分结果 |
| `repository_quality/` | 保存仓库质量排名结果 |
| `reports/` | 保存 Markdown 分析报告 |
| `site_config/` | 保存前端展示相关配置，如仓库清单 |

---

### 7.1 关键文件说明

| 文件 | 说明 |
|---|---|
| `{repo_name}_source.json` | 记录仓库原始地址、学校、队伍、年份等元信息 |
| `{repo_name}_blocks.json` | 记录从源码中切分出的代码块 |
| `{repo_name}_function_analysis.json` | 记录 AI 对代码块的分析结果 |
| `{repo_name}_repo_profile_full.json` | 仓库结构画像 |
| `{repo_name}_score_full.json` | 五维评分结果 |
| `{repo_name}_description.md` | 仓库详细描述报告，主要用于 target |
| `{repo_name}_final_report.md` | 最终综合分析报告 |
| `history_repository_quality_ranking.md` | 历史仓库质量排名 |
| `target_repository_quality_ranking.md` | 目标仓库质量排名 |
| `works_manifest.json` | 前端展示使用的仓库元信息清单 |

---

## 8. 前端展示说明

WARING!!!!!!!!!!

比赛只提交了后端算法部分，前端单独维护，最终的展示地址将于初赛截止后再提交。



---

## 9. 评分与排名说明

系统主要从以下五个维度进行综合评价：

| 维度 | 含义 |
|---|---|
| 原创性 | 判断项目是否与历史作品高度重复，是否具有独立设计成分 |
| 新颖性 | 判断模块组合、技术路线和实现方式是否具有差异化 |
| 可实践性 | 判断项目是否具备构建、运行、测试和工程落地基础 |
| 技术难度 | 判断内核模块复杂度、调用关系和系统机制实现深度 |
| 完成度 | 判断核心链路是否闭环，是否存在大量 TODO 或空实现 |

最终评分并非仅由代码行数、函数数量或结构复杂度决定，而是综合考虑：

- 源码结构；
- 核心模块实现证据；
- 历史项目相似度；
- 工程完整性；
- 代码理解结果；
- 报告与评分输出。

系统最终展示的主评分来自：

```text
evaluation/{repo_name}_score_full.json
```

该分数会同步用于：

```text
reports/{repo_name}_final_report.md
repository_quality/{scope}_repository_quality_ranking.md
前端展示页面
```

因此，最终报告、质量排名和前端页面使用同一评分口径。

其他实现质量分、结构复杂度分、证据完整度等指标只作为辅助分析依据，不作为排行榜主分数。
