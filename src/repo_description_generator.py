from src.repo_reader import build_file_tree
from src.file_reader import collect_important_files, format_files_content, format_file_scores
from src.report_writer import save_markdown_report


def generate_repo_description_report(repo_path, ask_ai_once):
    """
    生成旧版“人类友好的仓库描述报告”。

    这个报告比 final_report 里的结构化摘要更适合解释：
    1. 这个仓库是什么；
    2. 主要目录和文件是干什么的；
    3. 可能有哪些 OS 核心模块；
    4. 程序大致怎么运行；
    5. 当前优势和不足是什么。
    """

    file_tree = build_file_tree(repo_path)

    important_files = collect_important_files(repo_path)
    file_scores = format_file_scores(important_files)
    file_content = format_files_content(important_files)

    prompt = f"""
你现在要为一个操作系统比赛作品生成一份“人类友好的仓库描述报告”。

下面是该仓库的信息。

一、仓库文件结构树：
{file_tree}

二、文件重要性评分结果：
{file_scores}

三、高评分关键文件内容：
{file_content}

请你生成一份 Markdown 格式的仓库描述报告。

报告标题为：
# OS 仓库描述报告

报告必须包含以下部分：

## 一、项目基本信息

说明这个项目是什么类型的项目。
需要尽量判断：
- 项目名称
- 主要编程语言
- 可能运行的平台或架构
- 它是教学型 OS、比赛型 OS、微型内核、文件系统项目、驱动项目，还是其他类型
如果无法确定，请明确说明“当前证据不足”。

## 二、仓库结构概览

根据仓库文件树解释主要目录和文件的作用。
不要只列目录，要说明它们可能承担的职责。

## 三、关键性文件分析

结合文件重要性评分，解释高分文件为什么重要。
重点说明这些文件是否涉及：
- 启动入口
- 内核初始化
- 内存管理
- 任务/进程管理
- 中断/异常处理
- 系统调用
- 文件系统
- 驱动
- 构建运行

## 四、核心模块推测

从以下角度分析仓库可能包含哪些 OS 模块：

1. 启动模块
2. 内核初始化模块
3. 内存管理模块
4. 进程或任务管理模块
5. 中断或异常处理模块
6. 系统调用模块
7. 文件系统或驱动模块
8. 构建与运行模块

如果某些模块没有明显体现，请明确说明“当前仓库中未发现明显证据”。

## 五、程序运行流程推测

根据当前代码内容，推测项目的大致运行流程。
比如：
启动入口 → 初始化内存 → 初始化中断 → 初始化任务 → 进入调度 → 处理系统调用。
只能基于已有文件和代码合理推测，不要过度编造。

## 六、项目特点总结

总结这个 OS 作品的特点、可能优势和当前完成度。
要具体，不要只写“具有一定复杂度”。

## 七、当前不足与不确定信息

说明当前分析可能存在的不确定性。
例如：
- 未运行项目
- 只读取了部分关键文件
- 某些模块只有文件名证据，没有实现细节证据
- 缺少 README 或构建说明

## 八、后续比较建议

说明如果要和历史 OS 作品比较，后续应该重点比较哪些维度。


## 九、前端展示摘要

请额外给出一个适合前端展示的摘要区，包含：
- 一句话项目定位
- 3 个核心特点
- 3 个主要风险或不足
- 推荐在前端展示的关键词标签

## 十、评审视角结论

从评审视角给出简短结论：
- 这个项目最值得关注的地方是什么；
- 当前证据最薄弱的地方是什么；
- 后续如果继续深入分析，应该优先看哪些文件或模块。

输出要求：
1. 面向评审和初学者，语言清楚；
2. 不要写成普通聊天，要写成正式报告；
3. 不要编造没有代码依据的内容；
4. 遇到不确定内容要明确标注；
5. 输出必须是完整 Markdown 文档；
6. 内容要比普通摘要更详细，适合 target 仓库最终报告和前端 Repository Detail 页面展示；
7. 不要写空泛套话，必须围绕仓库结构、关键文件和可见代码证据展开。
"""

    report_content = ask_ai_once(prompt)

    report_path = save_markdown_report(
        repo_path=repo_path,
        report_content=report_content,
        report_type="description"
    )

    return report_path, report_content