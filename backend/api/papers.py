from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db, async_session_maker
from models.paper import Paper
from models.topic import Topic
from services.orchestrator import AgentOrchestrator
from pydantic import BaseModel
from typing import List, Optional
import asyncio

router = APIRouter()

class PaperGenerateRequest(BaseModel):
    topic_id: int

class PaperResponse(BaseModel):
    id: int
    topic_id: int
    title: str
    abstract: Optional[str]
    content: Optional[str]
    version: int
    status: str
    quality_score: float
    created_at: str

class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, paper_id: int):
        await websocket.accept()
        if paper_id not in self.active_connections:
            self.active_connections[paper_id] = []
        self.active_connections[paper_id].append(websocket)

    def disconnect(self, websocket: WebSocket, paper_id: int):
        if paper_id in self.active_connections:
            self.active_connections[paper_id].remove(websocket)

    async def send_progress(self, paper_id: int, data: dict):
        if paper_id in self.active_connections:
            for connection in self.active_connections[paper_id]:
                try:
                    await connection.send_json(data)
                except:
                    pass

manager = ConnectionManager()

async def run_paper_generation(paper_id: int, topic_id: int):
    """Background task to run paper generation"""
    async with async_session_maker() as db:
        orchestrator = AgentOrchestrator(db)
        
        async def progress_callback(data: dict):
            await manager.send_progress(paper_id, data)
            
        try:
            await orchestrator.generate_paper(
                topic_id=topic_id,
                paper_id=paper_id,
                progress_callback=progress_callback
            )
        except Exception as e:
            print(f"Background Paper Generation Error for {paper_id}: {e}")
            # Update paper status to error
            result = await db.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if paper:
                paper.status = "error"
                await db.commit()

@router.get("/", response_model=List[PaperResponse])
async def get_papers(db: AsyncSession = Depends(get_db)):
    """Get all papers"""
    result = await db.execute(select(Paper).order_by(Paper.created_at.desc()))
    papers = result.scalars().all()
    return [paper.to_dict() for paper in papers]


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Get paper by ID"""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return paper.to_dict()

@router.post("/generate", response_model=PaperResponse)
async def generate_paper(
    request: PaperGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start paper generation in background"""

    # 1. Get Topic
    result = await db.execute(select(Topic).where(Topic.id == request.topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Create Paper entry immediately
    paper = Paper(
        topic_id=request.topic_id,
        title=f"Research on {topic.title}",
        status="processing",
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)

    # 3. Add to background tasks
    background_tasks.add_task(run_paper_generation, paper.id, request.topic_id)

    return paper.to_dict()


@router.websocket("/ws/paper/{paper_id}")
async def websocket_endpoint(websocket: WebSocket, paper_id: int):
    """WebSocket endpoint for real-time progress updates"""
    await manager.connect(websocket, paper_id)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket, paper_id)


@router.delete("/{paper_id}")
async def delete_paper(paper_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a paper"""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    await db.delete(paper)
    await db.commit()

    return {"message": "Paper deleted successfully"}
