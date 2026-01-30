from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from models.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    topic_ids = Column(String(500), nullable=True) # JSON list of IDs
    title = Column(String(500), nullable=False)
    abstract = Column(Text)
    content = Column(Text)
    version = Column(Integer, default=1)
    status = Column(String(20), default="draft")  # draft/reviewing/completed
    quality_score = Column(Float, default=0.0)
    detailed_scores = Column(Text, nullable=True) # JSON string of dimension scores
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "topic_ids": self.topic_ids,
            "title": self.title,
            "abstract": self.abstract,
            "content": self.content,
            "version": self.version,
            "status": self.status,
            "quality_score": self.quality_score,
            "detailed_scores": json.loads(self.detailed_scores) if self.detailed_scores else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    agent_role = Column(String(50))
    message = Column(Text)
    iteration = Column(Integer, default=1)

    # New columns for traceability
    model_signature = Column(String(100), nullable=True)
    step_name = Column(String(100), nullable=True)
    input_context = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "agent_role": self.agent_role,
            "message": self.message,
            "iteration": self.iteration,
            "model_signature": self.model_signature,
            "step_name": self.step_name,
            "input_context": self.input_context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
