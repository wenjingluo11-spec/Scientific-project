from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.topic import Topic
from models.topic_recommendation import TopicRecommendation
from pydantic import BaseModel
from typing import List, Optional
import json
from services.topic_discovery import TopicDiscoveryService

router = APIRouter()


class TopicCreate(BaseModel):
    title: str
    description: Optional[str] = None
    field: Optional[str] = None
    specific_topic: Optional[str] = None
    keywords: Optional[List[str]] = None


class TopicResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    field: Optional[str]
    specific_topic: Optional[str] = None
    keywords: List[str]
    status: str
    created_at: str
    updated_at: Optional[str]


@router.get("/", response_model=List[TopicResponse])
async def get_topics(db: AsyncSession = Depends(get_db)):
    """Get all topics"""
    result = await db.execute(select(Topic).order_by(Topic.created_at.desc()))
    topics = result.scalars().all()
    return [topic.to_dict() for topic in topics]


# ==================== AI Discovery Endpoints ====================
# NOTE: These routes must be defined BEFORE /{topic_id} to avoid route conflicts

class TopicDiscoveryRequest(BaseModel):
    research_field: str
    topic: Optional[str] = None
    keywords: List[str]
    description: Optional[str] = None
    num_suggestions: int = 5
    use_deep_research: bool = False


class TopicSuggestion(BaseModel):
    title: str
    description: str
    field: str
    keywords: List[str]
    novelty_score: int
    feasibility_score: int
    reasoning: str


@router.post("/ai-discover")
async def discover_topics(request: TopicDiscoveryRequest, db: AsyncSession = Depends(get_db)):
    """AI-powered topic discovery"""
    service = TopicDiscoveryService(db)

    try:
        result = await service.discover(
            field=request.research_field,
            keywords=request.keywords,
            topic=request.topic,
            description=request.description,
            num_suggestions=request.num_suggestions,
            use_deep_research=request.use_deep_research
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_recommendation_history(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get recommendation history"""
    result = await db.execute(
        select(TopicRecommendation)
        .order_by(TopicRecommendation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    recommendations = result.scalars().all()
    return [rec.to_dict() for rec in recommendations]


@router.get("/recommendations/{recommendation_id}")
async def get_recommendation_by_id(
    recommendation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific recommendation by ID"""
    result = await db.execute(
        select(TopicRecommendation).where(TopicRecommendation.id == recommendation_id)
    )
    recommendation = result.scalar_one_or_none()

    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return recommendation.to_dict()


class BatchCreateRequest(BaseModel):
    topics: List[TopicCreate]


class BatchCreateResponse(BaseModel):
    created: List[TopicResponse]
    failed: List[dict]


@router.post("/batch-create", response_model=BatchCreateResponse)
async def batch_create_topics(
    request: BatchCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Batch create topics"""
    created = []
    failed = []

    for topic_data in request.topics:
        try:
            topic = Topic(
                title=topic_data.title,
                description=topic_data.description,
                field=topic_data.field,
                specific_topic=topic_data.specific_topic,
                keywords=json.dumps(topic_data.keywords or [], ensure_ascii=False),
                status="pending",
            )
            db.add(topic)
            created.append(topic)
        except Exception as e:
            failed.append({"topic": topic_data.title, "error": str(e)})

    await db.commit()

    for topic in created:
        await db.refresh(topic)

    return {
        "created": [t.to_dict() for t in created],
        "failed": failed
    }


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get topic by ID"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return topic.to_dict()


@router.post("/", response_model=TopicResponse)
async def create_topic(topic_data: TopicCreate, db: AsyncSession = Depends(get_db)):
    """Create a new topic"""
    topic = Topic(
        title=topic_data.title,
        description=topic_data.description,
        field=topic_data.field,
        specific_topic=topic_data.specific_topic,
        keywords=json.dumps(topic_data.keywords or [], ensure_ascii=False),
        status="pending",
    )

    db.add(topic)
    await db.commit()
    await db.refresh(topic)

    return topic.to_dict()


@router.get("/search/", response_model=List[TopicResponse])
async def search_topics(q: str, db: AsyncSession = Depends(get_db)):
    """Search topics by query"""
    result = await db.execute(
        select(Topic).where(
            (Topic.title.contains(q)) |
            (Topic.description.contains(q)) |
            (Topic.keywords.contains(q))
        ).order_by(Topic.created_at.desc())
    )
    topics = result.scalars().all()
    return [topic.to_dict() for topic in topics]


@router.delete("/{topic_id}")
async def delete_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a topic"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    await db.delete(topic)
    await db.commit()

    return {"message": "Topic deleted successfully"}
