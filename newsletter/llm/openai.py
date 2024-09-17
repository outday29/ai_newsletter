from typing import Annotated, Literal, Optional, Self, TypeAlias, get_args

from openai import OpenAI
from pydantic import ConfigDict, Field, PrivateAttr, SecretStr, model_validator
from typing_extensions import override

from newsletter.llm.base import BaseLLM, LLMOptions
from newsletter.settings import settings

Model: TypeAlias = Literal[
    "gpt-4-turbo",
    "gpt-4o",
    "gpt-4o-mini",
]

MODEL_ALIAS: dict[Model, str] = {
    "gpt-4-turbo": "gpt-4-turbo",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
}


def get_model_list():
    return get_args(Model)


def model_format_func(opt: str) -> str:
    return MODEL_ALIAS[opt]


class OpenAILLM(BaseLLM):
    api_key: Annotated[SecretStr, Field(default=settings.openai_api_key)]
    _client: OpenAI = PrivateAttr()

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @model_validator(mode="after")
    def init_client(self) -> Self:
        self._client = OpenAI(
            api_key=self.api_key.get_secret_value(),
        )
        return self

    @override
    def generate(
        self, prompt: str, model_name: Model, options: Optional[LLMOptions] = None
    ):
        if options is not None:
            kwargs = options.model_dump(
                exclude_none=True,
            )

        else:
            kwargs = {}

        return (
            self._client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                **kwargs,
            )
            .choices[0]
            .message.content
        )
