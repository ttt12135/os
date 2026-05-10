import os


def read_markdown_file(file_path, max_chars=5000):
    """
    读取markdown文件，之前的的分析报告
    max_chars用于限制单个报告的长度，防止内容过长
    """

    try:
        with open(file_path,"r",encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        return ""
    except PermissionError:
        return ""

    if len(content)>max_chars:
        content = content[:max_chars]+"\n\n......报告内容过长，后面部分省略......"

    return content


def find_history_description_reports(reports_dir, exclude_report_path=None):
    """
    在reports目录中查找历史作品描述报告。

    只读以_description.md结尾的报告文件；
    排除当前新作品自己的描述报告。
    """

    if not os.path.exists(reports_dir):
        return []

    if not os.path.isdir(reports_dir):
        return []

    history_reports = []

    exclude_abs_path = None

    if exclude_report_path is not None:
        exclude_abs_path = os.path.abspath(exclude_report_path)

    for file_name in os.listdir(reports_dir):
        #这是选择出后缀是"_description.md"格式的文件
        if not file_name.endswith("_description.md"):
            continue

        file_path = os.path.join(reports_dir, file_name)
        file_abs_path = os.path.abspath(file_path)

        if exclude_abs_path is not None and file_abs_path == exclude_abs_path:
            continue

        history_reports.append(file_path)

    history_reports.sort()

    return history_reports


def format_history_reports(report_paths, max_reports=5):
    """
    把多个历史作品描述报告整理成字符串，方便写进Prompt
    """

    if len(report_paths) == 0:
        return "当前没有找到历史作品报告"

    selected_reports = report_paths[:max_reports]

    output = []

    for index, report_path in enumerate(selected_reports, start = 1):
        report_name = os.path.basename(report_path)
        content = read_markdown_file(report_path)

        output.append(f"历史作品报告{index}:{report_name}")
        output.append("")
        output.append(content)
        output.append("")
        output.append("-"*80)

    if len(report_paths) > max_reports:
        output.append(f"注意！！！：历史报告数量较多，本次仅读取前{max_reports}份报告")

    return "\n".join(output)

