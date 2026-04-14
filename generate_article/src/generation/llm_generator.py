from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import torch
from typing import Tuple
from .config import RAG_CONFIG
import logging

logger = logging.getLogger(__name__)

class LLMGenerator:
    def __init__(self, model_name: str = None, device: str = None):
        if model_name is None:
            model_name = RAG_CONFIG['llm_model']
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        print(f"Используемое устройство: {self.device}")

        # Загружаем токенизатор и модель
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Корректный тип данных в зависимости от устройства
        torch_dtype = torch.float16 if device == "cuda" else torch.float32
        if torch_dtype == torch.float32:  # float32 не существует, заменяем на float32 → исправляем на torch.float32 → нет, правильный вариант: torch.float32 отсутствует → используем torch.float (стандартный)
            torch_dtype = torch.float  # Используем стандартный float для CPU

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
            device_map="auto" if device == "cuda" else None
        )

        # Создаём конфигурацию генерации
        self.generation_config = GenerationConfig(
            max_new_tokens=RAG_CONFIG.get('max_new_tokens', 1200),
            temperature=RAG_CONFIG.get('temperature', 0.7),
            do_sample=True,
            top_p=RAG_CONFIG.get('top_p', 0.9),
            repetition_penalty=RAG_CONFIG.get('repetition_penalty', 1.1),
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )

    def generate_article(self, prompt: str) -> Tuple[str, str]:
        """Генерирует заголовок и содержание статьи."""
        try:
            # Токенизируем промпт
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Генерируем текст
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    generation_config=self.generation_config
                )

            # Декодируем результат
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Удаляем промпт из ответа (если он повторился)
            if prompt.strip() in full_response:
                full_response = full_response.replace(prompt.strip(), "").strip()

            return self._parse_response(full_response)

        except Exception as e:
            logger.error(f"Ошибка при генерации статьи: {e}")
            return self._fallback_response(prompt)

    def _parse_response(self, full_response: str) -> Tuple[str, str]:
        """Парсит ответ модели на заголовок и контент."""
        lines = [line.strip() for line in full_response.split('\n') if line.strip()]

        generated_title = ""
        generated_content = ""

        # Ищем заголовок по префиксам
        title_prefixes = ["Заголовок:", "Title:", "Заголовок статьи:", "Article Title:"]
        content_prefixes = ["Содержание:", "Content:", "Текст статьи:", "Article Content:"]

        for i, line in enumerate(lines):
            # Извлекаем заголовок
            if any(line.startswith(prefix) for prefix in title_prefixes):
                generated_title = line.split(":", 1)[1].strip()
            # Извлекаем контент (всё после префикса контента)
            elif any(line.startswith(prefix) for prefix in content_prefixes):
                content_lines = lines[i + 1:]
                generated_content = '\n'.join(content_lines)
                break
            # Если заголовок ещё не найден и это первая строка — используем как заголовок
            elif not generated_title and i == 0:
                generated_title = line

        # Если не нашли заголовок или контент — используем fallback
        if not generated_title:
            generated_title = "Обзор тренда"
        if not generated_content:
            generated_content = full_response[:1000]

        return generated_title, generated_content

    def _fallback_response(self, prompt: str) -> Tuple[str, str]:
        """Возвращает запасной ответ при ошибке генерации."""
        try:
            # Пытаемся извлечь тему из промпта как заголовок
            topic_start = prompt.find("о тренде ")
            if topic_start != -1:
                topic_end = prompt.find('"', topic_start)
                if topic_end != -1:
                    generated_title = f"Обзор тренда: {prompt[topic_start + 7:topic_end]}"
                else:
                    generated_title = "Обзор тренда"
            else:
                generated_title = "Обзор тренда"
        except:
            generated_title = "Обзор тренда"

        generated_content = (
            "К сожалению, не удалось сгенерировать статью. "
            "Пожалуйста, попробуйте позже или измените параметры запроса."
        )
        return generated_title, generated_content
