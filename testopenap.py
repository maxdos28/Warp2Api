import openai

client = openai.OpenAI(
    base_url="https://v8d29kx9-28889.use.devtunnels.ms/v1",
    api_key="0000"  # 可选：某些客户端需要，但服务器不强制验证
)

response = client.chat.completions.create(
    model="claude-4-sonnet",  # 选择支持的模型
    messages=[
        {"role": "user", "content": "你好，你好吗？"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
