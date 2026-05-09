from openai import OpenAI
from dotenv import load_dotenv
from src.repo_reader import build_file_tree
from src.file_reader import collect_important_files, format_files_content, format_file_scores
from src.report_writer import save_markdown_report
from src.batch_analyzer import find_repos_in_folder, format_batch_summary
import os

#读取.env文件
load_dotenv()

#读取.env中的DEEPSEEK_API_KEY
api_key = os.getenv("DEEPSEEK_API_KEY")

if api_key is None:
    print("api获取错误，检查.env文件")
    exit()

#创建deepseek客户端
client=OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

#创建保存对话记录的地点
messages = [
    {
        "role":"system",
        "content":"你是一个帮助新手理解代码仓库和操作系统比赛项目的AI助手,回答的时候要清楚简单"
    }
]

def chat_with_ai(user_input):
#函数用途：把用户的话发给DeepSeek

#加入对话历史
    messages.append(
        {
            "role":"user",
            "content":user_input
        }
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
#提取AI第一个回答
    ai_reply = response.choices[0].message.content
#把回答添加进对话信息
    messages.append(
        {
            "role":"assistant",
            "content":ai_reply
        }
    )
    return ai_reply

def analyze_repo(repo_path):
    #读取本地的repo文件和关键文件的内容（有一定的优先度）

    file_tree = build_file_tree(repo_path)

    important_files = collect_important_files(repo_path)
    file_scores = format_file_scores(important_files)
    files_content = format_files_content(important_files)

    #AI提示词模块，首次接触加深学习
    prompt = f"""
下面是一个代码仓库的文件结构：
一、仓库的文件结构
{file_tree}

二、文件重要性评分结果：

{file_scores}

三、高评分关键文件内容：

{files_content}


请你认真的解释这个代码仓库结构和文件内容，认真分析这个代码仓库。
要求如下：
1. 说明这个仓库当前已经实现了什么功能；
2. 解释主要文件分别负责什么；
3. 分析程序的大致运行流程；
4. 指出当前实现的不足；
5. 给出下一步适合迭代的方向；
6. 回答要适合初学者理解，不要写得太抽象。
"""
    ai_reply = chat_with_ai(prompt)

    return file_tree,file_scores, files_content, ai_reply
     

def generate_repo_description(repo_path):
    """
    函数用途是生成单个os仓库的描述文档
    """

    file_tree = build_file_tree(repo_path)

    important_files = collect_important_files(repo_path)
    file_scores = format_file_scores(important_files)
    file_content = format_files_content(important_files)

    prompt = f"""
你先在要为一个操作系统比赛作品生成一份“人类友好的描述文档”

下面是该仓库的信息。

一、仓库文件的结构树：
{file_tree}

二、文件重要性评分结果：
{file_scores}

三、高评分关键文件：
{file_content}

请你生成一份Markdown格式的仓库描述报告。

标题为：
#os仓库描述报告

报告需包含一下几个部分：

##一、项目基本信息

说明这个项目是什么类型的项目。
若无法确定项目名称、编程语言或运行平台，请如实说明

##二、仓库结构概览

根据仓库文件树解释主要目录和文件的作用

##三、关键性文件分析

结合文件重要性评分，解释高分文件为什么重要。

##四、核心模块推测

从以下角度分析仓库可能包含哪些模块：

1.启动模块
2.内核初始化模块
3.内存管理模块
4.进程或人物管理模块
5.中断或异常处理模块
6.系统调用模块
7.文件系统或驱动模块
8.构建与运行模块

如果某些模块没有明显体现，请明确说明“当前仓库中未发现明显证据”

##五、程序运行流程推测

根据当前代码内容，推测项目的大致运行流程。
可以合理进行推测，不要过度编造，只能基于已有文件和代码进行合理推测。

##六、项目特点总结

总结这个os作品的特点、可能优势和当前完成度。

##七、当前不足与不确定的信息

说明当前分析可能存在的不确定性。例如读取文件数量有限、未运行项目、未完整分析全部代码等。

##八、后续比较建议
说明如果要和历史os作品比较，后续应该重点比较哪些维度。

输出要求：
1.面向评审和初学者，语言清楚；
2.不要写成普通聊天，要写成正式报告；
3.不要编造没有代码依据的内容；
4.遇到不确定内容要明确标注；
5.输出必须是完整的 Markdown 文档。
    """


    report_content = chat_with_ai(prompt)

    report_path = save_markdown_report(
        repo_path=repo_path,
        report_content=report_content,
        report_type="description"
    )

    return report_path,report_content



def batch_generate_history_reports(history_folder_path):
    """
    可以直接批量分析os作品文件夹
    这是非常令人激动的一步
    因为这是真正可以贴合赛题第一个要求的第一步
    现在是5.10一点十五分，版本v0.7
    """

    repo_paths = find_repos_in_folder(history_folder_path)

    results = []

    if not len(repo_paths):
        return results

    for repo_path in repo_paths:
        repo_name = os.path.basename(os.path.normpath(repo_path))

        print()
        print(f"正在分析历史仓库：{repo_name}")
        print(f"仓库路径：{repo_path}")

        report_path,report_content = generate_repo_description(repo_path)

        results.append(
            {
            "repo_name":repo_name,
            "repo_path":repo_path,
            "report_path":report_path
            }
        )

    return results




def main():
    print("OS agent v0.7,接入deepseek,可生成文件报告")
    print("-"*30)

    while True:
        user_input = input("请选择模式(chat/repo/report/batch/exit):")

        if user_input == "exit":
            print("程序退出")
            break
        
        elif user_input == "chat":
            user_input=input("用户： ")
            ai_reply = chat_with_ai(user_input)

            print("AI: ")
            print(ai_reply)
            print("-"*30)

        elif user_input == "repo":
            repo_path = input("请输入本地仓库路径：")

            file_tree, file_scores, files_content, ai_reply = analyze_repo(repo_path)
            """
            print("\n仓库文件结构：")
            print(file_tree)
            """
            print("\n文件重要性评分:")
            print(file_scores)

            print("\n关键文件内容：")
            print(files_content)

            print("\nAI 分析: ")
            print(ai_reply)
            print("-"*30)    


        elif user_input == "report":
            repo_path = input("请输入本地仓库路径: ")

            report_path, report_content = generate_repo_description(repo_path)

            print("\n描述文档已生成:")
            print(report_path)

            print("\n报告内容预览:")
            print(report_content)
            print("-" * 30)

        elif user_input == "batch":
            history_folder_path = input("请输入历史作品总文件夹路径: ")

            results = batch_generate_history_reports(history_folder_path)
            summary = format_batch_summary(results)

            print("\n批量分析结果:")
            print(summary)
            print("-" * 30)

        else:
            print("未知命令，请输入chat、repo 或 exit")

if __name__ == "__main__":
    main()
    