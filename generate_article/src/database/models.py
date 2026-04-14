from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from .base import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String)
    publish_date = Column(DateTime, nullable=False)
    embedding = Column(ARRAY(Float))  # массив чисел с плавающей точкой

    # Связь с кластерами
    cluster_associations = relationship("ClusterArticle", back_populates="article")

class GeneratedArticle(Base):
    __tablename__ = "generated_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cluster_id = Column(Integer, ForeignKey("trend_clusters.id"), nullable=False)
    cluster_name = Column(String, nullable=False)  # название кластера для удобства
    similarity_score = Column(Float, default=0.85)  # сходство сгенерированной статьи
    generation_metadata = Column(String)  # JSON с метаданными генерации
    embedding = Column(ARRAY(Float))  # массив чисел с плавающей точкой

    # Связь с кластером
    cluster = relationship("TrendCluster", back_populates="generated_articles")


class TrendAnalysis(Base):
    __tablename__ = "trend_analyses"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_articles = Column(Integer, default=0)

    # Связь с кластерами
    clusters = relationship("TrendCluster", back_populates="analysis")

class TrendCluster(Base):
    __tablename__ = "trend_clusters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # название тренда/кластера
    analysis_id = Column(Integer, ForeignKey("trend_analyses.id"))
    rank = Column(Integer, nullable=False)  # рейтинг в анализе (1 — наивысший)
    article_count = Column(Integer, default=0)  # количество статей в кластере
    hours_period = Column(Integer, nullable=False)  # период анализа в часах
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    analysis = relationship("TrendAnalysis", back_populates="clusters")
    articles = relationship("ClusterArticle", back_populates="cluster")
    # Новая связь с сгенерированными статьями
    generated_articles = relationship("GeneratedArticle", back_populates="cluster")

class ClusterArticle(Base):
    __tablename__ = "cluster_articles"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("trend_clusters.id"))
    article_id = Column(Integer, ForeignKey("articles.id"))
    similarity_score = Column(Float)  # степень сходства со средним вектором кластера
    article_rank = Column(Integer)  # ранг статьи в кластере (по близости к центру)

    # Связи
    cluster = relationship("TrendCluster", back_populates="articles")
    article = relationship("Article", back_populates="cluster_associations")
