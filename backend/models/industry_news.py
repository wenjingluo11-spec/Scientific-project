from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from models.database import Base
import json


class IndustryNews(Base):
    __tablename__ = "industry_news"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, index=True, nullable=True) # Added for topic-based tracking
    title = Column(String(500), nullable=False)
    source = Column(String(200))
    url = Column(String(1000))
    content = Column(Text)
    keywords = Column(Text)  # JSON string
    relevance_score = Column(Float, default=0.0)
    published_at = Column(DateTime(timezone=True))
    model_signature = Column(String(100), nullable=True) # New column
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "content": self.content,
            "keywords": json.loads(self.keywords) if self.keywords else [],
            "relevance_score": self.relevance_score,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "model_signature": self.model_signature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
