"""
Raw LLM Client - 使用原生 HTTP 请求调用 LLM API
完全复制旧项目 (research-paper-ai) 的 Rust 实现逻辑
"""

import httpx
from typing import Optional, List, Dict, Any
from config import settings


class RawLLMClient:
    """
    使用原生 HTTP 请求调用 LLM API
    
    与旧项目 Rust 实现完全一致:
    - 使用 x-api-key 头进行认证
    - 设置 anthropic-version 头
    - 120 秒超时
    - 禁用代理
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ANTHROPIC_BASE_URL).rstrip('/')
        # 确保 base_url 不包含 /v1 后缀，因为我们会手动拼接
        if self.base_url.endswith('/v1'):
            self.base_url = self.base_url[:-3]
        
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = settings.DEFAULT_MODEL
        self.max_tokens = settings.MAX_TOKENS
        
        # 与旧项目一致的请求头
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None
    ) -> str:
        """
        发送消息并获取完成响应
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            model: 模型名称，默认使用配置中的 DEFAULT_MODEL
            max_tokens: 最大 token 数，默认使用配置中的 MAX_TOKENS
            system: 系统提示词 (可选)
        
        Returns:
            模型响应的文本内容
        """
        url = f"{self.base_url}/v1/messages"
        
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages
        }
        
        # 如果有系统提示词，添加到 payload
        if system:
            payload["system"] = system
        
        # 使用与旧项目一致的配置：120秒超时，禁用代理
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),
            proxy=None
        ) as client:
            response = await client.post(
                url,
                json=payload,
                headers=self.headers
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"API error: status={response.status_code}, body={error_text}")
            
            data = response.json()
            
            # 解析 Anthropic 响应格式: { "content": [{ "text": "..." }] }
            content = data.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
            
            raise Exception(f"Invalid response format: {data}")
    
    async def create_message(
        self,
        role: str,
        context: str,
        task: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> str:
        """
        创建消息 - 与 AnthropicClient 接口兼容
        
        Args:
            role: Agent 角色名称
            context: 背景信息
            task: 任务描述
            conversation_history: 历史对话记录
        
        Returns:
            模型响应的文本内容
        """
        system_prompt = self._get_system_prompt(role)
        
        messages = []
        
        # 添加历史记录
        if conversation_history:
            messages.extend(conversation_history)
        
        # 添加用户任务
        messages.append({
            "role": "user",
            "content": f"## 背景信息\n{context}\n\n## 任务\n{task}"
        })
        
        return await self.complete(messages, system=system_prompt)
    
    def _get_system_prompt(self, role: str) -> str:
        """获取角色对应的系统提示词"""
        prompts = {
            "research_director": """你是一位经验丰富的科研主管 (Research Director)。
你的职责是：
1. 深度拆解研究选题，制定逻辑严密的"分步研究计划"。
2. 分析选题的潜在创新点（Novelty）和关键技术难点。
3. 为后续的文献调研、方法设计和数据分析提供明确的指导方向。

请输出一份详细的研究大纲，包含：
- 核心研究问题 (Research Questions)
- 预期目标 (Expected Objectives)
- 关键研究步骤 (Key Steps)
""",
            "literature_researcher": """你是一位专业的文献调研专家 (Literature Researcher)。
你的职责是：
1. 搜索和整理相关领域的学术文献
2. 提取关键研究方法和发现
3. 识别研究空白和创新点
4. 生成文献综述

输出格式要求（严格 JSON）：
{
  "papers": [
    {
      "title": "论文标题",
      "authors": "作者列表",
      "source": "发表来源 (Journal/Conference/arXiv)",
      "date": "发表日期 (YYYY-MM-DD)",
      "citations": 120,
      "abstract": "摘要内容 (100-200字)",
      "url": "论文链接 (如果有)"
    }
  ]
}
""",
            "topic_discovery_expert": """你是一位资深的科研选题顾问 (Topic Discovery Expert)。

你的职责是：
1. 基于用户提供的研究方向/领域，推荐创新且可行的研究选题
2. 分析当前研究热点和未来趋势
3. 识别跨学科研究机会
4. 评估选题的新颖性和可行性

输出格式要求（严格 JSON）：
{
  "suggestions": [
    {
      "title": "选题标题（简洁明确，15-30字）",
      "description": "选题描述（200-300字，包含研究背景、目标、意义）",
      "field": "研究领域",
      "keywords": ["关键词1", "关键词2", "关键词3", "关键词4"],
      "novelty_score": 85,
      "feasibility_score": 78,
      "reasoning": "推荐理由（100-150字）"
    }
  ]
}
"""
        }
        
        return prompts.get(role, "你是一个专业的AI助手，请协助完成科研任务。")


# 测试函数
async def test_connection():
    """测试 API 连接"""
    print(f"Testing RawLLMClient...")
    print(f"Base URL: {settings.ANTHROPIC_BASE_URL}")
    print(f"Model: {settings.DEFAULT_MODEL}")
    
    client = RawLLMClient()
    
    try:
        response = await client.complete(
            messages=[{"role": "user", "content": "Hello, are you working? Reply with just 'Yes'."}],
            max_tokens=50
        )
        print(f"\n✅ SUCCESS! Response: {response}")
        return True
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())
