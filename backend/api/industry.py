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


class IndustryNewsSearchItem(BaseModel):
    title: str
    source: str
    url: Optional[str] = None
    content: str
    keywords: List[str] = []
    relevance_score: float = 0.0
    published_at: Optional[str] = None


class IndustryNewsResponse(BaseModel):
    id: Optional[int] = None
    topic_id: Optional[int] = None
    title: str
    source: str
    url: Optional[str] = None
    content: str
    keywords: List[str] = []
    relevance_score: float = 0.0
    published_at: Optional[str] = None
    created_at: str


class IndustryNewsCreate(BaseModel):
    topic_id: Optional[int] = None
    title: str
    source: str
    url: Optional[str] = None
    content: str
    keywords: List[str] = []
    relevance_score: float = 0.0
    published_at: Optional[str] = None


class IndustryNewsUpdate(BaseModel):
    title: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    relevance_score: Optional[float] = None
    published_at: Optional[str] = None


@router.get("/news", response_model=List[IndustryNewsResponse])
async def get_industry_news(topic_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Get industry news, optionally filtered by topic"""
    query = select(IndustryNews).order_by(IndustryNews.published_at.desc()).limit(50)
    
    if topic_id:
        query = query.where(IndustryNews.topic_id == topic_id)
        
    result = await db.execute(query)
    news_list = result.scalars().all()
    return [news.to_dict() for news in news_list]


@router.post("/search", response_model=List[IndustryNewsSearchItem])
async def search_industry_news(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Search industry news for a specific topic using AI (Returns transient results)"""

    # 1. Get Topic Details
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Call AI to search industry news
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

    task = "请作为一名科技行业分析师，搜索并推荐 5 条与该选题高度相关的最新行业动态（**必须是 2025-2026 年的最新数据**）。请严格遵守 JSON 格式要求。"

    try:
        response_text = await client.create_message(
            role="industry_analyst",
            context=context,
            task=task
        )

        # 3. Parse JSON
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
        
        # Map fields (especially 'date' -> 'published_at') and handle potential None values
        processed_items = []
        for item in news_items:
            processed_item = {
                "title": item.get("title") or "无标题动态",
                "source": item.get("source") or "未知来源",
                "url": item.get("url"),
                "content": item.get("content") or "暂无内容描述",
                "keywords": item.get("keywords") or [],
                "relevance_score": float(item.get("relevance_score") or 0.0),
                "published_at": item.get("published_at") or item.get("date") or datetime.now().strftime("%Y-%m-%d")
            }
            processed_items.append(processed_item)
            
        return processed_items

    except Exception as e:
        print(f"Error in Industry AI Search: {e}")
        raise HTTPException(status_code=500, detail=f"AI Search Failed: {str(e)}")


@router.post("/refresh", response_model=List[IndustryNewsResponse])
async def refresh_industry_news(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Keep for backward compatibility, but this implementation will now use search and NOT save automatically if preferred, 
    but for now let's keep it as is or change to match the new 'transient' requirement."""
    # Actually, let's just use /search from the frontend.
    return await search_industry_news(topic_id, db)


@router.get("/news/{news_id}", response_model=IndustryNewsResponse)
async def get_news_item(news_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific news item"""
    result = await db.execute(select(IndustryNews).where(IndustryNews.id == news_id))
    news = result.scalar_one_or_none()

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    return news.to_dict()


@router.post("/", response_model=IndustryNewsResponse)
async def create_news_item(news_data: IndustryNewsCreate, db: AsyncSession = Depends(get_db)):
    """Create a news item manually"""
    pub_date = datetime.now()
    if news_data.published_at:
        try:
            if 'T' in news_data.published_at:
                pub_date = datetime.fromisoformat(news_data.published_at.replace('Z', '+00:00'))
            else:
                pub_date = datetime.strptime(news_data.published_at, "%Y-%m-%d")
        except:
            pub_date = datetime.now()

    news = IndustryNews(
        topic_id=news_data.topic_id,
        title=news_data.title,
        source=news_data.source,
        url=news_data.url,
        content=news_data.content,
        keywords=json.dumps(news_data.keywords, ensure_ascii=False),
        relevance_score=news_data.relevance_score,
        published_at=pub_date
    )
    db.add(news)
    await db.commit()
    await db.refresh(news)
    return news.to_dict()


@router.put("/{news_id}", response_model=IndustryNewsResponse)
async def update_news_item(news_id: int, news_data: IndustryNewsUpdate, db: AsyncSession = Depends(get_db)):
    """Update a news item"""
    result = await db.execute(select(IndustryNews).where(IndustryNews.id == news_id))
    news = result.scalar_one_or_none()

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    update_data = news_data.dict(exclude_unset=True)
    
    if "keywords" in update_data:
        news.keywords = json.dumps(update_data["keywords"], ensure_ascii=False)
        del update_data["keywords"]
    
    if "published_at" in update_data and update_data["published_at"]:
        try:
            news.published_at = datetime.fromisoformat(update_data["published_at"].replace('Z', '+00:00'))
            del update_data["published_at"]
        except:
            pass

    for key, value in update_data.items():
        setattr(news, key, value)

    await db.commit()
    await db.refresh(news)
    return news.to_dict()


@router.delete("/{news_id}")
async def delete_news_item(news_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a news item"""
    result = await db.execute(select(IndustryNews).where(IndustryNews.id == news_id))
    news = result.scalar_one_or_none()

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    await db.delete(news)
    await db.commit()
    return {"message": "News deleted successfully"}
