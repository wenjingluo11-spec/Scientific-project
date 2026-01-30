from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from models.database import Base
import json as json_lib


class TopicRecommendation(Base):
    """Topic recommendation history model"""
    __tablename__ = "topic_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    research_field = Column(String(100), nullable=False)
    specific_topic = Column(String(150), nullable=True) # New column
    keywords = Column(Text, nullable=False)  # JSON string
    description = Column(Text, nullable=True)
    suggestions = Column(Text, nullable=False)  # JSON string of all suggestions
    model_signature = Column(String(100), nullable=True) # New column
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "research_field": self.research_field,
            "specific_topic": self.specific_topic,
            "keywords": json_lib.loads(self.keywords) if self.keywords else [],
            "description": self.description,
            "suggestions": json_lib.loads(self.suggestions) if self.suggestions else [],
            "model_signature": self.model_signature,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
