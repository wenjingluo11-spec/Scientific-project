from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from models.database import Base
import json


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    field = Column(String(100))
    specific_topic = Column(String(200), nullable=True) # New column
    keywords = Column(Text)  # JSON string
    status = Column(String(20), default="pending")  # pending/processing/completed
    model_signature = Column(String(100), nullable=True)  # New column
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "field": self.field,
            "specific_topic": self.specific_topic,
            "keywords": json.loads(self.keywords) if self.keywords else [],
            "status": self.status,
            "model_signature": self.model_signature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
