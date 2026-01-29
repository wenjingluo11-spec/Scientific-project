from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api import topics, papers, industry, competitors
from models.database import init_db
# 导入所有模型以确保数据库表被创建
from models.topic import Topic
from models.topic_recommendation import TopicRecommendation


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("Database initialized successfully")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Scientific Research Assistant API",
    description="AI-powered research assistant with multi-agent paper generation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics.router, prefix="/api/v1/topics", tags=["Topics"])
app.include_router(papers.router, prefix="/api/v1/papers", tags=["Papers"])
app.include_router(industry.router, prefix="/api/v1/industry", tags=["Industry"])
app.include_router(competitors.router, prefix="/api/v1/competitors", tags=["Competitors"])


@app.get("/")
async def root():
    return {
        "message": "Scientific Research Assistant API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
