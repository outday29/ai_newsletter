from abc import ABC
from typing import Any, Optional

from PIL import Image
from pydantic import BaseModel, ConfigDict


class AbstractPrompt(ABC, BaseModel):
    prompt_type: str

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class TextPrompt(AbstractPrompt):
    prompt_type: str = "text"
    text_content: str

    def __str__(self):
        return self.text_content


class ImagePrompt(AbstractPrompt):
    prompt_type: str = "image"
    img_url: Optional[str] = None
    img_content: Optional[Image.Image] = None

    def load_content(self):
        if self.img_content is not None:
            # Already loaded
            pass

        else:
            if self.img_url is None:
                raise ValueError("Cannot load image when img urlis None")

            else:
                self.img_content = Image.open(self.img_url)

    def __str__(self):
        # May need to escape, sometimes I feel that MongoDB is a better choice.
        return f"<<image {self.img_url}>>" if self.img_url else "<<image object>>"


class VideoPrompt(AbstractPrompt):
    prompt_type: str = "video"
    video_url: Optional[str] = None
    video_content: Any = None


class AudioPrompt(AbstractPrompt):
    prompt_type: str = "audio"
    audio_url: Optional[str] = None
    audio_content: Any = None


class PromptInput(BaseModel):
    prompts: list[
        AbstractPrompt
    ]  # It is up to the LLM implementation on whether the order matters.

    def __str__(self) -> str:
        text = ""
        for prompt in self.prompts:
            match prompt.prompt_type:
                case "text":
                    text += str(prompt)
                case "image":
                    text += str(prompt)
                case other:
                    raise NotImplementedError(f"Unsupported prompt type: {other}")
            text += "\n"
        text = text.rstrip()
        return text
