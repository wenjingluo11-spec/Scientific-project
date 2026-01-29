多协议支持 (Multi-Protocol Support)

baseurl:
http://127.0.0.1:8045/v1

模型支持：gemini-3-pro-high、gemini-3-flash、gemini-3-pro-low、gemini-3-pro-image、claude-sonnet-4-5、claude-sonnet-4-5-thinking、claude-opus-4-5-thinking


## openAI协议：

from openai import OpenAI
 
 client = OpenAI(
     base_url="http://127.0.0.1:8045/v1",
     api_key=sk-691331534d4a403fbd2add1841357a8f"
 )
 
 response = client.chat.completions.create(
     model="gemini-3-pro-high",
     messages=[{"role": "user", "content": "Hello"}]
 )
 
 print(response.choices[0].message.content)

 

 ## Anthropic协议：

 http://127.0.0.1:8045/v1/messages
 from anthropic import Anthropic
 
 client = Anthropic(
     # 推荐使用 127.0.0.1
     base_url="http://127.0.0.1:8045",
     api_key="sk-691331534d4a403fbd2add1841357a8f"
 )
 
 # 注意: Antigravity 支持使用 Anthropic SDK 调用任意模型
 response = client.messages.create(
     model="gemini-3-pro-high",
     max_tokens=1024,
     messages=[{"role": "user", "content": "Hello"}]
 )
 
 print(response.content[0].text)


## Gemini 协议

 http://127.0.0.1:8045/v1beta/models

 # 需要安装: pip install google-generativeai
import google.generativeai as genai

# 使用 Antigravity 代理地址 (推荐 127.0.0.1)
genai.configure(
    api_key="sk-691331534d4a403fbd2add1841357a8f",
    transport='rest',
    client_options={'api_endpoint': 'http://127.0.0.1:8045'}
)

model = genai.GenerativeModel('gemini-3-pro-high')
response = model.generate_content("Hello")
print(response.text)
