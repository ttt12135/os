import os

def ensure_dir(dir_path):
    """
    如果目录不存在，就自动创建目录
    用makedirs可以把分级目录完整得创建出来
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_repo_name(repo_path):
    """
    从仓库路径中提取仓库名字。
    """

    repo_path = os.path.normpath(repo_path)
    return os.path.basename(repo_path)


def save_markdown_report(repo_path,report_content,report_type="description"):
    """
    把AI输出的想法整理成文件

    参数分析：
    repo_path：被分析的仓库路径
    repo_content：AI生成的报告
    report_type：报告类型，默认为描述类报告
    """

    reports_dir = "reports"
    ensure_dir(reports_dir)

    repo_name = get_repo_name(repo_path)

    file_name = f"{repo_name}_{report_type}.md"
    file_path = os.path.join(reports_dir,file_name)

    with open(file_path,"w",encoding="utf-8") as file:
        file.write(report_content)

    return file_path


def save_comparison_report(target_repo_path, report_content):
    """
    保存新作品和历史作品的对比报告
    """

    reports_dir = "reports"
    ensure_dir(reports_dir)

    repo_name = get_repo_name(target_repo_path)

    file_name = f"{repo_name}_comparison.md"

    file_path = os.path.join(reports_dir,file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(report_content)

    return file_path
