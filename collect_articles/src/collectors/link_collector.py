import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from src.config.logging import logger

class LinkCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; FavotBot/1.0)'
        })

    def collect_from_rss(self, rss_url, max_articles=50):
        """Сбор ссылок из RSS‑ленты."""
        try:
            feed = feedparser.parse(rss_url)
            links = []
            for entry in feed.entries[:max_articles]:
                links.append({
                    'url': entry.link,
                    'title': entry.title,
                    'published': entry.published if 'published' in entry else None
                })
            logger.info(f"Собрано {len(links)} ссылок из RSS: {rss_url}")
            return links
        except Exception as e:
            logger.error(f"Ошибка сбора из RSS {rss_url}: {e}")
            return []

    def collect_from_website(self, base_url, selector='a[href*="/article/"]', max_links=100):
        """Сбор ссылок с веб‑страницы."""
        try:
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            links = []

            for link in soup.select(selector)[:max_links]:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    links.append({'url': full_url, 'title': link.get_text().strip()})

            logger.info(f"Собрано {len(links)} ссылок с сайта: {base_url}")
            return links
        except Exception as e:
            logger.error(f"Ошибка сбора с сайта {base_url}: {e}")
            return []
        
    def collect_and_queue_links(self, rss_urls=None, website_urls=None):
        """Собирает ссылки и сразу добавляет в очередь БД."""
        all_links = []

        # Сбор из RSS
        if rss_urls:
            for rss_url in rss_urls:
                links = self.collect_from_rss(rss_url)
                all_links.extend(links)

        # Сбор с веб‑сайтов
        if website_urls:
            for website_url in website_urls:
                links = self.collect_from_website(website_url)
                all_links.extend(links)

        return all_links
