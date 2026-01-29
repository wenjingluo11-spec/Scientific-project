from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.competitor import Competitor
from models.topic import Topic
from utils.anthropic_client import AnthropicClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class CompetitorSearchItem(BaseModel):
    title: str
    authors: str
    source: str
    url: Optional[str] = None
    abstract: str
    citations: int = 0
    published_at: Optional[str] = None


class CompetitorResponse(BaseModel):
    id: Optional[int] = None
    topic_id: int
    title: str
    authors: str
    source: str
    url: Optional[str] = None
    abstract: str
    citations: int = 0
    published_at: Optional[str] = None
    analysis: Optional[str] = None
    created_at: str


class CompetitorCreate(BaseModel):
    topic_id: int
    title: str
    authors: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    citations: int = 0
    published_at: Optional[str] = None


class CompetitorUpdate(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    citations: Optional[int] = None
    published_at: Optional[str] = None
    analysis: Optional[str] = None


@router.get("/", response_model=List[CompetitorResponse])
async def get_competitors(topic_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Get competitors, optionally filtered by topic"""
    query = select(Competitor).order_by(Competitor.created_at.desc()).limit(50)
    
    if topic_id:
        query = query.where(Competitor.topic_id == topic_id)
        
    result = await db.execute(query)
    competitors = result.scalars().all()
    return [comp.to_dict() for comp in competitors]


@router.post("/search", response_model=List[CompetitorSearchItem])
async def search_competitors(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Search competitors for a specific topic using AI (Returns transient results)"""

    # 1. Get Topic Details
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Call AI to search papers
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
5. **JSON 格式**：请严格按照 JSON 格式返回。

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
}"""

    try:
        response_text = await client.create_message(
            role="literature_researcher",
            context=context,
            task=task
        )
        
        # 3. Parse JSON
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
        
        # Map fields (especially 'date' -> 'published_at') and handle potential None values
        processed_papers = []
        for p in papers:
            processed_paper = {
                "title": p.get("title") or "未命名论文",
                "authors": p.get("authors") or "不详",
                "source": p.get("source") or "未知渠道",
                "url": p.get("url"),
                "abstract": p.get("abstract") or "暂无摘要",
                "citations": int(p.get("citations") or 0),
                "published_at": p.get("published_at") or p.get("date") or datetime.now().strftime("%Y-%m-%d"),
                "analysis": p.get("analysis")
            }
            processed_papers.append(processed_paper)
            
        return processed_papers

    except Exception as e:
        print(f"Error in AI Competitor Search: {e}")
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


@router.post("/", response_model=CompetitorResponse)
async def create_competitor(comp_data: CompetitorCreate, db: AsyncSession = Depends(get_db)):
    """Create a competitor manually"""
    pub_date = datetime.now()
    if comp_data.published_at:
        try:
            # Try ISO format first
            if 'T' in comp_data.published_at:
                pub_date = datetime.fromisoformat(comp_data.published_at.replace('Z', '+00:00'))
            else:
                # Try YYYY-MM-DD
                pub_date = datetime.strptime(comp_data.published_at, "%Y-%m-%d")
        except:
            # Fallback to current time if parsing fails
            pub_date = datetime.now()

    competitor = Competitor(
        topic_id=comp_data.topic_id,
        title=comp_data.title,
        authors=comp_data.authors,
        source=comp_data.source,
        url=comp_data.url,
        abstract=comp_data.abstract,
        citations=comp_data.citations,
        published_at=pub_date
    )
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return competitor.to_dict()


@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(competitor_id: int, comp_data: CompetitorUpdate, db: AsyncSession = Depends(get_db)):
    """Update a competitor"""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    update_data = comp_data.dict(exclude_unset=True)
    
    if "published_at" in update_data and update_data["published_at"]:
        try:
            competitor.published_at = datetime.fromisoformat(update_data["published_at"].replace('Z', '+00:00'))
            del update_data["published_at"]
        except:
            pass

    for key, value in update_data.items():
        setattr(competitor, key, value)

    await db.commit()
    await db.refresh(competitor)
    return competitor.to_dict()


@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a competitor"""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    await db.delete(competitor)
    await db.commit()
    return {"message": "Competitor deleted successfully"}
