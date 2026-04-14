from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, GenerationConfig
import torch
from typing import Tuple
from .config import RAG_CONFIG

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
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
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
            pad_token_id=self.tokenizer.eos_token_id
        )

        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=self.device if self.device != "cuda" else 0,
            **self.generation_config.to_dict()
        )

    def generate_article(self, prompt: str) -> Tuple[str, str]:
        """Генерирует заголовок и содержание статьи."""
        outputs = self.generator(prompt)
        full_response = outputs[0]['generated_text']

        lines = [line.strip() for line in full_response.split('\n') if line.strip()]
        generated_title = ""
        generated_content = ""

        for line in lines:
            if line.startswith("Заголовок:") or line.startswith("Title:"):
                generated_title = line.replace("Заголовок:", "").replace("Title:", "").strip()
            elif line.startswith("Содержание:") or line.startswith("Content:"):
                content_lines = []
                for next_line in lines[lines.index(line) + 1:]:
                    if not (
                        next_line.startswith("Заголовок:") or
                        next_line.startswith("Title:") or
                        next_line.startswith("Содержание:") or
                        next_line.startswith("Content:")
                    ):
                        content_lines.append(next_line)
                        generated_content = '\n'.join(content_lines)
                        break

        if not generated_title or not generated_content:
            generated_title = f"Обзор тренда: {prompt.split('о тренде ')[1].split('"')[0]}"
            generated_content = full_response[:1000]

        return generated_title, generated_content
