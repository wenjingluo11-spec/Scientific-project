from utils.anthropic_client import AnthropicClient
import json
from typing import List, Dict, Optional
import re
from sqlalchemy.ext.asyncio import AsyncSession
from models.topic_recommendation import TopicRecommendation


class TopicDiscoveryService:
    """AI-powered topic discovery service"""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.client = AnthropicClient()
        self.db = db

    async def discover(
        self,
        field: str,
        keywords: List[str],
        description: str = None,
        num_suggestions: int = 5
    ) -> Dict:
        """
        使用 AI 推荐研究选题

        Args:
            field: 研究领域
            keywords: 关键词列表
            description: 研究方向描述（可选）
            num_suggestions: 推荐数量，默认 5

        Returns:
            包含 suggestions 列表的字典
        """

        # 构建上下文
        context = f"""研究领域: {field}
关键词: {', '.join(keywords)}"""

        if description:
            context += f"\n研究方向描述: {description}"

        # 构建任务
        task = f"请推荐 {num_suggestions} 个创新且可行的研究选题，严格按照 JSON 格式输出。"

        # 调用 AI
        response = await self.client.create_message(
            role="topic_discovery_expert",
            context=context,
            task=task
        )

        # 解析 JSON
        try:
            # 尝试直接解析
            result = json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分（处理 AI 可能在 JSON 前后添加说明文字的情况）
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise ValueError(f"AI 返回格式错误，无法解析为有效 JSON。原始响应: {response[:200]}...")
            else:
                raise ValueError(f"AI 返回格式错误，无法解析为有效 JSON。原始响应: {response[:200]}...")

        # 保存推荐历史到数据库
        if self.db:
            try:
                recommendation = TopicRecommendation(
                    research_field=field,
                    keywords=json.dumps(keywords, ensure_ascii=False),
                    description=description,
                    suggestions=json.dumps(result.get('suggestions', []), ensure_ascii=False)
                )
                self.db.add(recommendation)
                await self.db.commit()
                await self.db.refresh(recommendation)

                # 添加历史记录 ID 到返回结果
                result['recommendation_id'] = recommendation.id
            except Exception as e:
                # 记录错误但不影响推荐结果返回
                print(f"Warning: Failed to save recommendation history: {e}")
                await self.db.rollback()

        return result
