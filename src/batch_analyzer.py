import os


def find_repos_in_folder(folder_path):
    """
    在指定文件夹下查找多个历史仓库。

    规则：
    只扫描folder_path下面的第一个子文件夹。
    每个子文件夹都当作一个待分析的仓库。

    """

    if not os.path.exists(folder_path):
        return []

    if not os.path.isdir(folder_path):
        return []

    repos = []

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        if os.path.isdir(item_path):
            repos.append(item_path)
    
    #按照字母表顺序排序，保证输出一致性
    repos.sort()

    return repos



def format_batch_summary(results):
    """
    把批量的分析结果弄成字符串格式
    方便展示在终端
    """

    if len(results) == 0:
        return "没有生成正确的历史作品描述报告，请检查历史文件夹路径是否正确！！！"

    output = []

    output.append("批量分析完成，生成的报告如下：")
    output.append("")

    for index, item in enumerate(results, start=1):
        output.append(f"{index}. 仓库名称：{item['repo_name']}")
        output.append(f"   仓库路径：{item['repo_path']}")
        output.append(f"   报告路径：{item['report_path']}")
        output.append("")

    return "\n".join(output)