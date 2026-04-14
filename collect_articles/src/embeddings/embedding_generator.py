from sentence_transformers import SentenceTransformer
from src.config.logging import logger

class EmbeddingGenerator:
    def __init__(self, model_name='paraphrase-multilingual-mpnet-base-v2'):
        """Инициализация модели для генерации эмбеддингов."""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Модель эмбеддингов загружена: {model_name}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели эмбеддингов: {e}")
            raise

    def generate_embedding(self, text, title=''):
        """Генерирует эмбеддинг для текста статьи."""
        try:
            # Объединяем заголовок и контент для лучшего контекста
            full_text = f"{title} {text}"
            embedding = self.model.encode([full_text])[0]
            logger.debug(f"Сгенерирован эмбеддинг для текста длиной {len(text)} символов")
            return embedding.tolist()  # конвертируем в список для сохранения в БД
        except Exception as e:
            logger.error(f"Ошибка генерации эмбеддинга: {e}")
            return None

    def batch_generate(self, articles):
        """Генерация эмбеддингов для пачки статей."""
        try:
            texts = [f"{a['title']} {a['content']}" for a in articles]
            embeddings = self.model.encode(texts)
            embeddings_list = [emb.tolist() for emb in embeddings]
            logger.info(f"Сгенерировано {len(embeddings_list)} эмбеддингов")
            return embeddings_list
        except Exception as e:
            logger.error(f"Ошибка пакетной генерации эмбеддингов: {e}")
            return []
