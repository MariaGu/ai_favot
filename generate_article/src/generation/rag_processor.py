import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from src.generation.utils import calculate_similarity, sort_articles_by_similarity, truncate_text

class RAGProcessor:
    def __init__(self, embedding_model: SentenceTransformer):
        self.embedding_model = embedding_model

    def prepare_rag_context(self, articles_data: List[dict], cluster_name: str) -> str:
        """Подготавливает контекст для RAG на основе статей кластера."""
        sorted_articles = sort_articles_by_similarity(articles_data)
        top_articles = sorted_articles[:5]

        context_parts = []
        for i, art in enumerate(top_articles, 1):
            similarity = art['similarity_score'] or 0
            title = art['article'].title
            content = truncate_text(art['article'].content, 400)

            context_parts.append(
                f"Статья {i} (сходство: {similarity:.2f}):\n"
                f"Заголовок: {title}\n"
                f"Содержание: {content}"
            )

        return "\n\n".join(context_parts)
