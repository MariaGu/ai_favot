import numpy as np
from sqlalchemy.orm import Session
from typing import Optional, List
from src.database.models import TrendCluster, ClusterArticle, Article
from src.generation.utils import truncate_text
from src.config.logging import logger

class DataFetcher:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_top_trend_cluster(self) -> Optional[TrendCluster]:
        """Получает топ‑1 кластер из последнего анализа."""
        latest_analysis = self.db_session.query(TrendCluster.analysis_id)\
            .order_by(TrendCluster.created_at.desc())\
            .first()

        if not latest_analysis:
            return None

        analysis_id = latest_analysis[0]

        top_cluster = self.db_session.query(TrendCluster)\
            .filter(
                TrendCluster.analysis_id == analysis_id,
                TrendCluster.rank == 1
            )\
            .first()

        return top_cluster

    def get_cluster_articles_with_embeddings(self, cluster_id: int) -> List[dict]:
        """Получает статьи и их embeddings для указанного кластера."""
        articles_data = []

        cluster_articles = self.db_session.query(ClusterArticle)\
            .filter(ClusterArticle.cluster_id == cluster_id)\
            .all()

        for ca in cluster_articles:
            article = ca.article
            if article.embedding:
                embedding = np.array(article.embedding)
            else:
                embedding = None  # будет вычислено позже

            articles_data.append({
                'article': article,
                'embedding': embedding,
                'similarity_score': ca.similarity_score
            })

        return articles_data
