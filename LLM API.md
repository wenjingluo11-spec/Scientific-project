多协议支持 (Multi-Protocol Support)

baseurl:
http://127.0.0.1:8045/v1

模型支持：gemini-3-pro-high、gemini-3-flash、gemini-3-pro-low、gemini-3-pro-image、claude-sonnet-4-5、claude-sonnet-4-5-thinking、claude-opus-4-5-thinking


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
     model="claude-haiku-4-5",
     max_tokens=1024,
     messages=[{"role": "user", "content": "Hello"}]
 )
 
 print(response.content[0].text)
