from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from models.database import Base


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    title = Column(String(500), nullable=False)
    authors = Column(String(1000))
    source = Column(String(100))  # arXiv, PubMed, etc.
    url = Column(String(1000))
    abstract = Column(Text)
    citations = Column(Integer, default=0)
    published_at = Column(DateTime(timezone=True))
    analysis = Column(Text)  # AI analysis result
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "title": self.title,
            "authors": self.authors,
            "source": self.source,
            "url": self.url,
            "abstract": self.abstract,
            "citations": self.citations,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "analysis": self.analysis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
