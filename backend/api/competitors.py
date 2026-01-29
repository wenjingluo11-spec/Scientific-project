from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.database import get_db
from models.competitor import Competitor
from models.topic import Topic
from utils.anthropic_client import AnthropicClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class CompetitorResponse(BaseModel):
    id: int
    topic_id: int
    title: str
    authors: str
    source: str
    url: Optional[str]
    abstract: str
    citations: int
    published_at: Optional[str]
    analysis: Optional[str]
    created_at: str


@router.get("/", response_model=List[CompetitorResponse])
async def get_competitors(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get competitors for a specific topic using AI Search"""

    # 1. Get Topic Details
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Force Refresh: Delete old competitors for this topic to ensure real-time search
    # User requested: "查找每一个选题都是实时搜索得到的... 不要根据关键词"
    from sqlalchemy import delete
    await db.execute(delete(Competitor).where(Competitor.topic_id == topic_id))
    await db.commit()
    
    # 3. Call AI to search papers
    client = AnthropicClient()
    
    # Parse keywords (stored as JSON string)
    try:
        import json
        keywords_list = json.loads(topic.keywords) if topic.keywords else []
        keywords_str = ', '.join(keywords_list)
    except:
        keywords_str = topic.keywords if topic.keywords else ""

    # Construct Context with emphasis on Title
    context = f"""研究选题: {topic.title}
研究领域: {topic.field}
选题描述: {topic.description}
相关关键词: {keywords_str}"""

    task = """请作为一名在该领域经验丰富的专家，针对上述“研究选题”进行深度文献检索。

核心要求：
1. **精准匹配**：请忽略过于宽泛的关键词，重点匹配“选题标题”和“选题描述”中定义的核心科学问题。
2. **实时搜索/回忆**：请寻找与该特定选题最相关的竞品论文（或高度相关的经典参考文献）。
3. **真实性**：请尽量提供真实的论文、作者和来源。如果无法连接外部数据库，请基于你的大规模知识库提供准确的经典论文。
4. **数量**：推荐 5 篇最相关的论文。

请确保推荐的论文确实解决了与该选题类似的问题，而不仅仅是领域相同。"""

    try:
        response_text = await client.create_message(
            role="literature_researcher",
            context=context,
            task=task
        )
        
        # 4. Parse JSON
        import json
        import re
        
        # Clean up JSON markdown
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
        papers = data.get("papers", [])

        competitors = []
        for p in papers:
            # Handle date parsing looseness
            pub_date = datetime.now()
            try:
                if "date" in p and p["date"]:
                    pub_date = datetime.strptime(p["date"], "%Y-%m-%d")
            except:
                pass

            competitor = Competitor(
                topic_id=topic_id,
                title=p.get("title", "Unknown Title"),
                authors=p.get("authors", "Unknown Authors"),
                source=p.get("source", "Unknown Source"),
                url=p.get("url", ""),
                abstract=p.get("abstract", "No abstract available."),
                citations=p.get("citations", 0),
                published_at=pub_date
            )
            db.add(competitor)
            competitors.append(competitor)
        
        await db.commit()
        
        for comp in competitors:
            await db.refresh(comp)
            
        return [comp.to_dict() for comp in competitors]

    except Exception as e:
        print(f"Error in AI Competitor Search: {e}")
        # Build a fallback error object or raise
        raise HTTPException(status_code=500, detail=f"AI Search Failed: {str(e)}")


@router.post("/{competitor_id}/analyze", response_model=CompetitorResponse)
async def analyze_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Use AI to analyze a competitor paper"""

    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Use Anthropic API to analyze
    client = AnthropicClient()

    analysis_prompt = f"""请分析以下竞品论文，提供详细的对比分析：

标题: {competitor.title}
作者: {competitor.authors}
来源: {competitor.source}
引用数: {competitor.citations}
摘要: {competitor.abstract}

请从以下方面进行分析：
1. 主要创新点
2. 技术优势和劣势
3. 研究方法的特点
4. 与我们研究的差异化机会
5. 可以借鉴的方面

请提供专业、客观的分析。"""

    analysis = await client.create_message(
        role="peer_reviewer",
        context="",
        task=analysis_prompt,
    )

    competitor.analysis = analysis
    await db.commit()
    await db.refresh(competitor)

    return competitor.to_dict()


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific competitor"""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    return competitor.to_dict()
