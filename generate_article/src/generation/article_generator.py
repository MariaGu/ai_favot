import logging
from datetime import datetime
import json
from sqlalchemy.orm import Session
from typing import Optional
from sentence_transformers import SentenceTransformer

from src.generation.data_fetcher import DataFetcher
from src.generation.rag_processor import RAGProcessor
from src.generation.llm_client import RemoteLLMClient  # Импортируем новый клиент
from src.generation.config import RAG_CONFIG, PROMPT_TEMPLATE
from src.generation.utils import truncate_text
from src.database.models import TrendCluster, GeneratedArticle
from src.config.logging import logger

class RAGArticleGenerator:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.data_fetcher = DataFetcher(db_session)
        self.embedding_model = SentenceTransformer(RAG_CONFIG['embedding_model'])
        self.rag_processor = RAGProcessor(self.embedding_model)

        # Инициализируем клиент для удалённого LLM
        self.llm_generator = RemoteLLMClient(
            base_url="http://95.164.92.12:11434",
            model="qwen2.5:0.5b"
        )

    def generate_trend_based_article(self) -> Optional[GeneratedArticle]:
        """Основной метод: генерирует статью на основе топ‑1 тренда с использованием RAG."""
        logger.info("Запуск генерации статьи на основе топ‑тренда с RAG")

        # 1. Получаем топ‑1 кластер
        top_cluster = self.data_fetcher.get_top_trend_cluster()
        if not top_cluster:
            logger.warning("Не найден топ‑1 тренд для генерации статьи")
            return None

        logger.info(f"Найден топ‑тренд: {top_cluster.name} (ID: {top_cluster.id})")

        # 2. Получаем статьи кластера с embeddings
        cluster_articles = self.data_fetcher.get_cluster_articles_with_embeddings(top_cluster.id)
        if not cluster_articles:
            logger.warning(f"В кластере {top_cluster.id} нет статей для анализа")
            return None

        # 3. Подготавливаем RAG‑контекст
        context = self.rag_processor.prepare_rag_context(cluster_articles, top_cluster.name)

        # 4. Формируем промпт
        prompt = PROMPT_TEMPLATE.format(
            cluster_name=top_cluster.name,
            context=context,
            min_words=RAG_CONFIG['article_length_range'][0],
            max_words=RAG_CONFIG['article_length_range'][1]
        )

        # 5. Генерируем статью через LLM
        generated_title, generated_content = self.llm_generator.generate_article(prompt)

        # 6. Сохраняем статью в отдельную таблицу
        new_generated_article = self._save_generated_article(
            generated_title,
            generated_content,
            top_cluster
        )

        logger.info(f"Успешно сгенерирована и сохранена статья: {generated_title}")
        return new_generated_article

    def _save_generated_article(
        self,
        title: str,
        content: str,
        cluster: TrendCluster
    ) -> GeneratedArticle:
        """Сохраняет сгенерированную статью в отдельную таблицу generated_articles."""
        # Вычисляем embedding для новой статьи
        embedding = self.embedding_model.encode([title], convert_to_numpy=True)[0].tolist()

        # Собираем метаданные генерации
        generation_metadata = json.dumps({
            'generation_timestamp': datetime.now().isoformat(),
            'cluster_id': cluster.id,
            'cluster_name': cluster.name,
            'model_used': "qwen2.5:0.5b",  # Обновляем имя модели
            'embedding_model': RAG_CONFIG['embedding_model'],
            'article_length': len(content.split()),
            'similarity_score': RAG_CONFIG['generated_article_similarity']
        })

        new_article = GeneratedArticle(
            title=title,
            content=content,
            cluster_id=cluster.id,
            cluster_name=cluster.name,
            similarity_score=RAG_CONFIG['generated_article_similarity'],
            generation_metadata=generation_metadata,
            embedding=embedding
        )
        self.db_session.add(new_article)
        self.db_session.commit()

        return new_article
