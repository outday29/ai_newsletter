from pathlib import Path
from typing import Annotated, Literal, Optional, TypeAlias, get_args

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Doc

LLMPlatform: TypeAlias = Literal[
    "Together AI",
    "Fireworks AI",
    "OpenAI",
]

DataSource: TypeAlias = Literal["Reddit", "X"]


def get_supported_platform() -> list[str]:
    return get_args(LLMPlatform)


def get_supported_data_source() -> list[str]:
    return get_args(DataSource)


class RedditCredentials(BaseModel):
    personal_use_script: str
    client_secret: SecretStr
    user_agent: str
    username: str
    password: SecretStr


class StorageSettings(BaseModel):
    raw_data_folder: Annotated[Path, Doc("Folder where raw data is stored.")] = Path(
        "./data/raw/"
    )
    newsletter_folder: Annotated[Path, Doc("Folder where newsletter is stored.")] = (
        Path("./data/newsletter/")
    )
    preferences_folder: Annotated[Path, Doc("Folder where preferences are stored.")] = (
        Path("./data/preferences/")
    )

    @property
    def interest_file(self) -> Path:
        return self.preferences_folder / "interest.txt"

    def get_user_interest_prompt(self) -> Optional[str]:
        if self.interest_file.exists():
            return self.interest_file.read_text()

        else:
            return None

    def save_user_interest_prompt(self, new_text: str) -> None:
        self.interest_file.write_text(new_text)


class AppSettings(BaseSettings):
    together_api_key: Optional[SecretStr] = None
    openai_api_key: Optional[SecretStr] = None
    fireworks_api_key: Optional[SecretStr] = None
    reddit: Optional[RedditCredentials] = None
    storage: StorageSettings = StorageSettings()

    model_config = SettingsConfigDict(
        env_nested_delimiter="__", case_sensitive=False, env_file=".env"
    )

    def init_settings(self):
        self.storage.raw_data_folder.mkdir(parents=True, exist_ok=True)
        self.storage.newsletter_folder.mkdir(parents=True, exist_ok=True)
        self.storage.preferences_folder.mkdir(parents=True, exist_ok=True)

        # Initialize the preference files
        self.storage.interest_file.touch(exist_ok=True)
        for data_source in get_supported_data_source():
            (self.storage.preferences_folder / f"{data_source.lower()}.json").touch(
                exist_ok=True
            )

    def get_supported_platform(self) -> dict[LLMPlatform, bool]:
        results = {}
        results["Together AI"] = self.together_api_key is not None
        results["OpenAI"] = self.openai_api_key is not None
        results["Fireworks AI"] = self.fireworks_api_key is not None

        return results

    def get_supported_data_source(self) -> dict[DataSource, bool]:
        results = {}
        results["Reddit"] = self.reddit is not None
        results["X"] = False

        return results


settings = AppSettings()
settings.init_settings()
