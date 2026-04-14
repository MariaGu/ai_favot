from typing import List, Dict, Any
import numpy as np

def truncate_text(text: str, max_length: int = 400) -> str:
    """Обрезает текст до максимальной длины."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def calculate_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Вычисляет косинусное сходство между двумя векторами."""
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2) if norm_vec1 * norm_vec2 != 0 else 0.0

def sort_articles_by_similarity(articles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Сортирует статьи по similarity_score (по убыванию)."""
    return sorted(
        articles_data,
        key=lambda x: x.get('similarity_score', 0),
        reverse=True
    )
