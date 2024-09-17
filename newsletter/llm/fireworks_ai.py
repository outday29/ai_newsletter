from typing import Literal, Optional, Self, TypeAlias, get_args

from fireworks.client import Fireworks
from pydantic import Field, PrivateAttr, SecretStr, model_validator
from typing_extensions import override

from newsletter.llm.base import BaseLLM, LLMOptions
from newsletter.settings import settings

Model: TypeAlias = Literal[
    "accounts/fireworks/models/llama-v3p1-405b-instruct",
    "accounts/fireworks/models/llama-v3p1-70b-instruct",
    "accounts/fireworks/models/llama-v3p1-8b-instruct",
    "accounts/fireworks/models/mixtral-8x22b-instruct",
    "accounts/fireworks/models/mixtral-8x7b-instruct",
]

MODEL_ALIAS: dict[Model, str] = {
    "accounts/fireworks/models/llama-v3p1-405b-instruct": "Llama-3.1-405B",
    "accounts/fireworks/models/llama-v3p1-70b-instruct": "Llama-3.1-70B",
    "accounts/fireworks/models/llama-v3p1-8b-instruct": "Llama-3.1-8B",
    "accounts/fireworks/models/mixtral-8x22b-instruct": "Mixtral-8x22B",
    "accounts/fireworks/models/mixtral-8x7b-instruct": "Mixtral-8x7B",
}


def get_model_list():
    return get_args(Model)

def model_format_func(opt: str):
    return MODEL_ALIAS[opt]
    

class FireworksAI(BaseLLM):
    api_key: SecretStr = Field(default=settings.fireworks_api_key)
    _client: Fireworks = PrivateAttr()

    @model_validator(mode="after")
    def init_client(self) -> Self:
        self._client = Fireworks(api_key=self.api_key.get_secret_value())

    @override
    def generate(
        self, prompt: str, model_name: Model, options: Optional[LLMOptions] = None
    ) -> str:
        if options is not None:
            kwargs = options.model_dump(
                exclude_none=True,
            )

        else:
            kwargs = {}

        response = self._client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            **kwargs,
        )

        return response.choices[0].message.content
