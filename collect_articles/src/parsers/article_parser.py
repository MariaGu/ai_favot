import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
from src.config.logging import logger

class ArticleParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; FavotBot/1.0)'
        })

    def clean_text(self, text):
        """Очистка текста от лишних символов."""
        if not text:
            return ''
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()

    def parse_article(self, url, max_retries=3):
        """Парсинг статьи с повторными попытками."""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)

                if response.status_code != 200:
                    logger.warning(f"Попытка {attempt + 1}: HTTP {response.status_code} для {url}")
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')

                # Извлекаем заголовок
                title_elem = soup.find('h1') or soup.find('title')
                title = title_elem.get_text().strip() if title_elem else ''

                # Извлекаем основной текст
                content_elem = (soup.find('article') or
                               soup.find('div', class_='content') or
                               soup.find('div', itemprop='articleBody'))

                # Обрабатываем контент
                if content_elem:
                    # Удаляем ненужные элементы: рекламу, боковые панели и т. д.
                    for element in content_elem.find_all(['aside', 'nav', 'footer', 'script', 'style']):
                        element.decompose()
                    content = self.clean_text(content_elem.get_text())
                else:
                    content = ''

                # Дата публикации
                date_elem = soup.find('time') or soup.find(attrs={'pubdate': True})
                publish_date = None
                if date_elem and 'datetime' in date_elem.attrs:
                    publish_date = date_elem['datetime']

                logger.info(f"Успешно распарсено: {url}")
                return {
                    'url': url,
                    'title': self.clean_text(title),
                    'content': content,
                    'publish_date': publish_date,
                    'status': 'parsed'
                }

            except Exception as e:
                logger.warning(f"Попытка {attempt + 1} для {url} не удалась: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Не удалось распарсить {url} после {max_retries} попыток")
            return None

        return None
