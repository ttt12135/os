from openai import OpenAI
from dotenv import load_dotenv
from src.repo_reader import build_file_tree
from src.file_reader import collect_important_files, format_files_content
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
    files_content = format_files_content(important_files)

    #AI提示词模块，首次接触加深学习
    prompt = f"""
下面是一个代码仓库的文件结构：
一、仓库的文件结构
{file_tree}

二、仓库的关键文件内容

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

    return file_tree, files_content, ai_reply
     

def main():
    print("OS agent 接入deepseek,加入上下文记忆，加入repo，可读取关键文件的内容")
    print("-"*30)

    while True:
        user_input = input("请选择模式（chat/repo/exit）: ")

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
            file_tree, file_content, ai_reply = analyze_repo(repo_path)

            print("\n仓库文件结构：")
            print(file_tree)

            print("\n关键文件内容：")
            print(file_content)

            print("\nAI 分析: ")
            print(ai_reply)
            print("-"*30)    

        else:
            print("未知命令，请输入chat、repo 或 exit")

if __name__ == "__main__":
    main()
    