from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, ARRAY, Float, Boolean, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    def as_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if not c.name.startswith('_')
        }

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String)
    publish_date = Column(DateTime, nullable=False)
    embedding = Column(ARRAY(Float))
    cluster_associations = relationship("ClusterArticle", back_populates="article")

    def as_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if not c.name.startswith('_')
        }

class GeneratedArticle(Base):
    __tablename__ = "generated_articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cluster_id = Column(Integer, ForeignKey("trend_clusters.id"), nullable=False)
    cluster_name = Column(String, nullable=False)
    similarity_score = Column(Float, default=0.85)
    generation_metadata = Column(String)
    embedding = Column(ARRAY(Float))
    cluster = relationship("TrendCluster", back_populates="generated_articles")

    def as_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if not c.name.startswith('_')
        }

class TrendAnalysis(Base):
    __tablename__ = "trend_analyses"
    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_articles = Column(Integer, default=0)
    clusters = relationship("TrendCluster", back_populates="analysis")

    def as_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if not c.name.startswith('_')
        }

class TrendCluster(Base):
    __tablename__ = "trend_clusters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    analysis_id = Column(Integer, ForeignKey("trend_analyses.id"))
    rank = Column(Integer, nullable=False)
    article_count = Column(Integer, default=0)
    hours_period = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    analysis = relationship("TrendAnalysis", back_populates="clusters")
    articles = relationship("ClusterArticle", back_populates="cluster")
    generated_articles = relationship("GeneratedArticle", back_populates="cluster")

    def as_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if not c.name.startswith('_')
        }

class ClusterArticle(Base):
    __tablename__ = "cluster_articles"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("trend_clusters.id"))
    article_id = Column(Integer, ForeignKey("articles.id"))
    similarity_score = Column(Float)
    article_rank = Column(Integer)
    cluster = relationship("TrendCluster", back_populates="articles")
    article = relationship("Article", back_populates="cluster_associations")

    def as_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if not c.name.startswith('_')
        }

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    source_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


    # Ограничение CHECK для source_type
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('website', 'rss')",
            name="data_sources_source_type_check"
        ),
    )   

    def as_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if not c.name.startswith('_')
        } 
