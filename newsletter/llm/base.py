import abc
from typing import Optional

from pydantic import BaseModel


class LLMOptions(BaseModel):
    max_tokens: Optional[int] = None
    temperature: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[float] = None
    repetition_penalty: Optional[float] = None
    stop: Optional[list[str]] = None


class BaseLLM(abc.ABC, BaseModel):
    @abc.abstractmethod
    def generate(
        self, prompt: str, model_name: str, options: Optional[LLMOptions]
    ) -> str:
        raise NotImplementedError
