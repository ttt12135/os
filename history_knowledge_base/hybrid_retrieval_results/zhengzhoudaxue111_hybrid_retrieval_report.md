# Hybrid 历史项目检索报告

生成时间：2026-06-23 16:09:54
目标仓库：`zhengzhoudaxue111`

## 1. 检索配置

- 结构检索结果：`history_knowledge_base\retrieval_results\zhengzhoudaxue111_similar_projects_full.json`
- RAG Query：查找与目标 OS 项目 zhengzhoudaxue111 相似的历史项目。目标项目类型是 filesystem_focused_project，主要语言包括 rust，核心模块包括 syscall、filesystem、build、user。该项目包含 20 个函数节点、415 条调用边、4 个模块，结构复杂度为 0.45。请优先检索在项目类型、核心模块、系统结构、技术特征和工程复杂度上相似的历史 OS 项目。
- structured_weight：`0.65`
- semantic_weight：`0.35`
- top_k：`5`

## 2. 融合检索结果

| 排名 | 仓库名 | Hybrid分数 | 结构分数 | 语义分数 | 来源 |
|---:|---|---:|---:|---:|---|
| 1 | nankai | 0.6316 | 0.4871 | 0.9 | structured、rag |
| 2 | tianjingongye | 0.6005 | 0.4931 | 0.8 | structured、rag |
| 3 | qinghuadaxue | 0.4818 | 0.5258 | 0.4 | structured、rag |
| 4 | zhengzhoudaxue111 | 0.35 | 0.0 | 1.0 | rag |
| 5 | yanshandaxue | 0.245 | 0.0 | 0.7 | rag |

## 3. RAG 语义证据

### 1. nankai

- Hybrid 分数：`0.6316`
- 结构分数：`0.4871`
- 语义分数：`0.9`
- 来源：`structured、rag`

- `repo_overview` / `nankai__repo_overview`：历史项目 nankai 是一个 unknown_os_project 类型的 OS 项目。该项目主要语言包括 rust。系统识别到该项目包含 20 个函数节点、107 条调用边、4 个模块。核心模块包括 syscall、process、process/syscall、interrupt。结构复杂度为 0.38。

### 2. tianjingongye

- Hybrid 分数：`0.6005`
- 结构分数：`0.4931`
- 语义分数：`0.8`
- 来源：`structured、rag`

- `repo_overview` / `tianjingongye__repo_overview`：历史项目 tianjingongye 是一个 unknown_os_project 类型的 OS 项目。该项目主要语言包括 rust。系统识别到该项目包含 20 个函数节点、116 条调用边、7 个模块。核心模块包括 boot、filesystem、interrupt、memory、unknown。结构复杂度为 0.43。

### 3. qinghuadaxue

- Hybrid 分数：`0.4818`
- 结构分数：`0.5258`
- 语义分数：`0.4`
- 来源：`structured、rag`

- `repo_overview` / `qinghuadaxue__repo_overview`：历史项目 qinghuadaxue 是一个 unknown_os_project 类型的 OS 项目。该项目主要语言包括 rust。系统识别到该项目包含 20 个函数节点、119 条调用边、5 个模块。核心模块包括 boot、filesystem、process、memory、scheduler。结构复杂度为 0.43。

### 4. zhengzhoudaxue111

- Hybrid 分数：`0.35`
- 结构分数：`0.0`
- 语义分数：`1.0`
- 来源：`rag`

- `repo_overview` / `zhengzhoudaxue111__repo_overview`：历史项目 zhengzhoudaxue111 是一个 filesystem_focused_project 类型的 OS 项目。该项目主要语言包括 rust。系统识别到该项目包含 20 个函数节点、415 条调用边、4 个模块。核心模块包括 syscall、filesystem、build、user。结构复杂度为 0.45。

### 5. yanshandaxue

- Hybrid 分数：`0.245`
- 结构分数：`0.0`
- 语义分数：`0.7`
- 来源：`rag`

- `repo_overview` / `yanshandaxue__repo_overview`：历史项目 yanshandaxue 是一个 unknown_os_project 类型的 OS 项目。该项目主要语言包括 rust。系统识别到该项目包含 20 个函数节点、92 条调用边、5 个模块。核心模块包括 boot、memory、process、unknown、scheduler。结构复杂度为 0.43。

## 4. 说明

Hybrid 检索结果同时考虑结构相似度和 RAG 语义相似度。其中结构相似度主要来自 retrieve_full，关注项目类型、模块结构、函数规模和调用图规模；语义相似度主要来自 RAG 文档向量检索，关注技术描述、模块特征和文本语义。
