from typing import Literal, Optional, Self, TypeAlias, get_args

from pydantic import (
    ConfigDict,
    Field,
    PrivateAttr,
    SecretStr,
    model_validator,
)
from together import Together
from together.error import AuthenticationError, RateLimitError, ServiceUnavailableError
from typing_extensions import override

from newsletter.llm.base import BaseLLM, LLMOptions
from newsletter.llm.exception import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
)
from newsletter.settings import settings

Model: TypeAlias = Literal[
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
]

MODEL_ALIAS: dict[Model, str] = {
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": "Llama-3.1-8B",
    "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo": "Llama-3.1-405B",
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": "Llama-3.1-70B",
    "mistralai/Mixtral-8x22B-Instruct-v0.1": "Mixtral-8x22B",
    "mistralai/Mixtral-8x7B-Instruct-v0.1": "Mixtral-8x7B",
}


def get_model_list():
    return get_args(Model)


def model_format_func(opt: str):
    return MODEL_ALIAS[opt]


class TogetherLLM(BaseLLM):
    api_key: SecretStr = Field(default=settings.together_api_key)
    _client: Together = PrivateAttr()

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @model_validator(mode="after")
    def init_client(self) -> Self:
        self._client = Together(api_key=self.api_key.get_secret_value())
        return self

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
        try:
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

        except AuthenticationError as e:
            raise LLMAuthenticationError(e)

        except RateLimitError as e:
            raise LLMRateLimitError(e)

        except ServiceUnavailableError as e:
            raise LLMServiceUnavailableError(e)
