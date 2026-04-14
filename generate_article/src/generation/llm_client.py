import requests
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class RemoteLLMClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model

    def generate_article(self, prompt: str) -> Tuple[str, str]:
        """
        Отправляет промпт на удалённый LLM и возвращает заголовок и текст статьи.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=240
            )
            response.raise_for_status()
            result = response.json()

            # Предполагаем, что ответ содержит поле 'response' с текстом
            full_text = result.get('response', '')

            # Разделяем заголовок и контент (предполагаем, что заголовок — первая строка)
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            if lines:
                title = lines[0]
                content = '\n'.join(lines[1:])
            else:
                title = "Сгенерированная статья"
                content = full_text

            return title, content

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обращении к LLM: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при генерации статьи: {e}")
            raise
