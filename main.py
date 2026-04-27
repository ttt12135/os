from openai import OpenAI
from dotenv import load_dotenv
import os

#读取.env文件
load_dotenv()

#读取.env中的DEEPSEEK_API_KEY
api_key = os.getenv("DEEPSEEK_API_KEY")

if api_key is None:
    printf("api获取错误，检查.env文件")
    exit()

#创建deepseek客户端
client=OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)


def chat_with_ai(user_input):
    #函数用途：把用户的话发给DeepSeek
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            #上下文
            {
                "role":"system",
                "content":"你是一个帮助新手理解代码仓库和操作系统比赛项目的AI助手"
            },
            {
                "role":"user",
                "content":user_input
            }
        ],
        stream=False
    )

    ai_reply = response.choices[0].message.content
    return ai_reply

def main():
    print("OS agent 接入deepseek")
    print("输入exit退出")
    print("-"*30)

    while True:
        user_input = input("用户: ")

        if user_input == "exit":
            print("程序退出")
            break
        
        ai_reply = chat_with_ai(user_input)

        print("AI: ")
        print(ai_reply)
        print("-"*30)

if __name__ == "__main__":
    main()

