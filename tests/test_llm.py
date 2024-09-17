import pytest

from newsletter.llm import TogetherLLM
from newsletter.llm.base import LLMOptions
from newsletter.llm.fireworks_ai import FireworksAI
from newsletter.llm.openai import OpenAILLM


@pytest.fixture
def simple_prompt() -> str:
    return "Answer in one sentence. What is the meaning of life?"


def test_together_llm(simple_prompt):
    llm = TogetherLLM()
    answer = llm.generate(
        model_name="meta-llama/Meta-Llama-3-8B-Instruct-Turbo",
        prompt=simple_prompt,
        options=LLMOptions(max_tokens=10),
    )
    assert str(answer) != 0
    print(answer)


def test_fireworks_llm(simple_prompt):
    llm = FireworksAI()
    answer = llm.generate(
        model_name="accounts/fireworks/models/llama-v3p1-70b-instruct",
        prompt=simple_prompt,
        options=LLMOptions(max_tokens=10),
    )
    assert str(answer) != 0
    print(answer)


def test_openai(simple_prompt):
    llm = OpenAILLM()
    answer = llm.generate(
        model_name="gpt-4o-mini",
        prompt=simple_prompt,
        options=LLMOptions(max_tokens=10),
    )
    assert str(answer) != 0
    print(answer)
