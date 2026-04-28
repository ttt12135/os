from openai import OpenAI
from dotenv import load_dotenv
from src.repo_reader import build_file_tree
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
        "content":"你是一个帮助新手理解代码仓库和操作系统比赛项目的AI助手"
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
    #读取本地的repo文件

    file_tree = build_file_tree(repo_path)

    #AI提示词模块，首次接触加深学习
    prompt = f"""
    下面是一个代码仓库的文件结构：

    {file_tree}

    请你认真的解释这个代码仓库。
    要求如下：
    1、说明这个仓库目前有哪些主要文件和目录；
    2、解释每个重要文件的作用；
    3、给出阅读这个仓库的顺序；
    4、如果这个仓库有可优化的地方，指出后续如何拓展。
    """
    ai_reply = chat_with_ai(prompt)

    return file_tree, ai_reply
     

def main():
    print("OS agent 接入deepseek,加入上下文记忆，加入repo")
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
            file_tree, ai_reply = analyze_repo(repo_path)

            print("\n仓库文件结构：")
            print(file_tree)

            print("\nAI 分析: ")
            print(ai_reply)
            print("-"*30)    

        else:
            print("未知命令，请输入chat、repo 或 exit")

if __name__ == "__main__":
    main()
    