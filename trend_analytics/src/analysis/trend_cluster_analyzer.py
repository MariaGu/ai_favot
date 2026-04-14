
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
from typing import List, Dict, Any, Optional
from src.database.models import Article, TrendCluster, TrendAnalysis, ClusterArticle
from src.config.logging import logger
from src.database.init_db import SessionLocal
import re

class TrendClusterAnalyzer:
    def __init__(self):
        self.db_session = SessionLocal()
        # Инициализируем модель для получения embeddings
        self.embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("Инициализирован TrendClusterAnalyzer с активной сессией PostgreSQL")

    def analyze_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        # Создаём запись об анализе
        analysis = TrendAnalysis(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(hours=hours),
            total_articles=0  # будет обновлено после получения статей
        )
        self.db_session.add(analysis)
        self.db_session.flush()  # получаем ID после сохранения в БД
        analysis_id = analysis.id

        # Получаем статьи за указанный период
        articles = self._get_recent_articles(hours)
        logger.info(f"Число статей для анализа: {len(articles)}")


        if not articles:
            # Обновляем статус анализа: нет статей для обработки
            analysis.end_date = datetime.now()
            analysis.total_articles = 0
            self.db_session.commit()
            logger.info("Нет статей для анализа за указанный период")
            return []

        # Обновляем количество статей в записи анализа
        analysis.total_articles = len(articles)


        # Получаем embeddings для статей
        article_embeddings = self._get_article_embeddings(articles)

        # Кластеризуем статьи
        cluster_labels = self._cluster_articles(article_embeddings)

        # Создаём и сохраняем кластеры
        clusters_info = self._create_and_save_clusters(
            cluster_labels,
            articles,
            article_embeddings,
            analysis_id=analysis_id,  # теперь переменная определена
            hours=hours
        )

        # Обновляем end_date после завершения анализа
        analysis.end_date = datetime.now()
        self.db_session.commit()

        return clusters_info



    def _get_recent_articles(self, hours: int) -> List[Article]:
        """Получает статьи за последние N часов."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        articles = self.db_session.query(Article).filter(
            Article.publish_date >= cutoff_time
        ).all()
        return articles    

    def _cluster_articles(self, embeddings: np.ndarray) -> np.ndarray:
        """Кластеризует статьи на основе embeddings с использованием DBSCAN."""
        # Нормализация embeddings для улучшения качества кластеризации
        scaler = StandardScaler()
        scaled_embeddings = scaler.fit_transform(embeddings)

        # Настройка DBSCAN
        clustering = DBSCAN(
            eps=0.5,           # радиус окрестности
            min_samples=2,     # минимальное число точек в кластере
            metric='cosine'     # метрика для текстовых embeddings
        )

        cluster_labels = clustering.fit_predict(scaled_embeddings)
        return cluster_labels    


    def _generate_cluster_name_llm(self, article_titles: List[str]) -> str:
        """Генерирует название кластера с помощью анализа embeddings и ключевых слов."""
        if not article_titles:
            return "Общий тренд"

        # Получаем embeddings для заголовков текущего кластера
        cluster_embeddings = self.embedding_model.encode(article_titles, convert_to_numpy=True)

        # Усредняем embeddings кластера
        avg_embedding = np.mean(cluster_embeddings, axis=0)

        # Находим наиболее репрезентативные слова
        keywords = self._extract_keywords_from_embeddings(cluster_embeddings, article_titles)

        if keywords:
            return ' '.join(keywords[:3])  # берём топ‑3 ключевых слова
        else:
            # Fallback — простой метод по частоте слов
            return self._extract_cluster_name_fallback(article_titles)
        
    def _extract_keywords_from_embeddings(self, cluster_embeddings: np.ndarray, titles: List[str]) -> List[str]:
        """Извлекает ключевые слова на основе анализа embeddings."""
        # Объединяем все заголовки для анализа
        all_text = ' '.join(titles).lower()

        # Извлекаем слова (длина ≥ 3, без стоп‑слов)
        stop_words = {'и', 'в', 'на', 'с', 'по', 'о', 'об', 'к', 'у', 'за', 'от', 'до',
                  'из', 'без', 'для', 'над', 'под', 'про', 'через', 'при', 'во', 'со',
                  'не', 'но', 'а', 'или', 'что', 'как', 'где', 'когда', 'почему'}
        words = re.findall(r'[а-яa-z]{3,}', all_text)
        filtered_words = [word for word in words if word not in stop_words]

        # Считаем частоту
        word_counts = Counter(filtered_words)
        top_words = [word for word, _ in word_counts.most_common(5)]

        return top_words 
        
    def _get_article_embeddings(self, articles: List[Article]) -> np.ndarray:
        """Получает embeddings для списка статей."""
        titles = [article.title for article in articles if article.title]
        embeddings = self.embedding_model.encode(titles, convert_to_numpy=True)
        return embeddings

    def _perform_clustering(self, embeddings: np.ndarray) -> np.ndarray:
        """Выполняет кластеризацию с использованием DBSCAN."""
        logger.info(f"Запуск кластеризации DBSCAN для {embeddings.shape[0]} векторов")

        clustering = DBSCAN(
            eps=0.5,
            min_samples=2,
            metric='cosine'
        )
        labels = clustering.fit_predict(embeddings)

        # Статистика кластеризации
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)

        logger.info(f"Кластеризация завершена: {n_clusters} кластеров, {n_noise} шумовых точек")

        return labels

    def _save_analysis_record(self, start_date: datetime, end_date: datetime) -> int:
        """Сохраняет запись об анализе."""
        analysis = TrendAnalysis(
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.utcnow(),
            total_articles=self.db_session.query(Article).filter(
                Article.publish_date >= start_date,
                Article.publish_date <= end_date
            ).count()
        )
        self.db_session.add(analysis)
        self.db_session.flush()
        logger.info(f"Создана запись анализа с ID: {analysis.id}")
        return analysis.id

    def _create_and_save_clusters(self, cluster_labels, articles, embeddings, analysis_id, hours):
        clusters_info = []

        for cluster_id in set(cluster_labels):
            if cluster_id == -1:  # шум
                continue

            # Статьи и embeddings текущего кластера
            cluster_mask = (cluster_labels == cluster_id)
            cluster_articles = [articles[i] for i, mask in enumerate(cluster_mask) if mask]
            cluster_titles = [article.title for article in cluster_articles if article.title]

            # Генерируем название через LLM‑подход
            cluster_name = self._generate_cluster_name_llm(cluster_titles)

            # Создаём и сохраняем кластер
            cluster = TrendCluster(
                name=cluster_name,
                analysis_id=analysis_id,
                rank=len(clusters_info) + 1,
                article_count=len(cluster_articles),
                hours_period=hours
            )
            self.db_session.add(cluster)
            self.db_session.flush()

            # Сохраняем связи статей с кластером
            for article in cluster_articles:
                cluster_article = ClusterArticle(
                    cluster_id=cluster.id,
                    article_id=article.id,
                    similarity_score=self._get_similarity_score(article, cluster_id, embeddings,  cluster_labels),
                    article_rank=0
                )
                self.db_session.add(cluster_article)

            clusters_info.append({
                'cluster_id': cluster.id,
                'name': cluster_name,
                'article_count': len(cluster_articles)
            })

        self.db_session.commit()
        return clusters_info


    def _get_similarity_score(self, article: Article, cluster_id: int, embeddings: np.ndarray,
    cluster_labels: np.ndarray) -> float:
        """
        Вычисляет косинусное сходство между статьей и центроидом кластера.
        """
        # Находим индекс статьи в общем списке
        all_titles = [a.title for a in self._get_recent_articles(24) if a.title]  # используем актуальный список статей
        try:
            article_idx = all_titles.index(article.title)
        except ValueError:
            return 0.0  # если статья не найдена, возвращаем 0

        # Получаем embedding статьи
        article_embedding = embeddings[article_idx].reshape(1, -1)

        #Находим все статьи в этом кластере
        cluster_mask = (cluster_labels == cluster_id)  # cluster_labels должен быть доступен
        cluster_embeddings = embeddings[cluster_mask]

        if len(cluster_embeddings) == 0:
            return 0.0

        # Вычисляем центроид кластера
        cluster_centroid = np.mean(cluster_embeddings, axis=0).reshape(1, -1)

        # Вычисляем косинусное сходство
        similarity = cosine_similarity(article_embedding, cluster_centroid)[0][0]
        return float(similarity)
    
    def _calculate_centroid(self, embeddings: List[np.ndarray]) -> np.ndarray:
        """Рассчитывает центроид кластера."""
        return np.mean(embeddings, axis=0)

    def _sort_articles_by_centroid_distance(self, articles: List[Article],
                                   centroid: np.ndarray) -> List[Article]:
        """Сортирует статьи по расстоянию до центроида."""
        def distance_to_centroid(article: Article) -> float:
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity([article.embedding], [centroid])[0][0]
            return 1 - similarity  # чем больше сходство, тем меньше расстояние


        sorted_articles = sorted(articles, key=distance_to_centroid)
        return sorted_articles

    def _extract_cluster_name(
        self,
        articles: List[Article],
        global_word_freq: Optional[Dict[str, int]] = None
    ) -> str:
        """Извлекает название кластера на основе ключевых слов."""
        # Стоп‑слова для русского языка
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'о', 'об', 'к', 'у', 'за', 'от', 'до',
            'из', 'без', 'для', 'над', 'под', 'про', 'через', 'при', 'во', 'со',
            'не', 'но', 'а', 'или', 'что', 'как', 'где', 'когда', 'почему'
        }

        all_words = []
        for article in articles:
            if article.title:
                # Извлекаем слова: только буквы, длина ≥ 3, в нижнем регистре
                words = re.findall(r'[а-яa-z]{3,}', article.title.lower())
                # Фильтруем стоп‑слова
                filtered_words = [word for word in words if word not in stop_words]
                all_words.extend(filtered_words)

        if not all_words:
            return "Общий тренд"

        # Если global_word_freq не передан, используем простой подсчёт частоты
        if global_word_freq is None:
            word_counts = Counter(all_words)
            top_words = word_counts.most_common(2)
        else:
            # Учитываем глобальную частоту: частота в кластере / частота в целом по базе
            cluster_word_counts = Counter(all_words)
            scored_words = []
            for word, count in cluster_word_counts.items():
                global_freq = global_word_freq.get(word, 1)  # если нет — считаем редким
                score = count / global_freq
                scored_words.append((word, score))
            scored_words.sort(key=lambda x: x[1], reverse=True)
            top_words = scored_words[:2]

        name_parts = [word for word, _ in top_words]
        return ' '.join(name_parts) if name_parts else "Общий тренд"


    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Рассчитывает косинусное сходство между двумя векторами."""
        from sklearn.metrics.pairwise import cosine_similarity
        vec1 = np.asarray(vec1).astype(np.float64).flatten()
        vec2 = np.asarray(vec2).astype(np.float64).flatten()


        if vec1.size != vec2.size:
            raise ValueError(f"Несоответствие размеров: {vec1.size} vs {vec2.size}")

        if vec1.size == 0:
            return 0.0

        return cosine_similarity([vec1], [vec2])[0][0]