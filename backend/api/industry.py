from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.database import get_db
from models.industry_news import IndustryNews
from models.topic import Topic
from utils.anthropic_client import AnthropicClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import re

router = APIRouter()


class IndustryNewsResponse(BaseModel):
    id: int
    title: str
    source: str
    url: Optional[str]
    content: str
    keywords: List[str]
    relevance_score: float
    published_at: Optional[str]
    created_at: str


@router.get("/news", response_model=List[IndustryNewsResponse])
async def get_industry_news(topic_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Get industry news, optionally filtered by topic"""
    query = select(IndustryNews).order_by(IndustryNews.published_at.desc()).limit(50)
    
    if topic_id:
        query = query.where(IndustryNews.topic_id == topic_id)
        
    result = await db.execute(query)
    news_list = result.scalars().all()
    return [news.to_dict() for news in news_list]


@router.post("/refresh", response_model=List[IndustryNewsResponse])
async def refresh_industry_news(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Refresh industry news for a specific topic using AI"""

    # 1. Get Topic Details
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Force Refresh: Delete old news for this topic
    await db.execute(delete(IndustryNews).where(IndustryNews.topic_id == topic_id))
    await db.commit()

    # 3. Call AI to search industry news
    client = AnthropicClient()

    # Parse keywords
    try:
        keywords_list = json.loads(topic.keywords) if topic.keywords else []
        keywords_str = ', '.join(keywords_list)
    except:
        keywords_str = topic.keywords if topic.keywords else ""

    context = f"""研究选题: {topic.title}
研究领域: {topic.field}
选题描述: {topic.description}
相关关键词: {keywords_str}"""

    task = "请作为一名科技行业分析师，搜索并推荐 5 条与该选题高度相关的最新行业动态。请严格遵守 JSON 格式要求。"

    try:
        response_text = await client.create_message(
            role="industry_analyst",
            context=context,
            task=task
        )

        # 4. Parse JSON
        json_str = response_text.strip()
        if "```json" in json_str:
            match = re.search(r"```json(.*?)```", json_str, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
        elif "```" in json_str:
             match = re.search(r"```(.*?)```", json_str, re.DOTALL)
             if match:
                json_str = match.group(1).strip()

        data = json.loads(json_str)
        news_items = data.get("news", [])

        news_objects = []
        for item in news_items:
            # Handle date parsing
            pub_date = datetime.now()
            try:
                if "date" in item and item["date"]:
                    pub_date = datetime.strptime(item["date"], "%Y-%m-%d")
            except:
                pass
            
            # Handle keywords list to JSON string
            keywords_json = "[]"
            if "keywords" in item:
                 keywords_json = json.dumps(item["keywords"], ensure_ascii=False)

            news = IndustryNews(
                topic_id=topic_id,
                title=item.get("title", "Unknown Title"),
                source=item.get("source", "Unknown Source"),
                url=item.get("url", ""),
                content=item.get("content", "No content available."),
                keywords=keywords_json,
                relevance_score=item.get("relevance_score", 0.0),
                published_at=pub_date
            )
            db.add(news)
            news_objects.append(news)

        await db.commit()

        for news in news_objects:
            await db.refresh(news)

        return [news.to_dict() for news in news_objects]

    except Exception as e:
        print(f"Error in Industry AI Search: {e}")
        raise HTTPException(status_code=500, detail=f"AI Search Failed: {str(e)}")


@router.get("/news/{news_id}", response_model=IndustryNewsResponse)
async def get_news_item(news_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific news item"""
    result = await db.execute(select(IndustryNews).where(IndustryNews.id == news_id))
    news = result.scalar_one_or_none()

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    return news.to_dict()
